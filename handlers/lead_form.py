"""
Пошаговая форма заявки (FSM — «машина состояний»).

Бот запоминает, на каком шаге находится клиент:
    имя → телефон → услуга → комментарий → подтверждение

На шаге подтверждения можно «Отправить» заявку или «Изменить» любое поле.
"""

import logging
import re
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import ADMIN_ID
from database import add_lead
from keyboards import (
    cancel_kb,
    confirm_kb,
    edit_field_kb,
    main_menu_kb,
    services_choice_kb,
    share_phone_kb,
    skip_comment_kb,
)
from texts import texts

router = Router(name="lead_form")
log = logging.getLogger(__name__)


class LeadForm(StatesGroup):
    """Шаги формы заявки."""
    name = State()
    phone = State()
    service = State()
    comment = State()
    confirm = State()


# ---------- Проверка телефона ----------

# Разрешаем только цифры, пробелы, плюс, дефисы и скобки
PHONE_ALLOWED = re.compile(r"^[\d\s()+\-]+$")


def normalize_phone(raw: str) -> str | None:
    """
    Проверяет российский номер и приводит его к виду +7 (900) 123-45-67.
    Принимает: +7 900 123-45-67, 8 (900) 123 45 67, 79001234567, 9001234567.
    Если номер неверный — возвращает None.
    """
    raw = raw.strip()
    if not PHONE_ALLOWED.match(raw):
        return None

    digits = re.sub(r"\D", "", raw)

    if len(digits) == 11:
        # «+8...» — это не российский формат, а «+7...» и «8...» — да
        if raw.startswith("+") and digits[0] != "7":
            return None
        if digits[0] not in "78":
            return None
        digits = digits[1:]
    elif len(digits) == 10:
        if raw.startswith("+"):
            return None
    else:
        return None

    # Российские коды начинаются с 3, 4, 8 (городские) или 9 (мобильные)
    if digits[0] not in "3489":
        return None

    return f"+7 ({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"


# ---------- Вспомогательные функции ----------

def format_comment(comment: str | None) -> str:
    """Комментарий для показа (безопасно экранированный)."""
    return escape(comment) if comment else texts.form("no_comment")


async def show_confirmation(message: Message, state: FSMContext) -> None:
    """Показывает заполненную заявку и кнопки «Отправить / Изменить»."""
    data = await state.get_data()
    await state.update_data(editing=False)
    await state.set_state(LeadForm.confirm)
    await message.answer(
        texts.form(
            "confirm",
            name=escape(data["name"]),
            phone=data["phone"],
            service=escape(data["service"]),
            comment=format_comment(data.get("comment")),
        ),
        reply_markup=confirm_kb(),
    )


async def is_editing(state: FSMContext) -> bool:
    """True — клиент правит одно поле и после него вернётся к подтверждению."""
    return bool((await state.get_data()).get("editing"))


# ---------- Начало и отмена ----------

@router.callback_query(F.data == "menu:lead")
async def start_form(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await state.set_state(LeadForm.name)
    await callback.message.answer(texts.form("ask_name"), reply_markup=cancel_kb())


@router.callback_query(F.data == "form:cancel")
async def cancel_form_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    # ReplyKeyboardRemove убирает кнопку «Отправить мой номер», если она была
    await callback.message.answer(texts.form("cancelled"), reply_markup=ReplyKeyboardRemove())
    await callback.message.answer(texts["main_menu_text"], reply_markup=main_menu_kb())


@router.message(Command("cancel"), StateFilter(LeadForm))
async def cancel_form_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.form("cancelled"), reply_markup=ReplyKeyboardRemove())
    await message.answer(texts["main_menu_text"], reply_markup=main_menu_kb())


# ---------- Шаг 1: имя ----------

@router.message(LeadForm.name, F.text, ~F.text.startswith("/"))
async def get_name(message: Message, state: FSMContext) -> None:
    name = " ".join(message.text.split())  # убираем лишние пробелы
    if not 2 <= len(name) <= 50:
        await message.answer(texts.form("bad_name"))
        return

    await state.update_data(name=name)
    if await is_editing(state):
        await show_confirmation(message, state)
        return

    await state.set_state(LeadForm.phone)
    await message.answer(texts.form("ask_phone", name=escape(name)),
                         reply_markup=share_phone_kb())


@router.message(LeadForm.name)
async def get_name_wrong(message: Message) -> None:
    await message.answer(texts.form("bad_name"))


# ---------- Шаг 2: телефон ----------

@router.message(LeadForm.phone, F.contact)
@router.message(LeadForm.phone, F.text)
async def get_phone(message: Message, state: FSMContext) -> None:
    # Номер пришёл либо кнопкой «Отправить мой номер», либо текстом
    raw = message.contact.phone_number if message.contact else message.text
    phone = normalize_phone(raw)
    if phone is None:
        await message.answer(texts.form("bad_phone"), reply_markup=share_phone_kb())
        return

    await state.update_data(phone=phone)
    # Убираем кнопку «Отправить мой номер» с экрана
    await message.answer(f"📱 {phone} ✅", reply_markup=ReplyKeyboardRemove())

    if await is_editing(state):
        await show_confirmation(message, state)
        return

    await state.set_state(LeadForm.service)
    await message.answer(texts.form("ask_service"), reply_markup=services_choice_kb())


