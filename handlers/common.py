"""
Общие разделы: /start, главное меню, услуги, частые вопросы, контакты.
"""

from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

from keyboards import back_kb, faq_list_kb, main_menu_kb, services_info_kb
from texts import texts

router = Router(name="common")


async def show(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    """
    Показывает новый экран, заменяя текст сообщения с кнопками.
    Так чат не засоряется: меню «перелистывается» в одном сообщении.
    """
    await callback.answer()  # убираем «часики» на кнопке
    try:
        await callback.message.edit_text(text, reply_markup=markup,
                                         disable_web_page_preview=True)
    except TelegramBadRequest:
        # Сообщение слишком старое или не изменилось — просто пришлём новое
        await callback.message.answer(text, reply_markup=markup,
                                      disable_web_page_preview=True)


# ---------- /start ----------
# Команда /start вынесена в отдельный роутер start_router, который
# подключается ПЕРВЫМ: так /start работает даже посреди заполнения заявки.
start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    # Если человек был посреди заполнения заявки — сбрасываем её
    await state.clear()
    name = escape(message.from_user.first_name or "друг")
    await message.answer(texts["welcome"].format(name=name).strip(),
                         reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(callback, texts["main_menu_text"], main_menu_kb())


# ---------- Услуги и цены ----------

def build_services_text() -> str:
    """Собирает красивый список услуг из texts.yaml."""
    lines = [texts["services_title"].strip(), ""]
    for item in texts.services:
        lines.append(f"▫️ <b>{item['name']}</b> — {item['price']}")
        if item.get("description"):
            lines.append(f"<i>{item['description']}</i>")
        lines.append("")
    lines.append(texts["services_footer"].strip())
    return "\n".join(lines)


@router.callback_query(F.data == "menu:services")
async def cb_services(callback: CallbackQuery) -> None:
    await show(callback, build_services_text(), services_info_kb())


# ---------- Частые вопросы ----------

@router.callback_query(F.data == "menu:faq")
async def cb_faq_list(callback: CallbackQuery) -> None:
    await show(callback, texts["faq_title"].strip(), faq_list_kb())


@router.callback_query(F.data.startswith("faq:"))
async def cb_faq_answer(callback: CallbackQuery) -> None:
    index = int(callback.data.split(":")[1])
    # Список вопросов могли изменить через /reload — проверяем номер
    if index >= len(texts.faq):
        await callback.answer(texts["outdated_button"], show_alert=True)
        return
    item = texts.faq[index]
    text = f"<b>{item['question']}</b>\n\n{str(item['answer']).strip()}"
    await show(callback, text, back_kb("menu:faq"))


# ---------- Контакты ----------

@router.callback_query(F.data == "menu:contacts")
async def cb_contacts(callback: CallbackQuery) -> None:
    await show(callback, texts["contacts"].strip(), back_kb())


# ---------- Всё остальное ----------

@router.callback_query()
async def cb_unknown(callback: CallbackQuery) -> None:
    """Нажата кнопка из старого сообщения, которую бот уже не знает."""
    await callback.answer(texts["outdated_button"], show_alert=True)


@router.message()
async def msg_unknown(message: Message) -> None:
    """Любое сообщение, которое бот не понял."""
    await message.answer(texts["unknown"], reply_markup=ReplyKeyboardRemove())
