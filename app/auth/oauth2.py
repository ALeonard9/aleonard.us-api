"""
This module creates access tokens and verifys tokens.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import db_user
from app.db.database import get_db
from app.log.logging_config import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/auth/token')

# openssl rand -hex 32 to generate new secret key
# Get secret key from environment with a default for tests
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'test_secret_key')
if SECRET_KEY == 'test_secret_key':
    logger.warning('Using default test secret key for JWT.')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    This function creates an access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    This function verifies the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uuid: str = payload.get('sub')
        if uuid is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError as exc:
        raise credentials_exception from exc
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc
    user = db_user.get_user(db, uuid)
    if user is None:
        raise credentials_exception
    return user
