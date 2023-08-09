"""
Mixin classes that provide extra functionality to classes
"""
from typing import Dict, Any
import time
from collections import deque
from ..exceptions import CommandError
from ..types import Value, QUEUE, HASH, SET, KV


# pylint: disable-next=too-few-public-methods
class MetaUtils:
    """
    Class with helper properties and utilities
    """

    @property
    def name(self):
        """Returns the class name"""
        return self.__class__.__name__


class Guards:
    """
    Contains validity checks for the data types and expiry time of commands
    """

    def __init__(self, kv_store: Dict, expiry_map: Dict[Any, float]):
        self._kv = kv_store
        self._expiry_map = expiry_map

    def check_expired(self, key, timestamp=None) -> bool:
        """
        Checks if a key has expired
        :param key: Key
        :param timestamp: Timestamp, defaulted to None and will use current time
        :return: boolean
        """
        _timestamp = timestamp or time.time()
        return key in self._expiry_map and _timestamp > self._expiry_map[key]

    def check_datatype(self, data_type, key, set_missing=True, subtype=None):
        """
        Checks the data type of the supplied key
        :param data_type: Data type to check
        :param key: Key to check
        :param set_missing: Whether to set the value if the key is missing
        :param subtype: subtype to check
        :return: None
        :raises CommandError if the operation is against a wrong key type of wrong value
        """
        if key in self._kv and self.check_expired(key):
            del self._kv[key]

        if key in self._kv:
            value = self._kv[key]
            if value.data_type != data_type:
                raise CommandError(
                    f"Operation against wrong key type. Key type {value.data_type}. data type: {data_type}"
                )
            if subtype is not None and not isinstance(value.value, subtype):
                raise CommandError(
                    f"Operation against wrong value type. Value: {value.value}. Subtype: {subtype}"
                )
        elif set_missing:
            value = None
            if data_type == HASH:
                value = {}
            elif data_type == QUEUE:
                value = deque()
            elif data_type == SET:
                value = set()
            elif data_type == KV:
                value = ""
            self._kv[key] = Value(data_type, value)
