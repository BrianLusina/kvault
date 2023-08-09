"""
Types
"""
from collections import namedtuple

# pylint: disable-next=invalid-name
unicode = str
basestring = (bytes, str)

Value = namedtuple("Value", ("data_type", "value"))

KV = 0
HASH = 1
QUEUE = 2
SET = 3
