# StudyLangHelper

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58+-FF4B4B?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

📖 [English documentation](README_ENG.md)

Приложение для изучения иностранных языков: карточки со словами, статистика, календарь активности.

## Оглавление

- [Возможности](#-возможности)
- [Стек](#-стек)
- [Быстрый старт (Docker)](#-быстрый-старт-docker)
- [Локальная установка](#%EF%B8%8F-локальная-установка)
- [База данных](#-база-данных)
- [Тесты](#-тесты)
- [Линтинг](#-линтинг)
- [Структура проекта](#-структура-проекта)
- [Лицензия](#-лицензия)

## ✨ Возможности

### 🏠 Главный экран
- Календарь активности (heatmap в стиле GitHub за текущий год)
- Статистика: всего слов, выучено, изучается, % выученных, серия дней

### 🃏 Карточки
- Режимы: повторение изученных слов / изучение новых
- Направление: слово → перевод / перевод → слово
- Выбор количества карточек
- 4 варианта ответа, подсветка правильного при ошибке
- Итоговые результаты в процентах

### ⚙️ Настройки
- **Словари**: создание словарей по паре языков (родной ↔ изучаемый). Для пары EN↔RU автоматически добавляется 10 популярных слов. Для остальных пар — ручной ввод.
- **Слова**: добавление/удаление пар, просмотр статуса (выучено/изучается), фильтрация
- **Порог N**: настройка количества правильных ответов, после которого слово считается выученным (per словарь)

## 🛠 Стек

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI + SQLModel + SQLite |
| Frontend | Streamlit + Plotly |
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

## 🧪 Тесты

```bash
uv run pytest
```

## 📏 Линтинг

```bash
uv run ruff check .
```

## 📁 Структура проекта

```
StudyLangHelper/
├── backend/          # FastAPI + SQLModel + SQLite
│   ├── main.py
│   ├── routers/      # dictionaries, words, study, stats
│   └── Dockerfile
├── frontend/         # Streamlit + Plotly
│   ├── app.py
│   ├── pages/        # home, cards, settings
│   └── Dockerfile
├── data/             # SQLite DB (gitignored)
├── tests/
├── docker-compose.yml
└── pyproject.toml
```

## 📄 Лицензия

Распространяется по [лицензии MIT](LICENSE).