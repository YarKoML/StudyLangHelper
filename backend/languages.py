"""Справочник поддерживаемых языков: коды ↔ локализованные названия."""

LANG_CODES: list[str] = ["ru", "en", "es", "de", "fr", "it", "pt", "zh", "ja", "ko"]

LANG_NAMES: dict[str, dict[str, str]] = {
    "ru": {"ru": "Русский", "en": "Russian"},
    "en": {"ru": "Английский", "en": "English"},
    "es": {"ru": "Испанский", "en": "Spanish"},
    "de": {"ru": "Немецкий", "en": "German"},
    "fr": {"ru": "Французский", "en": "French"},
    "it": {"ru": "Итальянский", "en": "Italian"},
    "pt": {"ru": "Португальский", "en": "Portuguese"},
    "zh": {"ru": "Китайский", "en": "Chinese"},
    "ja": {"ru": "Японский", "en": "Japanese"},
    "ko": {"ru": "Корейский", "en": "Korean"},
}


def lang_name(code: str, ui_locale: str = "ru") -> str:
    names = LANG_NAMES.get(code)
    if not names:
        return code
    return names.get(ui_locale, names.get("en", code))


def dictionary_name(native_lang: str, study_lang: str, ui_locale: str = "ru") -> str:
    return f"{lang_name(native_lang, ui_locale)} → {lang_name(study_lang, ui_locale)}"


def supported_languages(ui_locale: str = "ru") -> list[dict[str, str]]:
    return [{"code": code, "name": lang_name(code, ui_locale)} for code in LANG_CODES]
