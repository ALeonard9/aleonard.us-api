"""
This module contains database operations for user-related actions.
"""

from sqlalchemy.orm import Session
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
    new_user = DbUser(
        display_name=request.display_name,
        email=request.email,
        password=Hash.bcrypt(request.password),
    )
    db.add(new_user)
    db.commit()
    # Refresh to obtain newly created ID
    db.refresh(new_user)
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
    return db.query(DbUser).filter(DbUser.id == user_id).first()


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
    db.delete(user)
    db.commit()
    return user
