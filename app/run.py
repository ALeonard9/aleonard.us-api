"""
This module contains the main application setup and routing.
"""

import asyncio
import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import authentication
from .db import db_user, models
from .db.database import engine, get_db
from .log.logging_config import logger
from .router.v1 import book, user
from .schemas.model_schemas import OutResponseBaseModel
from .utils.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .utils.patch_bcrypt import patch_bcrypt

# Suppresses warning about bcrypt version
patch_bcrypt()


# Create FastAPI app
app = FastAPI(
    title='aleonard.us API ' + os.getenv('ENV', 'local'),
    description='This is the API for aleonard.us',
    version='0.0.1',
    contact={
        'name': 'Adam',
        'url': 'https://www.aleonard.us',
        'email': 'aleonard9@hotmail.com',
    },
    openapi_tags=[
        {'name': 'users', 'description': 'User operations'},
        {'name': 'authentication', 'description': 'Auth operations'},
        {'name': 'books', 'description': 'Book operations'},
        {'name': 'intro', 'description': 'Welcome message'},
    ],
    openapi_url='/openapi.json',
    servers=[
        {'url': 'http://localhost:8000', 'description': 'Local server'},
    ],
    license_info={
        'name': 'Apache 2.0',
        'url': 'https://www.apache.org/licenses/LICENSE-2.0.html',
    },
)

app.include_router(authentication.router, prefix='/v1/auth')
app.include_router(user.router, prefix='/v1/users')
app.include_router(book.router, prefix='/v1/books')

# Serve static files
app.mount('/static', StaticFiles(directory='app/static'), name='static')

# Register custom exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get('/', tags=['intro'], response_model=OutResponseBaseModel)
def index():
    """
    Index endpoint that returns a welcome message.
    """
    return OutResponseBaseModel(message="Welcome to Adam's API folks!")


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    """
    Endpoint to serve favicon.
    """
    return FileResponse('app/static/favicon.ico')


async def generate_openapi_json():
    """
    Generate the OpenAPI schema and write it to a file upon startup.
    """
    openapi_schema = app.openapi()
    with open('openapi.json', 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2)
        f.write('\n')
    logger.info('OpenAPI schema generated and written to openapi.json')


if os.getenv('ENV') == 'local':
    origins = ['http://localhost:3000']
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


async def start_server():
    """
    Starts uvicorn server with the FastAPI app.
    """
    if os.getenv('ENV') in ['local', 'dev']:
        models.Base.metadata.drop_all(bind=engine)
        logger.debug('Dropped all tables')

    models.Base.metadata.create_all(engine)
    logger.info('Created all tables')

    try:
        db = next(get_db())
        db_user.create_admin_user(db)
    except SQLAlchemyError as e:
        logger.error('Unexpected error: %s', e)

    if os.getenv('ENV') == 'local':
        await generate_openapi_json()

    uvicorn.run(
        'app.run:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level=os.getenv('LOG_LEVEL', 'INFO').lower(),
    )


def run():
    """
    Run the FastAPI application.
    """
    asyncio.run(start_server())
