"""
Клавиатуры (кнопки) бота. Подписи кнопок берутся из texts.yaml.

callback_data — это скрытая «метка» кнопки, по которой бот понимает,
что именно нажали. Пользователь её не видит.
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from texts import texts


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню: 4 кнопки, по две в ряд."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("services"), callback_data="menu:services")
    kb.button(text=texts.button("faq"), callback_data="menu:faq")
    kb.button(text=texts.button("lead"), callback_data="menu:lead")
    kb.button(text=texts.button("contacts"), callback_data="menu:contacts")
    kb.adjust(2)
    return kb.as_markup()


def back_kb(target: str = "menu:main") -> InlineKeyboardMarkup:
    """Одна кнопка «Назад». target — куда вернуться."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("back"), callback_data=target)
    return kb.as_markup()


def services_info_kb() -> InlineKeyboardMarkup:
    """Под списком услуг: «Оставить заявку» и «Назад»."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("lead"), callback_data="menu:lead")
    kb.button(text=texts.button("back"), callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def faq_list_kb() -> InlineKeyboardMarkup:
    """Список вопросов — каждый вопрос отдельной кнопкой."""
    kb = InlineKeyboardBuilder()
    for index, item in enumerate(texts.faq):
        kb.button(text=str(item["question"]), callback_data=f"faq:{index}")
    kb.button(text=texts.button("back"), callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены заявки."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("cancel"), callback_data="form:cancel")
    return kb.as_markup()


def share_phone_kb() -> ReplyKeyboardMarkup:
    """
    Кнопка «Отправить мой номер» внизу экрана.
    Telegram сам подставит номер, привязанный к аккаунту.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.button("share_phone"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def services_choice_kb() -> InlineKeyboardMarkup:
    """Выбор услуги в форме заявки."""
    kb = InlineKeyboardBuilder()
    for index, item in enumerate(texts.services):
        kb.button(text=str(item["name"]), callback_data=f"svc:{index}")
    kb.button(text=texts.button("cancel"), callback_data="form:cancel")
    kb.adjust(1)
    return kb.as_markup()


def skip_comment_kb() -> InlineKeyboardMarkup:
    """Кнопки на шаге комментария: «Пропустить» и «Отменить»."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("skip"), callback_data="form:skip")
    kb.button(text=texts.button("cancel"), callback_data="form:cancel")
    kb.adjust(1)
    return kb.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение заявки: «Отправить» / «Изменить»."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("send"), callback_data="form:send")
    kb.button(text=texts.button("edit"), callback_data="form:edit")
    kb.button(text=texts.button("cancel"), callback_data="form:cancel")
    kb.adjust(2, 1)
    return kb.as_markup()


def edit_field_kb() -> InlineKeyboardMarkup:
    """Выбор, какое поле заявки изменить."""
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.button("edit_name"), callback_data="edit:name")
    kb.button(text=texts.button("edit_phone"), callback_data="edit:phone")
    kb.button(text=texts.button("edit_service"), callback_data="edit:service")
    kb.button(text=texts.button("edit_comment"), callback_data="edit:comment")
    kb.button(text=texts.button("back"), callback_data="form:back_to_confirm")
    kb.adjust(2, 2, 1)
    return kb.as_markup()
