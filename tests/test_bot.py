from cloudflare_wallet_checker.bot import language_keyboard, render_results
from cloudflare_wallet_checker.core import CheckResult, Status
from cloudflare_wallet_checker.emoji import PREMIUM_EMOJI_IDS


def test_language_keyboard_uses_custom_emoji_icons() -> None:
    keyboard = language_keyboard()
    buttons = keyboard.inline_keyboard[0]
    assert [button.text for button in buttons] == ["English", "Русский"]
    assert all(button.icon_custom_emoji_id == PREMIUM_EMOJI_IDS["settings"] for button in buttons)


def test_render_results_escapes_handle_and_uses_premium_emoji() -> None:
    rendered = render_results("en", [CheckResult("<bad>", Status.INVALID)])
    assert "<tg-emoji" in rendered
    assert "&lt;bad&gt;" in rendered
    assert "<code>@<bad></code>" not in rendered


def test_render_results_is_bilingual() -> None:
    result = [CheckResult("free", Status.AVAILABLE, "free")]
    assert "Available" in render_results("en", result)
    assert "Свободен" in render_results("ru", result)
