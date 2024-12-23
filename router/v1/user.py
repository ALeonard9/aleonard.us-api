"""
This module contains the API routes for user-related operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_user
from schemas import UserBase, UserDisplay
from auth.oauth2 import get_current_user

router = APIRouter(
    tags=['users'],
)


# Read all users
@router.get('/', response_model=list[UserDisplay])
def get_all_users(
    db: Session = Depends(get_db), current_user: UserBase = Depends(get_current_user)
):
    """
    Retrieve all users from the database. Must be an admin to view all users.

    Args:
        db (Session): The database session.

    Returns:
        list[UserDisplay]: A list of users.
    """
    if current_user['user_group'] == 'admin':
        users = db_user.get_all_users(db)
        if not users:
            raise HTTPException(status_code=404, detail='Users not found')
        return users

    raise HTTPException(
        status_code=403,
        detail='User does not have permission to view all users.',
    )


# Read user
@router.get('/{uuid}', response_model=UserDisplay)
def get_user(
    uuid: str,
    db: Session = Depends(get_db),
    current_user: UserBase = Depends(get_current_user),
):
    """
    Retrieve a user by ID from the database.
    Admins can view all users, while users can only view their own account.

    Args:
        uuid (str): The ID of the user.
        db (Session): The database session.

    Returns:
        UserDisplay: The user data.
    """
    if current_user['user_group'] == 'admin':
        user = db_user.get_user(db, uuid)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return user

    if current_user['user_group'] == 'user':
        if current_user['id'] == uuid:
            user = db_user.get_user(db, uuid)
            if not user:
                raise HTTPException(status_code=404, detail='User not found')
            return user
        raise HTTPException(
            status_code=403,
            detail='User can only view their own account.',
        )

    raise HTTPException(
        status_code=403,
        detail='User does not have permission to view users.',
    )


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
@router.put('/{uuid}', response_model=UserDisplay)
def update_user(
    uuid: str,
    request: UserBase,
    db: Session = Depends(get_db),
    current_user: UserBase = Depends(get_current_user),
):
    """
    Update a user's information in the database.
    Admins can update any user, while users can only update their own account.

    Args:
        uuid (str): The ID of the user.
        request (UserBase): The updated user data.
        db (Session): The database session.

    Returns:
        UserDisplay: The updated user data.
    """
    if current_user['user_group'] == 'admin':
        user = db_user.update_user(db, uuid, request)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return user

    if current_user['user_group'] == 'user':
        if current_user['id'] == uuid:
            user = db_user.update_user(db, uuid, request)
            if not user:
                raise HTTPException(status_code=404, detail='User not found')
            return user
        raise HTTPException(
            status_code=403,
            detail='User can only update their own account.',
        )

    raise HTTPException(
        status_code=403,
        detail='User does not have permission to update users.',
    )


# Delete user
@router.delete('/{uuid}', response_model=UserDisplay)
def delete_user(
    uuid: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a user by ID from the database.
    Admins can delete any user, while users can only delete their own account.

    Args:
        uuid (str): The ID of the user.
        db (Session): The database session.
        current_user (dict): The current authenticated user.

    Returns:
        UserDisplay: The deleted user data.
    """
    # Check if current user is admin
    if current_user['user_group'] == 'admin':
        user = db_user.delete_user(db, uuid)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return user

    if current_user['user_group'] == 'user':
        if current_user['id'] == uuid:
            user = db_user.delete_user(db, uuid)
            if not user:
                raise HTTPException(status_code=404, detail='User not found')
            return user
        raise HTTPException(
            status_code=403,
            detail='User can only delete their own account.',
        )

    raise HTTPException(
        status_code=403,
        detail='User does not have permission to delete users.',
    )
