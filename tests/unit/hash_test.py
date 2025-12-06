'''
This file contains unit tests for the Hash class in db/hash.py.
'''

from faker import Faker

from app.db.hash import Hash

fake = Faker()


def test_bcrypt():
    '''
    Tests if the bcrypt method hashes a plain password correctly.
    '''
    plain_password = fake.password(length=20)
    hashed_password = Hash.bcrypt(plain_password)
    assert (
        hashed_password != plain_password
    ), 'Hashed password should not match the plain password'
    assert isinstance(hashed_password, str), 'Hash.bcrypt should return a string'


def test_verify():
    '''
    Tests if the verify method correctly identifies matching and non-matching plain passwords.
    '''
    plain_password = fake.password(length=20)
    hashed_password = Hash.bcrypt(plain_password)
    assert Hash.verify(
        hashed_password, plain_password
    ), 'Verify should pass with the correct plain password'
    assert not Hash.verify(
        hashed_password, 'wrongPassword'
    ), 'Verify should fail with an incorrect plain password'
