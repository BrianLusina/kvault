from typing import Union, Any, Optional, List, Dict
from collections import deque
from .commands import BaseCommand, HASH, QUEUE, SET, KV
from ..exceptions import CommandError
from ..types import Value
from ..utils import enforce_datatype


class KvCommands(BaseCommand):
    def unexpire(self, key):
        self._expiry_map.pop(key, None)

    def _kv_incr(self, key, n) -> Union[Value, Any]:
        if key in self._kv:
            value = self._kv[key].value + n
        else:
            value = n
        self._kv[key] = Value(KV, value)
        return value

    def kv_append(self, key, value):
        if key not in self._kv:
            self.kv_set(key=key, value=value)
        else:
            kv_val = self._kv[key]
            if kv_val.data_type == QUEUE:
                if isinstance(value, list):
                    kv_val.value.extend(value)
                else:
                    kv_val.value.append(value)
            else:
                try:
                    kv_val = Value(kv_val.data_type, kv_val.value + value)
                except:
                    raise CommandError('Incompatible data-types')
        return self._kv[key].value

    def kv_set(self, key, value) -> int:
        if isinstance(value, dict):
            data_type = HASH
        elif isinstance(value, list):
            data_type = QUEUE
            value = deque(value)
        elif isinstance(value, set):
            data_type = SET
        else:
            data_type = KV
        self.unexpire(key)
        self._kv[key] = Value(data_type, value)
        return 1

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_decr(self, key):
        return self._kv_incr(key=key, n=-1)

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_decrby(self, key, n: Union[float, int]):
        return self._kv_incr(key=key, n=-1 * n)

    def kv_delete(self, key) -> int:
        if key in self._kv:
            del self._kv[key]
            return 1
        return 0

    def kv_exists(self, key) -> int:
        return 1 if key in self._kv and not self.check_expired(key) else 0

    def kv_get(self, key) -> Optional[Value]:
        if key in self._kv and not self.check_expired(key):
            return self._kv[key].value

    def kv_getset(self, key, value) -> Optional[Value]:
        original_value = None
        if key in self._kv and not self.check_expired(key):
            original_value = self._kv[key].value

        self._kv[key] = Value(KV, value)
        return original_value

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_incr(self, key):
        return self._kv_incr(key, 1)

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_incrby(self, key, n):
        return self._kv_incr(key, n)

    def kv_mdelete(self, *keys):
        n = 0
        for key in keys:
            try:
                del self._kv[key]
            except KeyError:
                pass
            else:
                n += 1
        return n

    def kv_mget(self, *keys) -> List[Optional[Value]]:
        accum = []
        for key in keys:
            if key in self._kv and not self.check_expired(key):
                accum.append(self._kv[key].value)
            else:
                accum.append(None)
        return accum

    def kv_mpop(self, *keys) -> List[Optional[Value]]:
        accum = []
        for key in keys:
            if key in self._kv and not self.check_expired(key):
                accum.append(self._kv.pop(key).value)
            else:
                accum.append(None)
        return accum

    def kv_mset(self, __data: Optional[Dict] = None, **kwargs) -> int:
        n = 0
        data = {}
        if __data is not None:
            data.update(__data)
        if kwargs is not None:
            data.update(kwargs)

        for key in data:
            self.unexpire(key)
            self._kv[key] = Value(KV, data[key])
            n += 1
        return n

    def kv_msetex(self, data, expires):
        self.kv_mset(data)
        for key in data:
            self.expire(key, expires)

    def kv_pop(self, key):
        if key in self._kv and not self.check_expired(key):
            return self._kv.pop(key).value

    def kv_setnx(self, key, value) -> int:
        if key in self._kv and not self.check_expired(key):
            return 0
        else:
            self.unexpire(key)
            self._kv[key] = Value(KV, value)
            return 1

    def kv_setex(self, key, value, expires) -> int:
        self.kv_set(key, value)
        self.expire(key, expires)
        return 1

    def kv_len(self) -> int:
        return len(self._kv)

    def kv_flush(self) -> int:
        kvlen = self.kv_len()
        self._kv.clear()
        self._expiry = []
        self._expiry_map = {}
        return kvlen
