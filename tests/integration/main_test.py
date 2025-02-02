""""
Integration testing for the main module
"""

import json
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient

from main import app, generate_openapi_json, start_server

client = TestClient(app)


def test_index():
    """
    Test the index endpoint.
    """
    response = client.get('/')
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert isinstance(response_data['data'], list)
    assert len(response_data['data']) == 0
    assert response_data['message'] == "Welcome to Adam's API folks!"


@pytest.mark.asyncio
async def test_generate_openapi_json():
    """
    Test the generate_openapi_json function.
    """
    openapi_schema = {
        'openapi': '3.0.0',
        'info': {'title': 'Test API', 'version': '0.1.0'},
    }

    expected_output = json.dumps(openapi_schema, indent=2) + '\n'

    m = mock_open()
    with patch('main.app.openapi', return_value=openapi_schema):
        with patch('builtins.open', m):
            await generate_openapi_json()
            m.assert_called_once_with('openapi.json', 'w', encoding='utf-8')
            # Combine all write() calls into one string.
            written_calls = m().write.call_args_list
            written_output = ''.join(call.args[0] for call in written_calls)
            assert written_output == expected_output


def test_start_server():
    """
    Test the start_server function.
    """
    with patch('main.models.Base.metadata.drop_all') as mock_drop_all, patch(
        'main.models.Base.metadata.create_all'
    ) as mock_create_all, patch('main.get_db') as mock_get_db, patch(
        'main.db_user.create_admin_user'
    ) as mock_create_admin_user, patch(
        'main.asyncio.run'
    ) as mock_asyncio_run, patch(
        'main.uvicorn.run'
    ) as mock_uvicorn_run, patch(
        'main.os.getenv',
        side_effect=lambda key: 'local' if key == 'API_ENV' else 'info',
    ):

        mock_db_instance = mock_get_db.return_value.__next__.return_value

        start_server()

        mock_drop_all.assert_called_once()
        mock_create_all.assert_called_once()
        mock_get_db.assert_called_once()
        mock_create_admin_user.assert_called_once_with(mock_db_instance)
        mock_asyncio_run.assert_called_once()
        mock_uvicorn_run.assert_called_once_with(
            'main:app',
            host='0.0.0.0',
            port=8000,
            reload=True,
            log_level='info',
        )
