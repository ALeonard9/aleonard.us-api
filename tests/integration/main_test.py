""""
Integration testing for the main module
"""

from fastapi.testclient import TestClient

from main import app

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
