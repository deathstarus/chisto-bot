"""
Обработчики (handlers) — функции, которые отвечают на команды и кнопки.

Порядок подключения важен: админ-команды и форма заявки идут раньше
общего раздела, где в самом конце стоит «ловушка» для непонятных сообщений.
"""

from aiogram import Router

from . import admin, common, lead_form


def get_routers() -> list[Router]:
    return [admin.router, common.start_router, lead_form.router, common.router]
