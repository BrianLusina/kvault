from ..types import unicode
from functools import wraps


def encode(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    elif isinstance(s, bytes):
        return s
    return str(s).encode("utf-8")


def decode(s) -> str:
    if isinstance(s, unicode):
        return s
    elif isinstance(s, bytes):
        return s.decode("utf-8")
    return str(s)


def enforce_datatype(data_type, set_missing=True, subtype=None):
    def decorator(meth):
        @wraps(meth)
        def inner(self, key, *args, **kwargs):
            self.check_datatype(data_type, key, set_missing, subtype)
            return meth(self, key, *args, **kwargs)

        return inner

    return decorator
