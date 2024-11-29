"""
This module provides hashing utilities for passwords.
"""

from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=['bcrypt'], deprecated='auto')


class Hash:
    """
    A class that provides methods for hashing and verifying passwords.
    """

    @staticmethod
    def bcrypt(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password (str): The plain password to hash.

        Returns:
            str: The hashed password.
        """
        return pwd_cxt.hash(password)

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        """
        Verify a hashed password against a plain password.

        Args:
            hashed_password (str): The hashed password.
            plain_password (str): The plain password to verify.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
        return pwd_cxt.verify(plain_password, hashed_password)
