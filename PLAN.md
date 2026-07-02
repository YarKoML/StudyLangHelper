# StudyLangHelper — План реализации

Приложение для изучения иностранных языков: FastAPI + SQLite (SQLModel) backend, Streamlit frontend.

## Подтверждённые решения

1. **Сид 10 популярных слов** применяется для **обоих** направлений EN↔RU: при создании словаря с парой (`en`, `ru`) в любом направлении (`ru→en` или `en→ru`) сеем 10 слов. Слово/перевод кладутся в правильные поля в зависимости от того, какой язык изучаемый. Для всех остальных пар — ручной ввод ≥10 слов.
2. **Коды языков** — ISO 639-1 из предзаданного списка в выпадающем меню (не свободный ввод).
3. **Названия словарей** — человекочитаемые, локализованные по языку интерфейса через маппинг кодов на названия (напр. при `ui_locale=ru`: "Русский → Английский"; при `ui_locale=en`: "Russian → English").

## Стек и зависимости

- Python 3.12, `uv` (уже настроено)
- Добавить в `pyproject.toml`:
  - `fastapi`, `uvicorn[standard]`, `sqlmodel`, `httpx`, `plotly` (`streamlit` уже есть)
  - dev: `ruff`, `pytest`, `pytest-httpx`

## Структура проекта

```
backend/                      # FastAPI backend
├── __init__.py
├── config.py                 # API_BASE_URL, настройки БД
├── main.py                   # FastAPI app, CORS, startup (create tables)
├── deps.py                   # get_session()
├── database.py               # engine, create_db_and_tables()
├── models.py                 # SQLModel-таблицы
├── schemas.py                # create/read/update схемы
├── seed.py                   # 10 популярных EN↔RU слов
├── languages.py              # маппинг кодов ↔ названий (ru/en локализации)
└── routers/
    ├── __init__.py
    ├── dictionaries.py
    ├── words.py
    ├── study.py
    └── stats.py
frontend/                     # Streamlit
├── __init__.py
├── app.py                    # entrypoint: st.navigation + сайдбар
├── api_client.py             # httpx-обёртка, @st.cache_data
├── i18n.py                   # словари ru/en, t(key)
├── state.py                  # хелперы session_state
├── config.py                 # API_BASE_URL
└── pages/
    ├── home.py
    ├── cards.py
    └── settings.py
tests/
├── __init__.py
└── api/
    ├── __init__.py
    └── test_api.py
```

## Модель данных (SQLModel)

- **Dictionary**: `id`, `native_lang` (code), `study_lang` (code), `n_to_learn` (int, порог выученности — per словарь), `created_at`. Unique-констрейнт `(native_lang, study_lang)`.
- **Word**: `id`, `dictionary_id` (FK → dictionary.id, ondelete CASCADE), `word` (на изучаемом языке), `translation` (на родном языке), `correct_count` (int, default 0), `learned` (bool, кэшируется: `correct_count >= dictionary.n_to_learn`), `created_at`.
- **StudySession**: `id`, `dictionary_id` (FK), `mode` ("review" | "new"), `direction` ("word_to_translation" | "translation_to_word"), `total`, `correct`, `started_at`, `finished_at`.
- **Answer**: `id`, `session_id` (FK), `word_id` (FK), `chosen`, `is_correct`, `answered_at`.

## Сидирование (10 EN↔RU слов)

Список: hello/привет, goodbye/до свидания, please/пожалуйста, thank you/спасибо, yes/да, no/нет, water/вода, friend/друг, book/книга, house/дом.

- При `study_lang="en"`, `native_lang="ru"` → word="hello", translation="привет", ...
- При `study_lang="ru"`, `native_lang="en"` → word="привет", translation="hello", ...
- Триггер: в `POST /dictionaries` после создания словаря проверяем пару языков; если это `(en, ru)` в любом порядке — сеем 10 слов. Для остальных пар — ничего, фронтенд заставит ввести ≥10.

## Backend (FastAPI) — эндпоинты

### Dictionaries

- `POST /dictionaries` — `{native_lang, study_lang, n_to_learn}` → создаёт (+ сид для en↔ru). 409 если пара уже существует.
- `GET /dictionaries` — список.
- `PATCH /dictionaries/{id}` — изменить `n_to_learn` (пересчёт `learned` всех слов словаря).
- `DELETE /dictionaries/{id}` — CASCADE удаляет слова, сессии, ответы.

### Words

- `POST /dictionaries/{dict_id}/words` — добавить пару `{word, translation}`.
- `POST /dictionaries/{dict_id}/words/batch` — пакетное добавление `[{word, translation}, ...]` (для инициализации ≥10 слов).
- `GET /dictionaries/{dict_id}/words?learned=all|true|false` — список со статусом.
- `PATCH /words/{id}` — обновить пару.
- `DELETE /words/{id}`.

### Study

- `POST /study/sessions` — `{dictionary_id, mode, direction, count}`.
  - `mode=review` → только слова с `learned=True`; если нет выученных → 400 "нет выученных слов для повторения".
  - `mode=new` → слова с `correct_count==0`; если нет → 400 "нет новых слов".
  - Если всего слов в словаре <4 → 400 "добавьте минимум 4 слова для генерации вариантов".
  - Возвращает `session_id` + `questions: [{word_id, prompt, options[4]}]` (1 верный + 3 случайных перевода из того же словаря, перемешанные).
