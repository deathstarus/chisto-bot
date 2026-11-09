"""
Команды администратора (работают только для ADMIN_ID из .env):
    /reload — перечитать texts.yaml без перезапуска бота
    /leads  — показать последние 10 заявок
"""

from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID
from database import get_last_leads
from texts import TextsError, texts

router = Router(name="admin")

# Все обработчики этого роутера срабатывают только для администратора.
# Для остальных пользователей эти команды как будто не существуют.
router.message.filter(F.from_user.id == ADMIN_ID)


@router.message(Command("reload"))
async def cmd_reload(message: Message) -> None:
    try:
        texts.load()
    except TextsError as e:
        # Файл с ошибкой — бот продолжает работать со старыми текстами
        await message.answer(
            "❌ <b>Тексты не обновлены</b> — в texts.yaml ошибка:\n\n"
            f"<pre>{escape(str(e))}</pre>\n\n"
            "Бот продолжает работать со старыми текстами. "
            "Исправьте файл и снова отправьте /reload."
        )
        return
    await message.answer(
        "✅ Тексты обновлены из texts.yaml.\n"
        f"Услуг: {len(texts.services)}, вопросов: {len(texts.faq)}."
    )


@router.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    leads = await get_last_leads(10)
    if not leads:
        await message.answer("Заявок пока нет.")
        return

    parts = [f"<b>📋 Последние заявки ({len(leads)})</b>"]
    for lead in leads:
        who = f" (@{lead['username']})" if lead["username"] else ""
        comment = ""
        if lead["comment"]:
            short = lead["comment"] if len(lead["comment"]) <= 300 else lead["comment"][:300] + "…"
            comment = f"\n💬 {escape(short)}"
        parts.append(
            f"<b>№{lead['id']}</b> · {lead['created_at']}\n"
            f"👤 {escape(lead['name'])}{who}\n"
            f"📱 {lead['phone']}\n"
            f"🧽 {escape(lead['service'])}"
            f"{comment}"
        )
    # В одном сообщении Telegram не больше 4096 символов,
    # поэтому длинный список отправляем несколькими сообщениями
    chunk = ""
    for part in parts:
        if chunk and len(chunk) + len(part) > 3800:
            await message.answer(chunk)
            chunk = ""
        chunk = f"{chunk}\n\n{part}" if chunk else part
    await message.answer(chunk)
