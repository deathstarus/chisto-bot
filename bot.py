"""
Точка входа: запускает Telegram-бота клининговой компании «Чисто».

Запуск:  python bot.py
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

import config
from database import init_db
from handlers import get_routers
from texts import TextsError, texts


async def set_commands(bot: Bot) -> None:
    """Команды в меню Telegram (кнопка «Меню» слева от поля ввода)."""
    user_commands = [BotCommand(command="start", description="Главное меню")]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Администратор дополнительно видит свои команды
    admin_commands = user_commands + [
        BotCommand(command="leads", description="Последние 10 заявок"),
        BotCommand(command="reload", description="Перечитать texts.yaml"),
    ]
    try:
        await bot.set_my_commands(admin_commands,
                                  scope=BotCommandScopeChat(chat_id=config.ADMIN_ID))
    except Exception as e:
        # Бывает, если администратор ещё ни разу не писал боту
        logging.warning("Не удалось установить команды администратора: %s", e)


async def main() -> None:
    # Сообщения о работе бота печатаются в консоль
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 1. Загружаем тексты. Если в texts.yaml ошибка — бот не запустится
    #    и напишет, что именно не так.
    try:
        texts.load()
    except TextsError as e:
        logging.critical("Ошибка в texts.yaml: %s", e)
        sys.exit(1)

    # 2. Готовим базу данных заявок
    await init_db()

    # 3. Создаём бота. ParseMode.HTML — разрешаем <b>жирный</b> и т.п. в текстах
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # MemoryStorage хранит шаг заполнения заявки в памяти.
    # При перезапуске бота незаконченные заявки сбрасываются — это нормально.
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(*get_routers())

    try:
        # Проверяем токен: если он неверный, Telegram ответит ошибкой
        try:
            me = await bot.get_me()
        except TelegramUnauthorizedError:
            logging.critical("Неверный BOT_TOKEN. Скопируйте токен из @BotFather в файл .env")
            sys.exit(1)
        await set_commands(bot)
        logging.info("Бот @%s запущен. Остановить: Ctrl+C", me.username)

        # Запускаем приём сообщений. Сообщения, пришедшие, пока бот был
        # выключен, тоже будут обработаны — так заявки не потеряются.
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
