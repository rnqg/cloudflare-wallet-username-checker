from __future__ import annotations

from cloudflare_wallet_checker.emoji import PREMIUM_EMOJI

SUPPORTED_LANGUAGES = {"en", "ru"}

TEXTS = {
    "en": {
        "welcome": (
            f"<b>{PREMIUM_EMOJI['bot']} Cloudflare Wallet Username Checker</b>\n\n"
            "Check whether a <code>cloudflare.pay</code> wallet handle is available.\n\n"
            "Send one or more names, or use:\n"
            "<code>/check name another-name</code>\n\n"
            "The bot distinguishes taken, Cloudflare-reserved, invalid and temporarily failed checks."
        ),
        "help": (
            f"<b>{PREMIUM_EMOJI['info']} Help</b>\n\n"
            "<code>/check name1 name2</code> — check up to {limit} names\n"
            "<code>/language</code> — change language\n"
            "<code>/about</code> — project information\n\n"
            "You can also send names as plain text, separated by spaces, commas or new lines."
        ),
        "about": (
            f"<b>{PREMIUM_EMOJI['wallet']} About</b>\n\n"
            "Open-source checker for Cloudflare Wallet handles. It uses the same public availability API as "
            "<code>cloudflare.pay</code> and never treats a reservation-page redirect as proof of availability."
        ),
        "language": f"<b>{PREMIUM_EMOJI['settings']} Choose your language</b>",
        "language_saved": "Language changed to English.",
        "empty": f"{PREMIUM_EMOJI['info']} Send at least one username.",
        "too_many": f"{PREMIUM_EMOJI['cross']} Maximum: {{limit}} usernames per request.",
        "checking": f"{PREMIUM_EMOJI['search']} Checking {{count}} username(s)…",
        "result_title": f"<b>{PREMIUM_EMOJI['wallet']} Results</b>",
        "available": f"{PREMIUM_EMOJI['check']} Available",
        "taken": f"{PREMIUM_EMOJI['cross']} Taken",
        "reserved": f"{PREMIUM_EMOJI['locked']} Reserved by Cloudflare",
        "invalid": f"{PREMIUM_EMOJI['info']} Invalid",
        "error": f"{PREMIUM_EMOJI['cross']} Temporary error",
        "rate_limit": f"{PREMIUM_EMOJI['info']} Please wait a moment before the next check.",
    },
    "ru": {
        "welcome": (
            f"<b>{PREMIUM_EMOJI['bot']} Проверка юзернеймов Cloudflare Wallet</b>\n\n"
            "Проверяю доступность имён кошелька <code>cloudflare.pay</code>.\n\n"
            "Отправьте одно или несколько имён либо используйте:\n"
            "<code>/check name another-name</code>\n\n"
            "Бот различает занятые, зарезервированные Cloudflare, некорректные имена и временные ошибки."
        ),
        "help": (
            f"<b>{PREMIUM_EMOJI['info']} Помощь</b>\n\n"
            "<code>/check name1 name2</code> — проверить до {limit} имён\n"
            "<code>/language</code> — изменить язык\n"
            "<code>/about</code> — информация о проекте\n\n"
            "Можно просто отправить имена текстом через пробел, запятую или с новой строки."
        ),
        "about": (
            f"<b>{PREMIUM_EMOJI['wallet']} О проекте</b>\n\n"
            "Open-source чекер имён Cloudflare Wallet. Использует тот же публичный API доступности, что и "
            "<code>cloudflare.pay</code>, и не считает редирект на форму резервирования доказательством доступности."
        ),
        "language": f"<b>{PREMIUM_EMOJI['settings']} Выберите язык</b>",
        "language_saved": "Язык изменён на русский.",
        "empty": f"{PREMIUM_EMOJI['info']} Отправьте хотя бы один юзернейм.",
        "too_many": f"{PREMIUM_EMOJI['cross']} Максимум {{limit}} юзернеймов за один запрос.",
        "checking": f"{PREMIUM_EMOJI['search']} Проверяю {{count}} имён…",
        "result_title": f"<b>{PREMIUM_EMOJI['wallet']} Результаты</b>",
        "available": f"{PREMIUM_EMOJI['check']} Свободен",
        "taken": f"{PREMIUM_EMOJI['cross']} Занят",
        "reserved": f"{PREMIUM_EMOJI['locked']} Зарезервирован Cloudflare",
        "invalid": f"{PREMIUM_EMOJI['info']} Некорректный",
        "error": f"{PREMIUM_EMOJI['cross']} Временная ошибка",
        "rate_limit": f"{PREMIUM_EMOJI['info']} Подождите немного перед следующей проверкой.",
    },
}


def text(language: str, key: str, **values: object) -> str:
    selected = language if language in SUPPORTED_LANGUAGES else "en"
    return TEXTS[selected][key].format(**values)
