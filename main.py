"""
This module contains the main application setup and routing.
"""

import asyncio
import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import authentication
from db import db_user, models
from db.database import engine, get_db
from log.logging_config import logger
from router.v1 import book, user

# Create FastAPI app
app = FastAPI(
    title='aleonard.us API ' + os.getenv('API_ENV', 'local'),
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
    openapi_url='/openapi.json',  # Customize OpenAPI path
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


@app.get('/', tags=['intro'])
def index():
    """
    Index endpoint that returns a welcome message.

    Returns:
        str: Welcome message.
    """
    return "Welcome to Adam's API folks!"


async def generate_openapi_json():
    """
    Generate the OpenAPI schema and write it to a file upon startup.
    """
    openapi_schema = app.openapi()
    with open('openapi.json', 'w', encoding='utf-8') as f:

        json.dump(openapi_schema, f, indent=2)
        # Add a newline to the end of the file
        f.write('\n')
    logger.info('OpenAPI schema generated and written to openapi.json')


if os.getenv('API_ENV') == 'local':
    # CORS
    origins = ['http://localhost:3000']

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


def start_server():
    """
    Starts uvicorn server with the FastAPI app.
    """
    if os.getenv('API_ENV') == 'local':
        # Drop the database tables
        models.Base.metadata.drop_all(bind=engine)
        logger.debug('Dropped all tables')

    # Create or update tables
    models.Base.metadata.create_all(engine)
    logger.info('Created all tables')

    # Create the admin user
    db = next(get_db())
    db_user.create_admin_user(db)

    log_level_var = os.getenv('LOG_LEVEL').lower()

    # Generate OpenAPI schema
    asyncio.run(generate_openapi_json())

    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level=log_level_var,
    )


if __name__ == '__main__':
    start_server()
