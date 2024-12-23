"""
This module contains the main application setup and routing.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import authentication
from db import models
from db.database import engine
from router.v1 import book, user

# Look for flag against main.py that indicate production
# If the flag is not present, load the local environment variables


# Load environment variables
load_dotenv(dotenv_path='env/local.env')

app = FastAPI(
    title='aleonard.us API',
    description='This is the API for aleonard.us',
    version='0.0.1',
)

app.include_router(authentication.router, prefix='/v1/auth')
app.include_router(user.router, prefix='/v1/users')
app.include_router(book.router, prefix='/v1/books')


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
if os.getenv('API_ENV') == 'local':
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
