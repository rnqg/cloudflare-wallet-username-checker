from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


class LanguageStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._connection:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS user_settings (user_id INTEGER PRIMARY KEY, language TEXT NOT NULL)"
            )

    def get(self, user_id: int, fallback: str = "en") -> str:
        with self._lock:
            row = self._connection.execute(
                "SELECT language FROM user_settings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return row[0] if row else fallback

    def set(self, user_id: int, language: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO user_settings(user_id, language) VALUES(?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET language = excluded.language",
                (user_id, language),
            )

    def close(self) -> None:
        with self._lock:
            self._connection.close()
