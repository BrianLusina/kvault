from collections import deque
from typing import Dict, Optional, AnyStr, List, Any, Union
import heapq
import time
import os
import pickle
import datetime
from ..exceptions import CommandError, ClientQuit, Shutdown
from ..types import Value
from ..utils import enforce_datatype, decode

KV = 0
HASH = 1
QUEUE = 2
SET = 3


class Commands(object):
    def __init__(self, kv: Optional[Dict[AnyStr, Value]], expiry_map: Dict, expiry: List, schedule: List):
        self._kv: Dict[AnyStr, Value] = kv
        self._expiry_map = expiry_map
        self._expiry = expiry
        self._schedule = schedule

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

    def expire(self, key, nseconds):
        eta = time.time() + nseconds
        self._expiry_map[key] = eta
        heapq.heappush(self._expiry, (eta, key))

    def clean_expired(self, ts=None):
        ts = ts or time.time()
        n = 0
        while self._expiry:
            expires, key = heapq.heappop(self._expiry)
            if expires > ts:
                heapq.heappush(self._expiry, (expires, key))
                break

            if self._expiry_map.get(key) == expires:
                del self._expiry_map[key]
                del self._kv[key]
                n += 1
        return n

    # Queue commands
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

    # ==== Hash Commands
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

    # ==== KV Commands

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

    # ====== Set Commands
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

    # ===== Misc Commands
    def _get_state(self):
        return {'kv': self._kv, 'schedule': self._schedule}

    def _set_state(self, state, merge=False):
        if not merge:
            self._kv = state['kv']
            self._schedule = state['schedule']
        else:
            def merge(orig, updates):
                orig.update(updates)
                return orig

            self._kv = merge(state['kv'], self._kv)
            self._schedule = state['schedule']

    def save_to_disk(self, filename):
        with open(filename, 'wb') as fh:
            pickle.dump(self._get_state(), fh, pickle.HIGHEST_PROTOCOL)
        return True

    def restore_from_disk(self, filename, merge=False):
        if not os.path.exists(filename):
            return False
        with open(filename, 'rb') as fh:
            state = pickle.load(fh)
        self._set_state(state, merge=merge)
        return True

    def merge_from_disk(self, filename):
        return self.restore_from_disk(filename, merge=True)

    def client_quit(self):
        raise ClientQuit('client closed connection')

    def shutdown(self):
        raise Shutdown('shutting down')

    # ===== Scheduled commands
    def _decode_timestamp(self, timestamp):
        timestamp = decode(timestamp)
        fmt = '%Y-%m-%d %H:%M:%S'
        if '.' in timestamp:
            fmt = fmt + '.%f'
        try:
            return datetime.datetime.strptime(timestamp, fmt)
        except ValueError:
            raise CommandError('Timestamp must be formatted Y-m-d H:M:S')

    def schedule_add(self, timestamp, data):
        dt = self._decode_timestamp(timestamp)
        heapq.heappush(self._schedule, (dt, data))
        return 1

    def schedule_read(self, timestamp=None):
        dt = self._decode_timestamp(timestamp)
        accum = []
        while self._schedule and self._schedule[0][0] <= dt:
            ts, data = heapq.heappop(self._schedule)
            accum.append(data)
        return accum

    def schedule_flush(self):
        schedule_len = self.schedule_length()
        self._schedule = []
        return schedule_len

    def schedule_length(self):
        return len(self._schedule)
