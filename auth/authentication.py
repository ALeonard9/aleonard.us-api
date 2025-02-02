"""
This module creates tokens for users.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session

from auth import oauth2
from db import models
from db.database import get_db
from db.hash import Hash

router = APIRouter(tags=['authentication'])


@router.post('/token')
def get_token(
    request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Retrieves a JWT token if username (email) and password match

    Args:
        username: The email of the user
        password: The password of the user

    Returns:
        Access token
    """
    user = (
        # OAuth2PasswordRequestForm requires username instead of email
        db.query(models.DbUser)
        .filter(models.DbUser.email == request.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Invalid credentials'
        )
    if not Hash.verify(user.password, request.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Invalid credentials'
        )

    access_token = oauth2.create_access_token(data={'sub': user.id})

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user_id': user.id,
        'user_group': user.user_group,
        'email': user.email,
    }
