"""
This module contains the API routes for book-related operations.
"""

from fastapi import APIRouter


router = APIRouter(
    tags=["books"],
)


@router.get(
    "/",
    summary="Get all books",
    description="Get all books from the database",
    response_description="List of books",
)
def get_all_books():
    """
    Retrieve all books from the database.

    Returns:
        dict: A dictionary containing a list of all books.
    """
    return {"data": "all books"}
