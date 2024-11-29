"""
This module contains the API routes for user-related operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_user
from schemas import UserBase, UserDisplay

router = APIRouter(
    tags=['users'],
)


# Read all users
@router.get('/', response_model=list[UserDisplay])
def get_all_users(db: Session = Depends(get_db)):
    """
    Retrieve all users from the database.

    Args:
        db (Session): The database session.

    Returns:
        list[UserDisplay]: A list of users.
    """
    return db_user.get_all_users(db)


# Read user
@router.get('/{user_id}', response_model=UserDisplay)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a user by ID from the database.

    Args:
        user_id (str): The ID of the user.
        db (Session): The database session.

    Returns:
        UserDisplay: The user data.
    """
    user = db_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user


# Create user
@router.post('/', response_model=UserDisplay)
def create_user(request: UserBase, db: Session = Depends(get_db)):
    """
    Create a new user in the database.

    Args:
        request (UserBase): The user data.
        db (Session): The database session.

    Returns:
        UserDisplay: The newly created user data.
    """
    return db_user.create_user(db, request)


# Update user
@router.put('/{user_id}', response_model=UserDisplay)
def update_user(user_id: str, request: UserBase, db: Session = Depends(get_db)):
    """
    Update a user's information in the database.

    Args:
        user_id (str): The ID of the user.
        request (UserBase): The updated user data.
        db (Session): The database session.

    Returns:
        UserDisplay: The updated user data.
    """
    user = db_user.update_user(db, user_id, request)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user


# Delete user
@router.delete('/{user_id}', response_model=UserDisplay)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Delete a user by ID from the database.

    Args:
        user_id (str): The ID of the user.
        db (Session): The database session.

    Returns:
        UserDisplay: The deleted user data.
    """
    user = db_user.delete_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user