@router.message(LeadForm.phone)
async def get_phone_wrong(message: Message) -> None:
    await message.answer(texts.form("bad_phone"), reply_markup=share_phone_kb())


# ---------- Шаг 3: услуга ----------

@router.callback_query(LeadForm.service, F.data.startswith("svc:"))
async def get_service(callback: CallbackQuery, state: FSMContext) -> None:
    index = int(callback.data.split(":")[1])
    if index >= len(texts.services):
        # Список услуг изменили через /reload — показываем актуальный
        await callback.answer(texts["outdated_button"], show_alert=True)
        await callback.message.answer(texts.form("ask_service"),
                                      reply_markup=services_choice_kb())
        return

    await callback.answer()
    service = str(texts.services[index]["name"])
    await state.update_data(service=service)
    # Убираем кнопки у вопроса, чтобы не нажали повторно, и показываем выбор
    await callback.message.edit_text(
        f"{texts.form('ask_service')}\n\n🧽 <b>{escape(service)}</b>"
    )

    if await is_editing(state):
        await show_confirmation(callback.message, state)
        return

    await state.set_state(LeadForm.comment)
    await callback.message.answer(texts.form("ask_comment"), reply_markup=skip_comment_kb())


@router.message(LeadForm.service)
async def get_service_wrong(message: Message) -> None:
    await message.answer(texts.form("use_buttons"))


# ---------- Шаг 4: комментарий ----------

@router.message(LeadForm.comment, F.text, ~F.text.startswith("/"))
async def get_comment(message: Message, state: FSMContext) -> None:
    await state.update_data(comment=message.text.strip()[:1000])
    await show_confirmation(message, state)


@router.callback_query(LeadForm.comment, F.data == "form:skip")
async def skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(comment=None)
    await show_confirmation(callback.message, state)


@router.message(LeadForm.comment)
async def get_comment_wrong(message: Message) -> None:
    await message.answer(texts.form("ask_comment"), reply_markup=skip_comment_kb())


# ---------- Шаг 5: подтверждение ----------

@router.callback_query(LeadForm.confirm, F.data == "form:edit")
async def edit_choose(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=edit_field_kb())


@router.callback_query(LeadForm.confirm, F.data == "form:back_to_confirm")
async def edit_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=confirm_kb())


@router.callback_query(LeadForm.confirm, F.data.startswith("edit:"))
async def edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент выбрал поле для изменения — задаём вопрос заново."""
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(editing=True)
    field = callback.data.split(":")[1]
    data = await state.get_data()

    if field == "name":
        await state.set_state(LeadForm.name)
        await callback.message.answer(texts.form("ask_name"), reply_markup=cancel_kb())
    elif field == "phone":
        await state.set_state(LeadForm.phone)
        await callback.message.answer(
            texts.form("ask_phone", name=escape(data["name"])),
            reply_markup=share_phone_kb(),
        )
    elif field == "service":
        await state.set_state(LeadForm.service)
        await callback.message.answer(texts.form("ask_service"),
                                      reply_markup=services_choice_kb())
    else:  # comment
        await state.set_state(LeadForm.comment)
        await callback.message.answer(texts.form("ask_comment"),
                                      reply_markup=skip_comment_kb())


@router.callback_query(LeadForm.confirm, F.data == "form:send")
async def send_lead(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    data = await state.get_data()
    user = callback.from_user

    # Защита от двойного нажатия: сразу выходим из формы и убираем кнопки
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)

    # 1. Сохраняем заявку в базу
    lead_id, created_at = await add_lead(
        user_id=user.id,
        username=user.username,
        name=data["name"],
        phone=data["phone"],
        service=data["service"],
        comment=data.get("comment"),
    )

    # 2. Отправляем заявку администратору
    if user.username:
        tg_user = f"@{user.username}"
    else:
        tg_user = f'<a href="tg://user?id={user.id}">{escape(user.full_name)}</a>'

    admin_text = texts["admin_lead"].format(
        lead_id=lead_id,
        name=escape(data["name"]),
        phone=data["phone"],
        service=escape(data["service"]),
        comment=format_comment(data.get("comment")),
        tg_user=tg_user,
        created_at=created_at,
    ).strip()
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        # Например, администратор ещё не нажал /start у бота.
        # Заявка всё равно сохранена в базе — её видно по /leads.
        log.error("Не удалось отправить заявку №%s администратору: %s", lead_id, e)

    # 3. Благодарим клиента
    await callback.message.answer(texts.form("thanks", lead_id=lead_id))
    await callback.message.answer(texts["main_menu_text"], reply_markup=main_menu_kb())


@router.message(LeadForm.confirm)
async def confirm_wrong(message: Message) -> None:
    await message.answer(texts.form("use_buttons"))
