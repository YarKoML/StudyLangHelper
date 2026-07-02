"""10 популярных EN↔RU слов для автосидирования словаря en↔ru."""

EN_RU_SEED: list[tuple[str, str]] = [
    ("hello", "привет"),
    ("goodbye", "до свидания"),
    ("please", "пожалуйста"),
    ("thank you", "спасибо"),
    ("yes", "да"),
    ("no", "нет"),
    ("water", "вода"),
    ("friend", "друг"),
    ("book", "книга"),
    ("house", "дом"),
]


def seed_words(native_lang: str, study_lang: str) -> list[tuple[str, str]]:
    """Возвращает [(word, translation), ...] для пары языков.

    word — на изучаемом языке, translation — на родном.
    Сид доступен только для пары (en, ru) в любом направлении.
    """
    pair = {native_lang, study_lang}
    if pair != {"en", "ru"}:
        return []
    if study_lang == "en":
        return list(EN_RU_SEED)
    return [(ru, en) for en, ru in EN_RU_SEED]
