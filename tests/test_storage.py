from pathlib import Path

from cloudflare_wallet_checker.storage import LanguageStore


def test_language_store(tmp_path: Path) -> None:
    store = LanguageStore(tmp_path / "bot.sqlite3")
    try:
        assert store.get(1, "en") == "en"
        store.set(1, "ru")
        assert store.get(1, "en") == "ru"
    finally:
        store.close()
