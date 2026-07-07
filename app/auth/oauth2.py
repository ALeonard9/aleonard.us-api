"""
This module creates access tokens and verifys tokens.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import db_user
from app.db.database import get_db
from app.log.logging_config import logger

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/auth/token')


def _resolve_secret_key() -> str:
    """
    Resolve the JWT signing secret.

    A fixed ``JWT_SECRET_KEY`` is required in deployed environments (dev/prod)
    so tokens survive restarts and are shared across workers. Local/CI fall
    back to a random per-process key with a warning.
    """
    # openssl rand -hex 32 to generate a new secret key
    if settings.jwt_secret_key:
        return settings.jwt_secret_key
    if settings.env in ('dev', 'prod', 'gs'):
        raise RuntimeError(
            f'JWT_SECRET_KEY must be set in the {settings.env} environment'
        )
    logger.warning(
        'JWT_SECRET_KEY not set; using a randomly generated key for this '
        'process. Tokens will not persist across restarts or be shared '
        'across workers.'
    )
    return secrets.token_hex(32)


SECRET_KEY = _resolve_secret_key()
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


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


def require_admin(current_user: list = Depends(get_current_user)) -> list:
    """
    Dependency that allows only admin users through.

    ``get_current_user`` returns a one-element list (``[DbUser]``); reuse it so
    the same object is available to the route.
    """
    if not current_user or current_user[0].user_group != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin privileges required',
        )
    return current_user
