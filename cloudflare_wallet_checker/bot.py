from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import time
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from cloudflare_wallet_checker.core import CheckResult, CloudflareWalletClient, unique_handles
from cloudflare_wallet_checker.emoji import PREMIUM_EMOJI_IDS
from cloudflare_wallet_checker.storage import LanguageStore
from cloudflare_wallet_checker.translations import SUPPORTED_LANGUAGES, text

router = Router(name="wallet-checker")
last_requests: dict[int, float] = {}


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="English",
                    callback_data="lang:en",
                    icon_custom_emoji_id=PREMIUM_EMOJI_IDS["settings"],
                ),
                InlineKeyboardButton(
                    text="Русский",
                    callback_data="lang:ru",
                    icon_custom_emoji_id=PREMIUM_EMOJI_IDS["settings"],
                ),
            ]
        ]
    )


def fallback_language(message: Message) -> str:
    code = message.from_user.language_code if message.from_user else None
    return "ru" if code and code.lower().startswith("ru") else "en"


def user_language(message: Message, store: LanguageStore) -> str:
    if message.from_user is None:
        return "en"
    return store.get(message.from_user.id, fallback_language(message))


def extract_handles(value: str) -> list[str]:
    return unique_handles(re.split(r"[\s,;]+", value.strip()))


def render_results(language: str, results: list[CheckResult]) -> str:
    lines = [text(language, "result_title"), ""]
    for result in results:
        value = html.escape(result.normalized or result.username)
        label = text(language, result.status.value)
        lines.append(f"{label} — <code>@{value}</code>")
    return "\n".join(lines)


async def send_welcome(message: Message, store: LanguageStore) -> None:
    language = user_language(message, store)
    await message.answer(text(language, "welcome"), reply_markup=language_keyboard())


@router.message(CommandStart())
async def start_handler(message: Message, language_store: LanguageStore) -> None:
    await send_welcome(message, language_store)


@router.message(Command("help"))
async def help_handler(message: Message, language_store: LanguageStore, max_handles: int) -> None:
    language = user_language(message, language_store)
    await message.answer(text(language, "help", limit=max_handles))


@router.message(Command("about"))
async def about_handler(message: Message, language_store: LanguageStore) -> None:
    language = user_language(message, language_store)
    await message.answer(text(language, "about"))


@router.message(Command("language"))
async def language_handler(message: Message, language_store: LanguageStore) -> None:
    language = user_language(message, language_store)
    await message.answer(text(language, "language"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery, language_store: LanguageStore) -> None:
    language = (callback.data or "").partition(":")[2]
    if language not in SUPPORTED_LANGUAGES or callback.from_user is None:
        await callback.answer()
        return
    language_store.set(callback.from_user.id, language)
    await callback.answer(text(language, "language_saved"))
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text(language, "welcome"), reply_markup=language_keyboard()
        )


async def process_check(
    message: Message,
    raw_handles: str,
    language_store: LanguageStore,
    wallet_client: CloudflareWalletClient,
    max_handles: int,
    cooldown: float,
) -> None:
    language = user_language(message, language_store)
    handles = extract_handles(raw_handles)
    if not handles:
        await message.answer(text(language, "empty"))
        return
    if len(handles) > max_handles:
        await message.answer(text(language, "too_many", limit=max_handles))
        return
    user_id = message.from_user.id if message.from_user else message.chat.id
    now = time.monotonic()
    if now - last_requests.get(user_id, 0.0) < cooldown:
        await message.answer(text(language, "rate_limit"))
        return
    last_requests[user_id] = now
    status_message = await message.answer(text(language, "checking", count=len(handles)))
    results = await wallet_client.check_many(handles, workers=min(5, len(handles)))
    await status_message.edit_text(render_results(language, results))


@router.message(Command("check"))
async def check_handler(
    message: Message,
    language_store: LanguageStore,
    wallet_client: CloudflareWalletClient,
    max_handles: int,
    cooldown: float,
) -> None:
    raw_handles = (message.text or "").partition(" ")[2]
    await process_check(
        message,
        raw_handles,
        language_store,
        wallet_client,
        max_handles,
        cooldown,
    )


@router.message(F.text)
async def text_handler(
    message: Message,
    language_store: LanguageStore,
    wallet_client: CloudflareWalletClient,
    max_handles: int,
    cooldown: float,
) -> None:
    await process_check(
        message,
        message.text or "",
        language_store,
        wallet_client,
        max_handles,
        cooldown,
    )


async def set_commands(bot: Bot) -> None:
    commands_en = [
        BotCommand(command="start", description="Open the checker"),
        BotCommand(command="check", description="Check usernames"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="about", description="About the project"),
    ]
    commands_ru = [
        BotCommand(command="start", description="Открыть чекер"),
        BotCommand(command="check", description="Проверить юзернеймы"),
        BotCommand(command="language", description="Изменить язык"),
        BotCommand(command="help", description="Показать помощь"),
        BotCommand(command="about", description="О проекте"),
    ]
    await bot.set_my_commands(commands_en)
    await bot.set_my_commands(commands_ru, language_code="ru")


async def run_bot() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    database = Path(os.getenv("BOT_DATABASE", "data/bot.sqlite3"))
    max_handles = int(os.getenv("BOT_MAX_HANDLES", "20"))
    cooldown = float(os.getenv("BOT_COOLDOWN", "1.0"))
    language_store = LanguageStore(database)
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    try:
        async with CloudflareWalletClient(max_connections=10) as wallet_client:
            await set_commands(bot)
            await dispatcher.start_polling(
                bot,
                language_store=language_store,
                wallet_client=wallet_client,
                max_handles=max_handles,
                cooldown=cooldown,
            )
    finally:
        language_store.close()
        await bot.session.close()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
