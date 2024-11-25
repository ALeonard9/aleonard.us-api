"""
This module contains the main application setup and routing.
"""

from fastapi import FastAPI
from router.v1 import book

app = FastAPI(
    title="aleonard.us API",
    description="This is the API for aleonard.us",
    version="0.0.1",
)
app.include_router(book.router, prefix="/v1/books")


@app.get("/")
def index():
    """
    Index endpoint that returns a welcome message.

    Returns:
        str: Welcome message.
    """
    return "Welcome to Adam's API!"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
