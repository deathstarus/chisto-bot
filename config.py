"""
Настройки бота. Берутся из файла .env (см. .env.example).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

# Читаем переменные из файла .env, который лежит рядом с ботом
load_dotenv(BASE_DIR / ".env")

# Токен бота от @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Telegram ID администратора — ему приходят заявки
_admin_id = os.getenv("ADMIN_ID", "").strip()

# Файл базы данных SQLite с заявками
DB_PATH = BASE_DIR / os.getenv("DB_FILE", "leads.db")


def _fail(message: str) -> None:
    """Печатает понятную ошибку и завершает программу."""
    print(f"\n❌ ОШИБКА НАСТРОЙКИ: {message}\n"
          f"Откройте файл .env и проверьте его (образец — .env.example).\n",
          file=sys.stderr)
    sys.exit(1)


if not BOT_TOKEN or BOT_TOKEN.startswith("123456:"):
    _fail("не указан BOT_TOKEN — токен бота от @BotFather")

if not _admin_id.isdigit():
    _fail("ADMIN_ID должен быть числом — ваш ID из @userinfobot")

ADMIN_ID = int(_admin_id)
