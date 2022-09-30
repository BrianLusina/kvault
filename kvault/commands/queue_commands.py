from collections import deque
from .commands import BaseCommand, QUEUE
from ..types import Value
from ..utils import enforce_datatype


class QueueCommands(BaseCommand):

    @enforce_datatype(QUEUE)
    def lpush(self, key, *values):
        self._kv[key].value.extendleft(values)
        return len(values)

    @enforce_datatype(QUEUE)
    def rpush(self, key, *values):
        self._kv[key].value.extend(values)
        return len(values)

    @enforce_datatype(QUEUE)
    def lpop(self, key):
        try:
            return self._kv[key].value.popleft()
        except IndexError:
            pass

    @enforce_datatype(QUEUE)
    def rpop(self, key):
        try:
            return self._kv[key].value.pop()
        except IndexError:
            pass

    @enforce_datatype(QUEUE)
    def lrem(self, key, value):
        try:
            self._kv[key].value.remove(value)
        except ValueError:
            return 0
        else:
            return 1

    @enforce_datatype(QUEUE)
    def llen(self, key):
        return len(self._kv[key].value)

    @enforce_datatype(QUEUE)
    def lindex(self, key, idx):
        try:
            return self._kv[key].value[idx]
        except IndexError:
            pass

    @enforce_datatype(QUEUE)
    def lset(self, key, idx, value):
        try:
            self._kv[key].value[idx] = value
        except IndexError:
            return 0
        else:
            return 1

    @enforce_datatype(QUEUE)
    def ltrim(self, key, start, stop):
        trimmed = list(self._kv[key].value)[start:stop]
        self._kv[key] = Value(QUEUE, deque(trimmed))
        return len(trimmed)

    @enforce_datatype(QUEUE)
    def rpoplpush(self, src, dest):
        self.check_datatype(QUEUE, dest, set_missing=True)
        try:
            self._kv[dest].value.appendleft(self._kv[src].value.pop())
        except IndexError:
            return 0
        else:
            return 1

    @enforce_datatype(QUEUE)
    def lrange(self, key, start, end=None):
        return list(self._kv[key].value)[start:end]

    @enforce_datatype(QUEUE)
    def lflush(self, key):
        qlen = len(self._kv[key].value)
        self._kv[key].value.clear()
        return qlen
