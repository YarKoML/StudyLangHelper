# StudyLangHelper

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58+-FF4B4B?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

📖 [Документация на русском](README.md)

A foreign language learning app: word flashcards, statistics, and an activity calendar.

## Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start (Docker)](#-quick-start-docker)
- [Local Development](#%EF%B8%8F-local-development)
- [Database](#-database)
- [Testing](#-testing)
- [Linting](#-linting)
- [Project Structure](#-project-structure)
- [License](#-license)

## ✨ Features

### 🏠 Home
- Activity calendar (GitHub-style heatmap for the current year)
- Statistics: total words, learned, learning, learned %, day streak

### 🃏 Cards
- Modes: review learned words / learn new words
- Direction: word → translation / translation → word
- Configurable number of cards
- 4 answer options with the correct one highlighted on mistake
- Final results as percentages

### ⚙️ Settings
- **Dictionaries**: create dictionaries by language pair (native ↔ study). The EN↔RU pair is auto-seeded with 10 popular words. Other pairs require manual input.
- **Words**: add/delete pairs, view status (learned/learning), filter
- **Threshold N**: configure how many correct answers mark a word as learned (per dictionary)

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + SQLModel + SQLite |
| Frontend | Streamlit + Plotly |
| Runtime | Python 3.12 |
| Package manager | uv |
| Containers | Docker Compose |

## 🐳 Quick Start (Docker)

```bash
docker compose up -d --build
```

- Backend: http://localhost:8000 (docs: http://localhost:8000/docs)
- Frontend: http://localhost:8501

The SQLite database is stored in `./data/studylanghelper.db` (bind mount) and persists across restarts. The `data/` directory is created automatically and is gitignored.

Stop:

```bash
docker compose down          # stop, data is preserved
```

To reset the database, remove the `data/` directory manually:

```bash
docker compose down
Remove-Item -Recurse -Force data   # Windows PowerShell
# or: rm -rf data                  # Linux/macOS
```

## ⚙️ Local Development

Dependencies are split into optional-groups `backend` and `frontend`. For local development install both:

```bash
uv sync --extra backend --extra frontend
# or equivalently:
uv sync --group local
```

> ⚠️ **Note**: `uv sync` without arguments installs only base dependencies (empty set).
> Always specify `--extra backend --extra frontend` or `--group local` for full functionality.

### Run (two terminals)

```bash
# 1. Backend
uv run uvicorn backend.main:app --reload --port 8000

# 2. Frontend
uv run streamlit run frontend/app.py
```

## 🗄 Database

- **Location**: `data/studylanghelper.db` (auto-created on first run)
- **Docker**: bind-mounted at `./data:/app/data`
- **Gitignored**: yes (`.gitignore`)
- **Reset**: delete the `data/` directory

## 🧪 Testing

```bash
uv run pytest
```

## 📏 Linting

```bash
uv run ruff check .
```

## 📁 Project Structure

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

## 📄 License

Distributed under the [MIT License](LICENSE).