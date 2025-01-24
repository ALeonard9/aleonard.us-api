"""
Test the custom exception handlers.
"""

import json

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from main import app
from utils.exceptions import generic_exception_handler, http_exception_handler

client = TestClient(app)


@pytest.mark.asyncio
async def test_http_exception_handler():
    """
    Test the custom HTTPException handler.
    """
    request = Request(scope={'type': 'http'})
    exc = HTTPException(status_code=404, detail='Not Found')
    response = await http_exception_handler(request, exc)
    response_body = json.loads(response.body.decode('utf-8'))
    assert response.status_code == 404
    assert response_body['success'] is False
    assert response_body['message'] == 'Not Found'
    assert response_body['data'] == []


@pytest.mark.asyncio
async def test_generic_exception_handler():
    """
    Test the custom generic exception handler.
    """
    request = Request(scope={'type': 'http'})
    exc = Exception('Test exception')
    response = await generic_exception_handler(request, exc)
    response_body = json.loads(response.body.decode('utf-8'))
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    assert response_body['success'] is False
    assert response_body['message'] == 'Test exception'
    assert response_body['data'] == []
