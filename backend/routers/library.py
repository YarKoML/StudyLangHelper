"""Роутер библиотеки книг (PDF)."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlmodel import Session, select

from backend.deps import get_session
from backend.models import Book, User
from backend.parsing import extract_pdf
from backend.schemas import BookPageRead, BookRead, BookUpdatePosition
from backend.security import get_current_user

router = APIRouter(prefix="/library", tags=["library"])

ALLOWED_EXTENSIONS = {".pdf"}


def _to_read(b: Book) -> BookRead:
    return BookRead(
        id=b.id,
        title=b.title,
        source_filename=b.source_filename,
        total_pages=b.total_pages,
        last_page=b.last_page,
        created_at=b.created_at,
    )


def _parse_content(content: str) -> list[str]:
    try:
        pages = json.loads(content)
        return pages if isinstance(pages, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


@router.post("/books", response_model=BookRead, status_code=201)
async def upload_book(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    filename = file.filename or "unknown.pdf"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Only .pdf is supported.")

    existing = session.exec(
        select(Book).where(
            Book.user_id == current_user.id,
            Book.source_filename == filename,
        )
    ).first()
    if existing:
        raise HTTPException(409, "Book with this filename already exists")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "Empty file")

    try:
        pages = extract_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse PDF: {e}") from e

    if not pages:
        raise HTTPException(422, "PDF contains no extractable text")

    title = Path(filename).stem
    book = Book(
        user_id=current_user.id,
        title=title,
        source_filename=filename,
        total_pages=len(pages),
        content=json.dumps(pages, ensure_ascii=False),
        last_page=0,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return _to_read(book)


@router.get("/books", response_model=list[BookRead])
def list_books(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    books = session.exec(
        select(Book).where(Book.user_id == current_user.id).order_by(Book.created_at)
    ).all()
    return [_to_read(b) for b in books]


@router.get("/books/{book_id}", response_model=BookPageRead)
def get_book_page(
    book_id: int,
    session: Session = Depends(get_session),
    page: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    b = session.get(Book, book_id)
    if not b or b.user_id != current_user.id:
        raise HTTPException(404, "Book not found")

    pages = _parse_content(b.content)
    if page >= len(pages):
        raise HTTPException(400, f"Page {page} out of range (total {len(pages)})")

    page_text = pages[page]
    return BookPageRead(
        id=b.id,
        title=b.title,
        total_pages=b.total_pages,
        current_page=page,
        page_text=page_text,
    )


@router.patch("/books/{book_id}", response_model=BookRead)
def update_book_position(
    book_id: int,
    payload: BookUpdatePosition,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    b = session.get(Book, book_id)
    if not b or b.user_id != current_user.id:
        raise HTTPException(404, "Book not found")
    b.last_page = payload.last_page
    session.add(b)
    session.commit()
    session.refresh(b)
    return _to_read(b)


@router.delete("/books/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    b = session.get(Book, book_id)
    if not b or b.user_id != current_user.id:
        raise HTTPException(404, "Book not found")
    session.delete(b)
    session.commit()
