"""
Creates a fixture to provide a database session for testing.
"""

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.database import Base, get_db
from main import app
from schemas import InUserBase

fake = Faker()


# Create a new database session for testing
@pytest.fixture(scope='session', name='test_db_engine')
def db_engine():
    """
    Fixture to provide a database engine for testing.
    """

    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope='function', name='test_db_session')
def db_session(test_db_engine):
    """
    Fixture to provide a database session for testing.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_local()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# Override the get_db dependency to use the test database
@pytest.fixture(scope='function')
def client(test_db_session: Session):
    """
    Fixture to provide a FastAPI TestClient.
    """

    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(name='test_user_data_generator')
def fixture_test_user_data_generator():
    '''
    Fixture for user data generator.
    '''

    def _generate_user_data(num_users=1):
        user_data = []
        for _ in range(num_users):
            user_data.append(
                InUserBase(
                    display_name=fake.name(),
                    email=f'{fake.first_name()}@zoho.com',
                    password=fake.password(),
                )
            )
        return user_data

    return _generate_user_data
