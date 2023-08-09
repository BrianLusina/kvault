"""
Utility functions
"""
from functools import wraps
from ..types import unicode


def encode(characters, encoding: str = "utf-8"):
    """
    Encodes a string with the set encoding defaulted to utf-8
    :param characters: string to encode
    :param encoding: Encoding to set
    :return:
    """
    if isinstance(characters, unicode):
        return characters.encode(encoding=encoding)
    if isinstance(characters, bytes):
        return characters
    return str(characters).encode(encoding=encoding)


def decode(characters) -> str:
    """
    Decodes a string and returns the correct type
    :param characters: String.
    :return: string
    """
    if isinstance(characters, unicode):
        return characters
    if isinstance(characters, bytes):
        return characters.decode("utf-8")
    return str(characters)


def enforce_datatype(data_type, set_missing=True, subtype=None):
    """
    decorator that enforces a data type on a function.
    :param data_type: Data type to enforce
    :param set_missing: Whether to set a value if the key is missing
    :param subtype: subtype to check. This will be for the value
    :return: wrapped function
    """

    def decorator(meth):
        @wraps(meth)
        def inner(self, key, *args, **kwargs):
            self.check_datatype(data_type, key, set_missing, subtype)
            return meth(self, key, *args, **kwargs)

        return inner

    return decorator
