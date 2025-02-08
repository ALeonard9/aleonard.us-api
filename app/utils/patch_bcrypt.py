"""
Monkey-patch the bcrypt module to add an __about__ attribute
if it doesn't exist.
"""

import bcrypt


def patch_bcrypt():
    """
    Adds __about__ attribute to bcrypt module if it doesn't exist.
    This suppresses warnings about missing version information.
    """
    if not hasattr(bcrypt, '__about__'):

        class DummyAbout:
            """
            Mock the __about__ attribute of the bcrypt module.
            """

            __version__ = getattr(bcrypt, '__version__', 'unknown')

        bcrypt.__about__ = DummyAbout()
