"""
This module contains the main application setup and routing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.v1 import book, user
from auth import authentication
from db import models
from db.database import engine

app = FastAPI(
    title='aleonard.us API',
    description='This is the API for aleonard.us',
    version='0.0.1',
)
app.include_router(book.router, prefix='/v1/books')
app.include_router(user.router, prefix='/v1/users')
app.include_router(authentication.router, prefix='/v1/auth')


@app.get('/')
def index():
    """
    Index endpoint that returns a welcome message.

    Returns:
        str: Welcome message.
    """
    return "Welcome to Adam's API folks!"


# Create the database tables
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(engine)

# CORS
# TOdDO move to .env and make dev only
origins = ['http://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
