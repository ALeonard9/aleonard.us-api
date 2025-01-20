"""
Creates a fixture to provide a database session for testing.
"""

import pytest
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base
from schemas import InUserBase

fake = Faker()


@pytest.fixture(name='test_db_session')
def fixture_test_db_session():
    '''
    Fixture to provide a database session for testing.
    '''

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


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