- `POST /study/sessions/{id}/answer` — `{word_id, chosen}` → записывает Answer; при верном `correct_count += 1`, обновляет `learned` (повторение тоже увеличивает); возвращает `{is_correct, correct_translation}`.
- `POST /study/sessions/{id}/finish` — финализирует сессию (`finished_at`, итоги); возвращает `{total, correct, wrong, correct_pct, wrong_pct}`.

### Stats

- `GET /stats?dictionary_id=...` — `{total_words, learned_words, learning_words, learned_pct, streak_days}`.
- `GET /stats/calendar?dictionary_id=...&year=YYYY` — `[{date, count}]` карта активности (сессии за день) для хитмапа.

### Languages (справочник)

- `GET /languages` — список поддерживаемых кодов с названиями, локализованными по `?ui_locale=ru|en`.

## Frontend (Streamlit)

### `app.py` entrypoint — `st.navigation` (новый API)

```python
pg = st.navigation([
    st.Page("pages/home.py", title="Главная", url_path="home", default=True),
    st.Page("pages/cards.py", title="Карточки", url_path="cards"),
    st.Page("pages/settings.py", title="Настройки", url_path="settings"),
])
```

Сайдбар (в entrypoint, чтобы state сохранялся между страницами):
- язык интерфейса (ru/en, default ru) → `key="ui_locale"`;
- выбор текущего словаря (`key="dict_id"`) — выпадающий список из `/dictionaries`, отображаются человекочитаемые локализованные названия.

### i18n

Словарь `{"ru": {...}, "en": {...}}` + `t(key)` из `st.session_state["ui_locale"]`. Названия языков берём с бэкенда (`/languages?ui_locale=...`) и кэшируем через `@st.cache_data`.

### api_client

httpx-клиент с базовым URL из `config.py` (`http://localhost:8000`). GET-запросы справочных данных обёрнуты в `@st.cache_data(ttl=60)`; mutation-вызовы (POST/PATCH/DELETE) сбрасывают кэш через `st.cache_data.clear()`.

### Home page

- Plotly heatmap (оси X=недели года, Y=дни недели, GitHub-style) из `/stats/calendar`. Цвет/интенсивность по числу сессий за день.
- `st.metric`-карточки: добавлено слов, выучено, изучается, % выученных, текущий streak.

### Cards page

1. Экран настройки: `st.radio` режим (повторение / новые), `st.selectbox` направление (слово→перевод / перевод→слово), `st.number_input` количество (1–доступно, динамический максимум из доступных слов). Кнопка "Начать" → POST `/study/sessions`.
2. Экран сессии: состояние в `st.session_state` (`session_id`, `questions`, `i`, `correct`, `wrong`, `answered`). Показываем `prompt`, 4 `st.button` (варианты). При клике → POST `/answer`, показ "Верно"/"Неверно, правильный перевод: …", блокировка кнопок, кнопка "Далее" → `i+=1`, `st.rerun()`. На последнем вопросе — POST `/finish` и экран результатов: `st.metric`/`st.progress` с %, кнопка "Завершить" → очистка state, возврат к настройке.

### Settings page — `st.tabs`

- **"Словари"**: список существующих с человекочитаемыми названиями; форма создания нового (два `st.selectbox` — родной/изучаемый язык из `/languages`, `n_to_learn`); при создании не-en↔ru пары → `@st.dialog` с пакетным вводом ≥10 пар (валидация: минимум 10, иначе кнопка "Сохранить" disabled). Для en↔ru — сидируется автоматически, диалог не нужен.
- **"Слова"**: форма `st.form` добавления пары; `st.dataframe`/`st.data_editor` существующих слов со столбцом-статусом (выучен/изучается, подсветка через цвет/иконку); фильтр `st.checkbox` "только выученные"/"только изучаемые"/"все"; удаление через `@st.dialog` подтверждения.
- **"Порог N"**: `st.number_input` + кнопка "Сохранить" (PATCH с пересчётом `learned`).

## Запуск

- API: `uv run uvicorn backend.main:app --reload --port 8000`
- UI: `uv run streamlit run frontend/app.py`
- CORS на FastAPI: `http://localhost:8501`.
- README с инструкцией запуска обоих процессов.

## Тесты (базовые)

API через `TestClient`, БД in-memory (`sqlite://`):

1. Создание словаря `ru→en` → проверка сида 10 слов.
2. Создание словаря `en→ru` → проверка сида 10 слов (корректное распределение word/translation).
3. Создание словаря `ru→es` → пусто, требуется ручной ввод.
4. Пакетный ввод 10 слов для `ru→es`.
5. Попытка стартовать сессию при <4 словах → 400.
6. Старт сессии `mode=new` → ответы → `correct_count` растёт, `learned` становится True при достижении `n_to_learn`.
7. Смена `n_to_learn` → пересчёт `learned` всех слов.
8. Сессия `mode=review` → только выученные слова; если выученных нет → 400.
9. `/stats` и `/stats/calendar` возвращают корректные данные после сессий.

## Порядок реализации (шаги)

1. Обновить `pyproject.toml` (зависимости), `uv sync`.
2. `config.py`, `api/database.py`, `api/models.py`, `api/schemas.py`, `api/deps.py`, `api/seed.py`, `api/languages.py`.
3. `api/routers/*` (dictionaries → words → study → stats).
4. `api/main.py` (CORS, startup, подключение роутеров).
5. Тесты API, прогон `pytest`.
6. `frontend/i18n.py`, `frontend/api_client.py`, `frontend/state.py`.
7. `frontend/app.py` (entrypoint + сайдбар).
8. `frontend/pages/home.py`, `cards.py`, `settings.py`.
9. README с инструкцией запуска.
10. Финальная проверка: запуск обоих процессов, ручной прогон сценария.