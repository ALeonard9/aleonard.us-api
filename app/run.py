"""
This module contains the main application setup and routing.
"""

import asyncio
import json

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import authentication
from .config import get_settings
from .db import db_user, models
from .db.database import engine, get_db
from .db.models_sandbox import DbCountry
from .log.logging_config import logger
from .router.v1 import (
    user,
    router_activity,
    router_countries,
    router_notifications,
    router_search,
    router_movies,
    router_games,
    router_books,
    router_tv,
)
from .schemas.model_schemas import OutResponseBaseModel
from .services.country_data import seed_countries
from .utils.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

settings = get_settings()


# Create FastAPI app
app = FastAPI(
    title='aleonard.us API ' + settings.env,
    description='This is the API for aleonard.us',
    version='0.0.1',
    contact={
        'name': 'Adam',
        'url': 'https://www.aleonard.us',
        'email': 'aleonard9@hotmail.com',
    },
    openapi_tags=[
        {'name': 'intro', 'description': 'Welcome message'},
        {'name': 'authentication', 'description': 'Auth operations'},
        {'name': 'users', 'description': 'User operations'},
        {
            'name': 'Movies',
            'description': 'Movie catalog, search, and per-user tracker',
        },
        {'name': 'TV', 'description': 'TV shows, episodes, and per-user tracker'},
        {'name': 'Games', 'description': 'Video game catalog and per-user tracker'},
        {'name': 'Books', 'description': 'Book catalog and per-user tracker'},
        {'name': 'Countries', 'description': 'Country catalog and per-user tracker'},
        {
            'name': 'Activity',
            'description': 'Cross-domain activity log and "I\'m bored" recommendation',
        },
        {'name': 'Notifications', 'description': 'Per-user notification feed'},
        {'name': 'Search', 'description': 'Cross-domain global search'},
    ],
    openapi_url='/openapi.json',
    servers=[
        {'url': 'http://localhost:8000', 'description': 'Local server'},
    ],
    license_info={
        'name': 'GPL-3.0',
        'url': 'https://www.gnu.org/licenses/gpl-3.0.html',
    },
)

app.include_router(authentication.router, prefix='/v1/auth')
app.include_router(user.router, prefix='/v1/users')
app.include_router(router_countries.router)
app.include_router(router_movies.router)
app.include_router(router_games.router)
app.include_router(router_books.router)
app.include_router(router_tv.router)
app.include_router(router_activity.router)
app.include_router(router_notifications.router)
app.include_router(router_search.router)

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


if settings.env in ('local', 'dev'):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


async def start_server():
    """
    Starts uvicorn server with the FastAPI app.

    Schema ownership: local/CI use SQLite and create tables directly for a
    zero-setup developer loop. Deployed environments (dev/prod) own their schema
    through Alembic migrations (``alembic upgrade head``) so data is never
    dropped on restart.
    """
    if settings.is_local or settings.is_ci:
        models.Base.metadata.create_all(engine)
        logger.info('Created all tables (local/CI)')
    else:
        logger.info('Skipping create_all; schema managed by Alembic migrations')

    try:
        db = next(get_db())
        db_user.create_admin_user(db)
        # The Countries catalog has no search proxy (it's the finite world
        # list) — seed it once so "add a country" has anything to pick from.
        if db.query(DbCountry).count() == 0:
            created = seed_countries(db)
            db.commit()
            logger.info('Seeded countries catalog: %d created', created)
    except SQLAlchemyError as e:
        logger.error('Unexpected error: %s', e)

    if settings.is_local:
        await generate_openapi_json()

    uvicorn.run(
        'app.run:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )


def run():
    """
    Run the FastAPI application.
    """
    asyncio.run(start_server())
