import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import RankedArticle

DB_PATH = Path.home() / ".newspull" / "newspull.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            bullet_summary TEXT NOT NULL,
            credibility_score REAL NOT NULL,
            rank_score REAL NOT NULL,
            cross_ref_count INTEGER NOT NULL DEFAULT 0,
            fetched_at TEXT NOT NULL,
            read INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS feed_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            shown_at TEXT NOT NULL,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        );
    """)
    conn.commit()
    conn.close()


def save_article(article: RankedArticle) -> int | None:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO articles
               (source, url, title, bullet_summary, credibility_score,
                rank_score, cross_ref_count, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                article.source,
                article.url,
                article.title,
                json.dumps(article.bullets),
                article.credibility_score,
                article.rank_score,
                article.cross_ref_count,
                article.fetched_at.isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid if cursor.rowcount > 0 else None
    finally:
        conn.close()


def get_unread_articles(limit: int = 20) -> list[dict]:
    """Highest-ranked unread articles."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM articles WHERE read = 0 ORDER BY rank_score DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_backlog_articles(limit: int = 20) -> list[dict]:
    """Oldest unread articles (backlog dig)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM articles WHERE read = 0 ORDER BY fetched_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def mark_articles_read(article_ids: list[int]) -> None:
    if not article_ids:
        return
    conn = get_connection()
    try:
        placeholders = ",".join("?" * len(article_ids))
        conn.execute(
            f"UPDATE articles SET read = 1 WHERE id IN ({placeholders})",
            article_ids,
        )
        conn.commit()
    finally:
        conn.close()


def count_cross_refs(url: str) -> int:
    """Count existing articles with the same URL (cross-reference detection)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE url = ?", (url,)
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["bullet_summary"] = json.loads(d["bullet_summary"])
    return d
