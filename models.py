import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash BLOB NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lesson_completions (
    user_id      INTEGER NOT NULL,
    lesson_id    TEXT    NOT NULL,
    completed_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, lesson_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

class UserStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def create_user(self, username: str, password_hash: bytes) -> bool:
        try:
            with self._conn() as c:
                c.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username: str):
        with self._conn() as c:
            row = c.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return row

    def mark_lesson_complete(self, user_id: int, lesson_id: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO lesson_completions (user_id, lesson_id) VALUES (?, ?)",
                (user_id, lesson_id),
            )

    def is_lesson_complete(self, user_id: int, lesson_id: str) -> bool:
        with self._conn() as c:
            row = c.execute(
                "SELECT 1 FROM lesson_completions WHERE user_id = ? AND lesson_id = ?",
                (user_id, lesson_id),
            ).fetchone()
        return row is not None

    def completed_lessons(self, user_id: int):
        with self._conn() as c:
            rows = c.execute(
                "SELECT lesson_id, completed_at FROM lesson_completions WHERE user_id = ? ORDER BY completed_at",
                (user_id,),
            ).fetchall()
        return rows
