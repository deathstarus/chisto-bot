"""
Загрузка текстов бота из файла texts.yaml.

Все тексты, услуги, вопросы и контакты лежат в texts.yaml, чтобы их
можно было править без программиста. Здесь мы читаем этот файл,
проверяем, что в нём есть всё нужное, и даём к нему удобный доступ.
"""

from pathlib import Path
from typing import Any

import yaml

# Путь к файлу с текстами (лежит рядом с этим файлом)
TEXTS_PATH = Path(__file__).parent / "texts.yaml"

# Ключи, без которых бот работать не сможет. Если заказчик случайно
# удалит один из них — /reload сообщит об ошибке и оставит старые тексты.
REQUIRED_KEYS = [
    "welcome", "main_menu_text", "buttons",
    "services_title", "services_footer", "services",
    "faq_title", "faq", "contacts", "form", "admin_lead",
    "unknown", "outdated_button",
]


class TextsError(Exception):
    """Ошибка в файле texts.yaml (понятное описание для администратора)."""


class Texts:
    """Хранилище текстов. Один общий объект на весь бот."""

    def __init__(self, path: Path = TEXTS_PATH) -> None:
        self.path = path
        self.data: dict[str, Any] = {}

    def load(self) -> None:
        """
        Читает texts.yaml. Если файл с ошибкой — выбрасывает TextsError,
        а уже загруженные ранее тексты НЕ трогает (бот продолжает работать).
        """
        try:
            with open(self.path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise TextsError(f"Файл {self.path.name} не найден")
        except yaml.YAMLError as e:
            # Чаще всего это неправильные отступы или лишние кавычки
            raise TextsError(f"Ошибка в разметке {self.path.name}:\n{e}")

        self._validate(data)
        self.data = data  # подменяем тексты только если всё хорошо

    @staticmethod
    def _validate(data: Any) -> None:
        """Проверяет, что в файле есть все нужные разделы."""
        if not isinstance(data, dict):
            raise TextsError("Файл пустой или имеет неверную структуру")

        missing = [key for key in REQUIRED_KEYS if key not in data]
        if missing:
            raise TextsError("Не хватает разделов: " + ", ".join(missing))

        if not isinstance(data["services"], list) or not data["services"]:
            raise TextsError("Раздел services должен быть непустым списком")
        for i, s in enumerate(data["services"], start=1):
            if not isinstance(s, dict) or "name" not in s or "price" not in s:
                raise TextsError(f"У услуги №{i} должны быть поля name и price")

        if not isinstance(data["faq"], list):
            raise TextsError("Раздел faq должен быть списком")
        for i, q in enumerate(data["faq"], start=1):
            if not isinstance(q, dict) or "question" not in q or "answer" not in q:
                raise TextsError(f"У вопроса №{i} должны быть поля question и answer")

    # --- Удобный доступ к данным ---

    def __getitem__(self, key: str) -> Any:
        """texts["welcome"] — получить значение верхнего уровня."""
        return self.data[key]

    def button(self, key: str) -> str:
        """Подпись кнопки из раздела buttons."""
        return str(self.data["buttons"].get(key, key))

    def form(self, key: str, **kwargs: Any) -> str:
        """Текст из раздела form, с подстановкой значений {name} и т.п."""
        return str(self.data["form"][key]).format(**kwargs).strip()

    @property
    def services(self) -> list[dict]:
        return self.data["services"]

    @property
    def faq(self) -> list[dict]:
        return self.data["faq"]


# Общий объект, который импортируют все обработчики
texts = Texts()
