import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from .models import Account, ArticleCandidate


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    connector TEXT NOT NULL,
    source_id TEXT,
    feed_url TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_checked_at TEXT,
    last_error TEXT,
    UNIQUE(connector, source_id),
    UNIQUE(connector, feed_url)
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT NOT NULL,
    discovered_at TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    cover_url TEXT NOT NULL DEFAULT '',
    UNIQUE(account_id, external_id),
    UNIQUE(account_id, url)
);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def add_account(self, name: str, connector: str, source_id: str | None, feed_url: str | None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO accounts(name, connector, source_id, feed_url, created_at) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), connector, source_id or None, feed_url or None, now),
            )
            return int(cursor.lastrowid)

    def list_accounts(self, enabled_only: bool = False) -> list[Account]:
        query = "SELECT * FROM accounts"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name COLLATE NOCASE"
        with self.connect() as connection:
            return [self._account(row) for row in connection.execute(query).fetchall()]

    def get_account(self, account_id: int) -> Account | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
            return self._account(row) if row else None

    def delete_account(self, account_id: int) -> bool:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            return cursor.rowcount == 1

    def find_account_by_name(self, name: str) -> Account | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM accounts WHERE name = ?", (name,)).fetchone()
            return self._account(row) if row else None

    def set_account_state(self, account_id: int, error: str | None) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE accounts SET last_checked_at = ?, last_error = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), error, account_id),
            )

    def insert_article(self, account_id: int, article: ArticleCandidate) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO articles(
                    account_id, external_id, title, url, published_at, discovered_at,
                    summary, content, cover_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    article.external_id,
                    article.title,
                    article.url,
                    article.published_at.astimezone(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                    article.summary,
                    article.content,
                    article.cover_url,
                ),
            )
            return cursor.rowcount == 1

    def recent_articles(self, hours: int = 24, account_id: int | None = None, limit: int = 500) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        params: list[object] = [since]
        where = "a.published_at >= ?"
        if account_id is not None:
            where += " AND a.account_id = ?"
            params.append(account_id)
        params.append(limit)
        query = f"""
            SELECT a.*, c.name AS account_name
            FROM articles a JOIN accounts c ON c.id = a.account_id
            WHERE {where}
            ORDER BY a.published_at DESC LIMIT ?
        """
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    @staticmethod
    def _account(row: sqlite3.Row) -> Account:
        return Account(
            id=row["id"], name=row["name"], connector=row["connector"],
            source_id=row["source_id"], feed_url=row["feed_url"], enabled=bool(row["enabled"]),
            last_checked_at=row["last_checked_at"], last_error=row["last_error"],
        )
