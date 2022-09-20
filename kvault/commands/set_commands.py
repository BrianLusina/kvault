from commands import BaseCommand, SET
from ..utils import enforce_datatype
from ..types import Value


class SetCommands(BaseCommand):
    @enforce_datatype(SET)
    def sadd(self, key, *members):
        self._kv[key].value.update(members)
        return len(self._kv[key].value)

    @enforce_datatype(SET)
    def scard(self, key):
        return len(self._kv[key].value)

    @enforce_datatype(SET)
    def sdiff(self, key, *keys):
        src = set(self._kv[key].value)
        for key in keys:
            self.check_datatype(SET, key)
            src -= self._kv[key].value
        return list(src)

    @enforce_datatype(SET)
    def sdiffstore(self, dest, key, *keys):
        src = set(self._kv[key].value)
        for key in keys:
            self.check_datatype(SET, key)
            src -= self._kv[key].value
        self.check_datatype(SET, dest)
        self._kv[dest] = Value(SET, src)
        return len(src)

    @enforce_datatype(SET)
    def sinter(self, key, *keys):
        src = set(self._kv[key].value)
        for key in keys:
            self.check_datatype(SET, key)
            src &= self._kv[key].value
        return list(src)

    @enforce_datatype(SET)
    def sinterstore(self, dest, key, *keys):
        src = set(self._kv[key].value)
        for key in keys:
            self.check_datatype(SET, key)
            src &= self._kv[key].value
        self.check_datatype(SET, dest)
        self._kv[dest] = Value(SET, src)
        return len(src)

    @enforce_datatype(SET)
    def sismember(self, key, member):
        return 1 if member in self._kv[key].value else 0

    @enforce_datatype(SET)
    def smembers(self, key):
        return self._kv[key].value

    @enforce_datatype(SET)
    def spop(self, key, n=1):
        accum = []
        for _ in range(n):
            try:
                accum.append(self._kv[key].value.pop())
            except KeyError:
                break
        return accum

    @enforce_datatype(SET)
    def srem(self, key, *members):
        ct = 0
        for member in members:
            try:
                self._kv[key].value.remove(member)
            except KeyError:
                pass
            else:
                ct += 1
        return ct

    @enforce_datatype(SET)
    def sunion(self, key, *keys):
        src = set(self._kv[key].value)
        for key in keys:
            self.check_datatype(SET, key)
            src |= self._kv[key].value
        return list(src)

    @enforce_datatype(SET)
    def sunionstore(self, dest, key, *keys):
        src = set(self._kv[key].value)
        for key in keys:
            self.check_datatype(SET, key)
            src |= self._kv[key].value
        self.check_datatype(SET, dest)
        self._kv[dest] = Value(SET, src)
        return len(src)
