# pylint: disable=missing-function-docstring, useless-return
"""
This module contains the API routes for Books.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbBook, DbUserBook
from app.auth.oauth2 import get_current_user
from app.schemas.schemas_sandbox import (
    BookCreate,
    BookResponse,
    BookUpdate,
    UserBookCreate,
    UserBookResponse,
    UserBookUpdate,
)

router = APIRouter(prefix='/v1', tags=['Books'])


# Global Entity Endpoints
@router.get('/books', response_model=List[BookResponse])
def get_all_books(db: Session = Depends(get_db)):
    return db.query(DbBook).all()


@router.post('/books', response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(request: BookCreate, db: Session = Depends(get_db)):
    new_book = DbBook(**request.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@router.put('/books/{book_id}', response_model=BookResponse)
def update_book(book_id: str, request: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(DbBook).filter(DbBook.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not found'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)
    return book


@router.delete('/books/{book_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str, db: Session = Depends(get_db)):
    book = db.query(DbBook).filter(DbBook.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not found'
        )
    db.delete(book)
    db.commit()
    return None


# User Tracker Endpoints
@router.get('/users/me/books', response_model=List[UserBookResponse])
def get_user_books(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return db.query(DbUserBook).filter(DbUserBook.user_id == current_user[0].pk).all()


@router.post(
    '/users/me/books/{book_id}',
    response_model=UserBookResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_book(
    book_id: str,
    request: UserBookCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    book = db.query(DbBook).filter(DbBook.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not found'
        )

    existing_tracker = (
        db.query(DbUserBook)
        .filter(DbUserBook.user_id == current_user[0].pk, DbUserBook.book_id == book.pk)
        .first()
    )
    if existing_tracker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Book already marked'
        )

    new_tracker = DbUserBook(
        user_id=current_user[0].pk, book_id=book.pk, **request.model_dump()
    )
    db.add(new_tracker)
    db.commit()
    db.refresh(new_tracker)
    return new_tracker


@router.put('/users/me/books/{book_id}', response_model=UserBookResponse)
def update_user_book(
    book_id: str,
    request: UserBookUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    book = db.query(DbBook).filter(DbBook.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not found'
        )

    tracker = (
        db.query(DbUserBook)
        .filter(DbUserBook.user_id == current_user[0].pk, DbUserBook.book_id == book.pk)
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not marked'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tracker, key, value)

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete('/users/me/books/{book_id}', status_code=status.HTTP_204_NO_CONTENT)
def unmark_book(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    book = db.query(DbBook).filter(DbBook.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not found'
        )

    tracker = (
        db.query(DbUserBook)
        .filter(DbUserBook.user_id == current_user[0].pk, DbUserBook.book_id == book.pk)
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Book not marked'
        )

    db.delete(tracker)
    db.commit()
    return None
