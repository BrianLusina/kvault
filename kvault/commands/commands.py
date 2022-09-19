from collections import deque
from typing import Dict, Optional
import time
from ..types import Value
from ..exceptions import CommandError

KV = 0
HASH = 1
QUEUE = 2
SET = 3


class BaseCommand(object):
    def __init__(self, kv: Optional[Dict[bytes, Value]], expiry_map: Dict):
        self._kv: Dict[bytes, Value] = kv
        self._expiry_map = expiry_map

    def check_expired(self, key, ts=None):
        ts = ts or time.time()
        return key in self._expiry_map and ts > self._expiry_map[key]

    def check_datatype(self, data_type, key, set_missing=True, subtype=None):
        if key in self._kv and self.check_expired(key):
            del self._kv[key]

        if key in self._kv:
            value = self._kv[key]
            if value.data_type != data_type:
                raise CommandError('Operation against wrong key type.')
            if subtype is not None and not isinstance(value.value, subtype):
                raise CommandError('Operation against wrong value type.')
        elif set_missing:
            value = None
            if data_type == HASH:
                value = {}
            elif data_type == QUEUE:
                value = deque()
            elif data_type == SET:
                value = set()
            elif data_type == KV:
                value = ''
            self._kv[key] = Value(data_type, value)
