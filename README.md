# StudyLangHelper

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58+-FF4B4B?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

📖 [English documentation](README_ENG.md)

Приложение для изучения иностранных языков: карточки со словами, статистика, календарь активности, библиотека PDF-книг с переводом через LLM.

## Оглавление

- [StudyLangHelper](#studylanghelper)
  - [Оглавление](#оглавление)
  - [✨ Возможности](#-возможности)
    - [🔐 Авторизация](#-авторизация)
    - [🏠 Главный экран](#-главный-экран)
    - [🃏 Карточки](#-карточки)
    - [⚙️ Настройки](#️-настройки)
    - [📚 Библиотека](#-библиотека)
    - [📤 Загрузка книг](#-загрузка-книг)
  - [🛠 Стек](#-стек)
  - [🐳 Быстрый старт (Docker)](#-быстрый-старт-docker)
  - [⚙️ Локальная установка](#️-локальная-установка)
    - [Запуск (два терминала)](#запуск-два-терминала)
  - [🗄 База данных](#-база-данных)
  - [🔧 Переменные окружения](#-переменные-окружения)
  - [🧪 Тесты](#-тесты)
  - [📏 Линтинг](#-линтинг)
  - [📁 Структура проекта](#-структура-проекта)
  - [📄 Лицензия](#-лицензия)

## ✨ Возможности

### 🔐 Авторизация
- Регистрация и вход по имени пользователя / паролю
- JWT-токены (HS256), хранение паролей через bcrypt
- Индивидуальное хранение: словари, API-ключи LLM, библиотека книг — изолированы между пользователями
- При первой регистрации существующие словари (если БД была создана без авторизации) автоматически привязываются к первому пользователю

<!-- Скриншот: страница входа / регистрации. Вставьте: ![login](screenshots/login.png) -->

![login](screenshots/login.png)

<!-- Скриншот: сайдбар с именем пользователя и кнопкой «Выйти». Вставьте: ![sidebar-user](screenshots/sidebar-user.png) -->

![sidebar-user](screenshots/sidebar-user.png)

### 🏠 Главный экран
- Календарь активности (heatmap в стиле GitHub за текущий год)
- Статистика: всего слов, выучено, изучается, % выученных, серия дней

<!-- Скриншот: главный экран с календарём активности и статистикой. Вставьте: ![home](screenshots/home.png) -->
![home](screenshots/home.png)


### 🃏 Карточки
- Режимы: повторение изученных слов / изучение новых
- Направление: слово → перевод / перевод → слово
- Выбор количества карточек
- 4 варианта ответа, подсветка правильного при ошибке
- Итоговые результаты в процентах

<!-- Скриншот: карточка с 4 вариантами ответа. Вставьте: ![cards](screenshots/cards.png) -->

![cards](screenshots/cards.png)

### ⚙️ Настройки
- **Словари**: создание словарей по паре языков (родной ↔ изучаемый). Для пары EN↔RU автоматически добавляется 10 популярных слов. Для остальных пар — ручной ввод.
- **Слова**: добавление/удаление пар, просмотр статуса (выучено/изучается), фильтрация
- **Порог N**: настройка количества правильных ответов, после которого слово считается выученным (per словарь)
- **LLM (Bring Your Own Key)**: ввод URL до `/v1/chat/completions` от провайдера, API-ключ, загрузка доступных моделей через `/v1/models`, выбор модели. Ключ хранится в БД (плоскопрочно для self-hosted), не возвращается в GET-запросах.

<!-- Скриншот: вкладка LLM в Настройках (ввод base_url, api_key, выбор модели). Вставьте: ![settings-llm](screenshots/settings-llm.png) -->
![settings-llm](screenshots/settings-llm.png)
<!-- Скриншот: вкладка «Словари» в Настройках. Вставьте: ![settings-dicts](screenshots/settings-dicts.png) -->
![settings-dicts](screenshots/settings-dicts.png)


### 📚 Библиотека
- Загрузка PDF-книг (текст извлекается постранично через pdfplumber, бинарные файлы не хранятся)
- Чтение с постраничной навигацией (кнопки «←» / «→»)
- Перевод выделенного слова или фразы через LLM прямо во время чтения
- Добавление переведённого слова в выбранный словарь
- Прогресс чтения: прогресс-бар на каждой книге + сохранение позиции (продолжение с места остановки)
- Дедупликация: повторная загрузка файла с тем же именем отклоняется (409 Conflict)

<!-- Скриншот: список книг с прогресс-барами прочтения. Вставьте: ![library-list](screenshots/library-list.png) -->
![library-list](screenshots/library-list.png)

<!-- Скриншот: режим чтения книги с панелью перевода справа. Вставьте: ![library-read](screenshots/library-read.png) -->
![library-read](screenshots/library-read.png)


### 📤 Загрузка книг
- Отдельная страница для загрузки PDF-файлов
- Визуальный индикатор загрузки (`st.status` с этапами «Отправка файла и парсинг PDF…» → «Готово»)
- Защита от дубликатов на уровне API (409 Conflict при повторной загрузке файла с тем же именем)

<!-- Скриншот: страница «Загрузка книг» с индикатором st.status. Вставьте: ![upload](screenshots/upload.png) -->
![upload](screenshots/upload.png) 


## 🛠 Стек

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI + SQLModel + SQLite |
| Auth | JWT (PyJWT) + bcrypt |
| PDF parsing | pdfplumber |
| Frontend | Streamlit + Plotly |
| LLM | OpenAI-совместимый API (BYOK) |
| Среда | Python 3.12 |
| Менеджер пакетов | uv |
| Контейнеры | Docker Compose |

## 🐳 Быстрый старт (Docker)

```bash
docker compose up -d --build
```

- Backend: http://localhost:8000 (документация: http://localhost:8000/docs)
- Frontend: http://localhost:8501

База данных SQLite хранится в `./data/studylanghelper.db` (bind mount) и сохраняется между перезапусками. Директория `data/` создаётся автоматически и исключена из git (`.gitignore`).

Остановка:

```bash
docker compose down          # остановить, данные сохранятся
```

Чтобы сбросить БД — удалите директорию `data/` вручную:

```bash
docker compose down
Remove-Item -Recurse -Force data   # Windows PowerShell
# или: rm -rf data                  # Linux/macOS
```

## ⚙️ Локальная установка

Зависимости разделены на optional-groups `backend` и `frontend`. Для локальной разработки установите обе:

```bash
uv sync --extra backend --extra frontend
# или эквивалентно:
uv sync --group local
```

> ⚠️ **Примечание**: `uv sync` без аргументов поставит только базовые зависимости (пустой набор).
> Обязательно указывайте `--extra backend --extra frontend` или `--group local` для полноценной работы.

### Запуск (два терминала)

```bash
# 1. Backend
uv run uvicorn backend.main:app --reload --port 8000

# 2. Frontend
uv run streamlit run frontend/app.py
```

## 🗄 База данных

- **Расположение**: `data/studylanghelper.db` (создаётся автоматически при первом запуске)
- **Docker**: bind mount `./data:/app/data`
- **В gitignore**: да (`.gitignore`)
- **Сброс**: удалите директорию `data/`
- **Миграции**: при запуске автоматически добавляется колонка `user_id` в таблицу `dictionary` (для БД, созданных до введения авторизации)

## 🔧 Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|--------------|----------|
| `DATABASE_URL` | `sqlite:///<project>/data/studylanghelper.db` | URL подключения к БД |
| `CORS_ORIGINS` | `http://localhost:8501,http://127.0.0.1:8501` | Разделённый запятыми список CORS-источников |
| `JWT_SECRET` | `dev-secret-change-me` | Секрет для подписи JWT-токенов. **Обязательно измените в production** |
| `API_BASE_URL` | `http://localhost:8000` | URL backend для frontend (Streamlit) |

> ⚠️ В production обязательно установите `JWT_SECRET` в случайную строку длиной ≥ 32 байт.

## 🧪 Тесты

```bash
uv run pytest
```

29 тестов покрывают: авторизацию (регистрация, логин, изоляция пользователей), словари, слова, учебные сессии, статистику, LLM (с моками httpx), библиотеку (с генерацией PDF через reportlab).

## 📏 Линтинг

```bash
uv run ruff check .
uv run ruff format --check .
```

## 📁 Структура проекта

```
StudyLangHelper/
├── backend/                  # FastAPI + SQLModel + SQLite
│   ├── main.py               # точка входа, регистрация роутеров
│   ├── security.py           # JWT (PyJWT) + bcrypt, get_current_user
│   ├── llm.py                # OpenAI-совместимый LLM-клиент (BYOK)
│   ├── parsing.py            # PDF → постраничный текст (pdfplumber)
│   ├── config.py             # DATABASE_URL, CORS_ORIGINS
│   ├── database.py           # engine, create_db_and_tables, миграция user_id
│   ├── models.py             # User, Dictionary, Word, StudySession, Answer, LLMSettings, Book
│   ├── schemas.py            # Pydantic-схемы (auth, LLM, library, ...)
│   ├── languages.py          # справочник языков
│   ├── seed.py               # 10 EN↔RU слов для автосидирования
│   ├── routers/
│   │   ├── auth.py           # регистрация, логин, /me
│   │   ├── dictionaries.py   # CRUD словарей (под auth)
│   │   ├── words.py          # CRUD слов (под auth)
│   │   ├── study.py          # учебные сессии, ответы (под auth)
│   │   ├── stats.py          # статистика, календарь (под auth)
│   │   ├── llm.py            # настройки LLM, список моделей, перевод
│   │   └── library.py        # загрузка/чтение/удаление PDF-книг
│   └── Dockerfile
├── frontend/                 # Streamlit + Plotly
│   ├── app.py                # auth gate, навигация, logout
│   ├── api_client.py         # HTTP-клиент с Bearer-токеном
│   ├── config.py             # API_BASE_URL
│   ├── i18n.py               # локализация (ru/en)
│   ├── state.py              # session_state хелперы
│   ├── pages/
│   │   ├── login.py          # вход / регистрация
│   │   ├── home.py           # календарь активности + статистика
│   │   ├── cards.py          # учебные карточки
│   │   ├── upload.py         # загрузка PDF-книг
│   │   ├── library.py        # чтение книг + перевод через LLM
│   │   └── settings.py       # словари, слова, порог N, LLM
│   └── Dockerfile
├── data/                     # SQLite DB (gitignored)
├── tests/
│   ├── conftest.py           # in-memory SQLite, authed_client fixture
│   └── api/test_api.py       # 29 тестов
├── docker-compose.yml
└── pyproject.toml
```

## 📄 Лицензия

Распространяется по [лицензии MIT](LICENSE).