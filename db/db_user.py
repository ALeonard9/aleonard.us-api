"""
This module contains database operations for user-related actions.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from schemas import UserBase
from db.hash import Hash
from db.models import DbUser


def create_user(db: Session, request: UserBase):
    """
    Create a new user in the database.

    Args:
        db (Session): The database session.
        request (UserBase): The user data.

    Returns:
        DbUser: The newly created user.
    """
    existing_user = db.query(DbUser).filter(
        DbUser.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered',
        )
    new_user = DbUser(
        display_name=request.display_name,
        email=request.email,
        password=Hash.bcrypt(request.password),
    )
    try:
        db.add(new_user)
        db.commit()
        # Refresh to obtain newly created ID
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Error creating user',
        ) from exc
    return new_user


def get_all_users(db: Session):
    """
    Retrieve all users from the database.

    Args:
        db (Session): The database session.

    Returns:
        list[DbUser]: A list of all users.
    """
    return db.query(DbUser).all()


def get_user(db: Session, user_id: str):
    """
    Retrieve a user by ID from the database.

    Args:
        db (Session): The database session.
        user_id (str): The ID of the user.

    Returns:
        DbUser: The user data.
    """
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return user.__dict__


def update_user(db: Session, user_id: str, request: UserBase):
    """
    Update a user's information in the database.

    Args:
        db (Session): The database session.
        user_id (str): The ID of the user.
        request (UserBase): The updated user data.

    Returns:
        DbUser: The updated user data.
    """
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    user.display_name = request.display_name
    user.email = request.email
    user.password = Hash.bcrypt(request.password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str):
    """
    Delete a user by ID from the database.

    Args:
        db (Session): The database session.
        user_id (str): The ID of the user.

    Returns:
        DbUser: The deleted user data.
    """
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    db.delete(user)
    db.commit()
    return user.__dict__
