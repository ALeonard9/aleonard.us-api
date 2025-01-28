"""
Tests the user API calls
"""

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from db.database import get_db
from main import app

fake = Faker()
client = TestClient(app)


@pytest.fixture
def override_get_db(test_db_session):
    """
    Override the get_db dependency for each test.
    """

    def _override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides[get_db] = get_db


# def authenticate_user(auth_client: TestClient, email: str, password: str) -> str:
#     """
#     Authenticate a user and return the access token.
#     """
#     response = auth_client.post(
#         "/v1/auth/token/", data={"username": email, "password": password}
#     )
#     print(response.json())

#     assert response.status_code == 200, "Authentication failed"
#     token = response.json().get("access_token")
#     return token


@pytest.mark.usefixtures('override_get_db')
def test_api_create_user(test_user_data_generator):
    """
    Test creating a new user.
    """
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    user_data = {
        'display_name': test_user_data.display_name,
        'email': test_user_data.email,
        'password': test_user_data.password,
    }
    response = client.post('/v1/users/', json=user_data)

    print(response.json())
    assert response.status_code == 201
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User created'
    assert response_data['data'][0]['email'] == test_user_data.email
    assert response_data['data'][0]['display_name'] == test_user_data.display_name


# @pytest.mark.usefixtures("override_get_db")
# def test_api_get_user():
#     """
#     Test getting a user.
#     """
#     user_data = {
#         "display_name": "John Doe",
#         "email": "john.doe@zoho.com",
#         "password": "securepassword",
#     }
#     post_response = client.post("/v1/users/", json=user_data)
#     post_response_data = post_response.json()
#     user_id = post_response_data["data"][0]["id"]

#     token = authenticate_user(client, user_data["email"], user_data["password"])
#     assert token is not None

#     headers = {"Authorization": f"Bearer {token}"}
#     get_response = client.get(f"/v1/users/{user_id}", headers=headers)

#     assert get_response.status_code == 200
#     response_data = get_response.json()
#     assert response_data['success'] is True
#     assert response_data['message'] == "User retrieved"
#     assert response_data["data"][0]["email"] == "john.doe@zoho.com"
#     assert response_data["data"][0]["display_name"] == "John Doe"
#     assert response_data["data"][0]["id"] == user_id
#     assert response_data["data"][0]["created_at"] is not None
#     assert response_data["data"][0]["updated_at"] is not None
