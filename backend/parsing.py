"""Парсинг PDF в постраничный текст."""

import io

import pdfplumber


def extract_pdf(file_bytes: bytes) -> list[str]:
    """Вернуть список текстов постранично: один элемент = одна страница.

    Пустые страницы возвращаются как пустая строка.
    """
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages
