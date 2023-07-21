from collections import namedtuple

unicode = str
basestring = (bytes, str)

Value = namedtuple("Value", ("data_type", "value"))
