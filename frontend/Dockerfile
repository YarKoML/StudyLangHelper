FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra frontend --no-install-project

COPY frontend/ ./frontend/

RUN uv sync --frozen --no-dev --extra frontend

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_BASE_URL=http://backend:8000

EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "frontend/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]