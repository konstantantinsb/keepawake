"""
i18n — лёгкий модуль интернационализации для KeepAwake.

Хранит переводы в JSON-файлах в locales/. Поддерживает fallback на язык
по умолчанию, формат-строки с именованными плейсхолдерами ({name}),
самоименование языков (Русский/English/Latviešu).

API:
    i18n.load("en")            — загрузить все локали
    i18n.set_lang("ru")        — переключить активный язык
    i18n.t("menu.exit")        — перевести точечный ключ
    i18n.t("menu.greet", name="Bob") — перевести с плейсхолдерами
    i18n.get_lang()            — текущий язык
    i18n.supported()           — кортеж поддерживаемых кодов
    i18n.LANG_NAMES            — словарь самоимён языков
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LANG = "en"
SUPPORTED: tuple[str, ...] = ("en", "ru", "lv")

# Самоименование языков: каждый называет себя так, как принято у него.
# Эти строки не зависят от текущего языка интерфейса.
LANG_NAMES: dict[str, str] = {
    "en": "English",
    "ru": "Русский",
    "lv": "Latviešu",
}

_translations: dict[str, dict] = {}
_current_lang: str = DEFAULT_LANG
_loaded: bool = False


def load(lang: str = DEFAULT_LANG) -> None:
    """Загрузить JSON-файлы локалей. lang — желаемый начальный язык.
    Если lang нет в SUPPORTED, используется DEFAULT_LANG."""
    global _current_lang, _loaded
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    _current_lang = lang
    _translations.clear()
    for code in SUPPORTED:
        path = LOCALES_DIR / f"{code}.json"
        if path.exists():
            with path.open(encoding="utf-8") as f:
                _translations[code] = json.load(f)
        else:
            _translations[code] = {}
    if not _translations.get(DEFAULT_LANG):
        # Дефолт критичен — без него fallback не сработает.
        raise RuntimeError(
            f"Default locale '{DEFAULT_LANG}' missing or empty in {LOCALES_DIR}"
        )
    _loaded = True


def set_lang(lang: str) -> bool:
    """Переключить активный язык. Возвращает True если язык поддерживается."""
    global _current_lang
    if not _loaded:
        load(lang)
        return _current_lang == lang
    if lang in SUPPORTED:
        _current_lang = lang
        return True
    return False


def get_lang() -> str:
    return _current_lang


def supported() -> tuple[str, ...]:
    return SUPPORTED


def t(key: str, **kwargs: Any) -> str:
    """Перевести точечный ключ. Поддерживает плейсхолдеры {name}.
    Fallback: current → default → key-as-is."""
    if not _loaded:
        load(_current_lang)
    parts = key.split(".")

    def lookup_in(lang_code: str) -> str | None:
        tree = _translations.get(lang_code, {})
        node: Any = tree
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        return node if isinstance(node, str) else None

    # Сначала текущий, потом дефолт
    val = lookup_in(_current_lang)
    if val is None:
        val = lookup_in(DEFAULT_LANG)
    if val is None:
        return key
    if kwargs:
        try:
            return val.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return val
    return val
