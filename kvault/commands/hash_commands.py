from typing import Any, List, Dict
from .commands import BaseCommand, HASH
from ..utils import enforce_datatype
from ..types import Value


class HashCommands(BaseCommand):
    @enforce_datatype(HASH)
    def hdel(self, key, field) -> int:
        value = self._kv[key].value
        if field in value:
            del value[field]
            return 1
        return 0

    @enforce_datatype(HASH)
    def hexists(self, key, field) -> int:
        value = self._kv[key].value
        return 1 if field in value else 0

    @enforce_datatype(HASH)
    def hget(self, key, field) -> Any:
        return self._kv[key].value.get(field)

    @enforce_datatype(HASH)
    def hgetall(self, key) -> Value:
        return self._kv[key].value

    @enforce_datatype(HASH)
    def hincrby(self, key, field, incr=1) -> Value:
        self._kv[key].value.setdefault(field, 0)
        self._kv[key].value[field] += incr
        return self._kv[key].value[field]

    @enforce_datatype(HASH)
    def hkeys(self, key) -> List[Value]:
        return list(self._kv[key].value)

    @enforce_datatype(HASH)
    def hlen(self, key) -> int:
        return len(self._kv[key].value)

    @enforce_datatype(HASH)
    def hmget(self, key, *fields) -> Dict:
        accum = {}
        value = self._kv[key].value
        for field in fields:
            accum[field] = value.get(field)
        return accum

    @enforce_datatype(HASH)
    def hmset(self, key, data) -> int:
        self._kv[key].value.update(data)
        return len(data)

    @enforce_datatype(HASH)
    def hset(self, key, field, value) -> int:
        self._kv[key].value[field] = value
        return 1

    @enforce_datatype(HASH)
    def hsetnx(self, key, field, value) -> int:
        kval = self._kv[key].value
        if field not in kval:
            kval[field] = value
            return 1
        return 0

    @enforce_datatype(HASH)
    def hvals(self, key) -> List:
        return list(self._kv[key].value.values())
