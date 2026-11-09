"""
Работа с базой данных SQLite, где хранятся заявки.

SQLite — это обычный файл (leads.db) рядом с ботом, отдельный сервер
базы данных не нужен. Файл создаётся автоматически при первом запуске.
"""

from datetime import datetime
from pathlib import Path

import aiosqlite

from config import DB_PATH

# SQL-запрос, создающий таблицу заявок (если её ещё нет)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,          -- Telegram ID клиента
    username    TEXT,                      -- @username клиента (если есть)
    name        TEXT    NOT NULL,          -- имя из формы
    phone       TEXT    NOT NULL,          -- телефон в формате +7 (XXX) XXX-XX-XX
    service     TEXT    NOT NULL,          -- выбранная услуга
    comment     TEXT,                      -- комментарий (может быть пустым)
    created_at  TEXT    NOT NULL           -- дата и время заявки
)
"""


async def init_db(path: Path = DB_PATH) -> None:
    """Создаёт файл базы и таблицу заявок, если их ещё нет."""
    async with aiosqlite.connect(path) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


async def add_lead(
    user_id: int,
    username: str | None,
    name: str,
    phone: str,
    service: str,
    comment: str | None,
    path: Path = DB_PATH,
) -> tuple[int, str]:
    """
    Сохраняет заявку. Возвращает её номер и время создания.
    """
    created_at = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute(
            "INSERT INTO leads (user_id, username, name, phone, service, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, name, phone, service, comment, created_at),
        )
        await db.commit()
        return cursor.lastrowid, created_at


async def get_last_leads(limit: int = 10, path: Path = DB_PATH) -> list[dict]:
    """Возвращает последние заявки (самые новые — первыми)."""
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row  # чтобы обращаться к полям по имени
        cursor = await db.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
