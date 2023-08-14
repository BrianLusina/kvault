# pylint: disable-next=too-many-lines
"""
Contains all commands performed by the key store
"""
from collections import deque
from typing import Dict, Optional, AnyStr, List, Any, Union
import heapq
import time
import os
import pickle
import datetime
from ..utils.mixins import Guards
from ..exceptions import CommandError, ClientQuit, Shutdown
from ..types import Value, KV, HASH, QUEUE, SET
from ..utils import enforce_datatype, decode


# pylint: disable-next=too-many-public-methods
class Commands(Guards):
    """
    Commands class contains all the commands performed by the key store
    """

    def __init__(
        self,
        kv_store: Optional[Dict[AnyStr, Value]],
        expiry_map: Dict,
        expiry: List,
        schedule: List,
    ):
        """Creates an instance of commands"""
        self._kv: Dict[AnyStr, Value] = kv_store
        self._expiry_map = expiry_map
        self._expiry = expiry
        self._schedule = schedule

        super().__init__(self._kv, self._expiry_map)

    def expire(self, key, nseconds: Union[float, int]):
        """Sets an expiry time for a key in nano-seconds."""
        eta = time.time() + nseconds
        self._expiry_map[key] = eta
        heapq.heappush(self._expiry, (eta, key))

    def clean_expired(self, timestamp=None):
        """
        Performs cleanup of the expired keys
        :param timestamp: timestamp to check against expired keys
        :return: Number of cleanups performed
        """
        _timestamp = timestamp or time.time()
        cleanup_count = 0
        while self._expiry:
            expires, key = heapq.heappop(self._expiry)
            if expires > _timestamp:
                heapq.heappush(self._expiry, (expires, key))
                break

            if self._expiry_map.get(key) == expires:
                del self._expiry_map[key]
                del self._kv[key]
                cleanup_count += 1
        return cleanup_count

    ## Queue commands
    @enforce_datatype(QUEUE)
    def lpush(self, key, *values) -> int:
        """
        Pushes a key with values to a list. This is added to the left of the list
        :param key: identifying Key for the values.
        :param values: Values
        :return: length of values to add
        """
        self._kv[key].value.extendleft(values)
        return len(values)

    @enforce_datatype(QUEUE)
    def rpush(self, key, *values) -> int:
        """
        Pushes a list of values given a key to a list
        :param key: Key to use to identify the values.
        :param values: values to push
        :return: Length of values added
        """
        self._kv[key].value.extend(values)
        return len(values)

    @enforce_datatype(QUEUE)
    def lpop(self, key) -> Any:
        """
        Pops the left item from the queue given a key.
        :param key: Key to pop from the list
        :return: the value of the key
        :raises CommandError if key is not found
        """
        try:
            return self._kv[key].value.popleft()
        except KeyError as key_error:
            raise CommandError(
                f"Failed to find key with error {key_error}. Key {key} does not exist"
            ) from key_error

    @enforce_datatype(QUEUE)
    def rpop(self, key) -> Any:
        """
        Pops the right item from the queue
        :param key: key to pop
        :return: value of key
        :raises CommandError if key is not found
        """
        try:
            return self._kv[key].value.pop()
        except KeyError as error:
            raise CommandError(
                f"Failed to find key with error {error}. Key {key} does not exist"
            ) from error

    @enforce_datatype(QUEUE)
    def lrem(self, key, value) -> int:
        """
        Removes the first occurrence of a value of a given key.
        :param key: Key to use to remove instances of value.
        :param value: Value to remove.
        :return: 0 if value is not found, 1 if value has been removed
        """
        try:
            self._kv[key].value.remove(value)
        except ValueError:
            return 0
        return 1

    @enforce_datatype(QUEUE)
    def llen(self, key) -> int:
        """
        Returns the length of the values of the given key.
        :param key: Key to check for
        :return: length of the values of the given key
        """
        return len(self._kv[key].value)

    @enforce_datatype(QUEUE)
    def lindex(self, key, idx):
        """
        Retrieves the value of a key given a particular index. If the key does not exist, a CommandError is raised
        :param key: Key to check for.
        :param idx: Index of the value to look for in the given key-value pair
        :return: Value at the given index
        :raise: CommandError
        """
        try:
            return self._kv[key].value[idx]
        except KeyError as error:
            raise CommandError(
                f"Failed to find key with error {error}. Key {key} does not exist"
            ) from error

    @enforce_datatype(QUEUE)
    def lset(self, key, idx, value):
        """
        Sets the key, index and value
        :param key: Key to set
        :param idx: Position or index to set the value.
        :param value: The value to set
        :return: 0 if the key does not exist, 1 if the operation is successful
        """
        try:
            self._kv[key].value[idx] = value
        except KeyError:
            return 0
        return 1

    @enforce_datatype(QUEUE)
    def ltrim(self, key, start, stop):
        """
        Trims the key from a given start index to a given stop index(not inclusive). This returns the new trimmed length
        of the queue
        :param key: Key to trim
        :param start: Start of the range
        :param stop: End of the range, exclusive
        :return: length of the trimmed queue
        :raise CommandError if key does not exist
        """
        try:
            trimmed = list(self._kv[key].value)[start:stop]
            self._kv[key] = Value(QUEUE, deque(trimmed))
            return len(trimmed)
        except KeyError as error:
            raise CommandError(
                f"Failed to find key with error {error}. Key {key} does not exist"
            ) from error

    @enforce_datatype(QUEUE)
    def rpoplpush(self, src, dest):
        """
        Pops a given key 'src's value and appends it to the left of the key 'dest' value.
        :param src: Source key whose right value will be popped
        :param dest: Where the popped value will be added
        :return: 0 if the operation fails. For example if either one of the keys does not exist. 1 if the operation
        succeeds
        """
        self.check_datatype(QUEUE, dest, set_missing=True)
        try:
            self._kv[dest].value.appendleft(self._kv[src].value.pop())
        except KeyError:
            return 0
        return 1

    @enforce_datatype(QUEUE)
    def lrange(self, key, start, end=None):
        """
        Returns a range of values of a given key from the start to end. Note that the end value is exclusive
        :param key: Key to get range
        :param start: Start of range
        :param end: End of range(exclusive)
        :return: values in the given range
        :raises: CommandError if key does not exist
        """
        try:
            return list(self._kv[key].value)[start:end]
        except KeyError as error:
            raise CommandError(
                f"Failed to find key with error {error}. Key {key} does not exist"
            ) from error

    @enforce_datatype(QUEUE)
    def lflush(self, key):
        """
        Clears the value of a given key if the key exists
        :param key: Key whose value is to be cleared
        :return: The length of the cleared value
        :raises CommandError if the key does not exist
        """
        try:
            qlen = len(self._kv[key].value)
            self._kv[key].value.clear()
            return qlen
        except KeyError as error:
            raise CommandError(
                f"Failed to find key with error {error}. Key {key} does not exist"
            ) from error

    ## Hash commands
    @enforce_datatype(HASH)
    def hdel(self, key, field) -> int:
        """
        Deletes a field with a given key if available. If the key does not exist a CommandError is raised
        :param key: Key to use.
        :param field: Field to delete
        :return: 1 if the key is successfully deleted. 0 if there is a failure deleting the key
        """
        try:
            value = self._kv[key].value
            if field in value:
                del value[field]
                return 1
            return 0
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hexists(self, key, field) -> int:
        """
        Checks if a field exists in a given key.
        :param key: Key to use
        :param field: value to check for
        :return: 1 if field exists in the key's value, else 0
        :raises: CommandError if the key does not exist
        """
        try:
            value = self._kv[key].value
            return 1 if field in value else 0
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hget(self, key, field) -> Any:
        """
        Gets the value of a field given the key.
        :param key: Key to retrieve value
        :param field: Field to obtain value
        :return: Field's value
        """
        try:
            return self._kv[key].value.get(field)
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hgetall(self, key) -> Value:
        """
        Gets all values of a given key
        :param key: Key to use
        :return: value of a given key if the key exists
        """
        try:
            return self._kv[key].value
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hincrby(self, key, field, incr=1) -> Value:
        """
        Increments a given field in a key by 1
        :param key: Key to use to obtain field.
        :param field: Field to increment
        :param incr: Amount to increment field by. defaulted to 1
        :return: new value
        :raises CommandError if key does not exist
        """
        try:
            self._kv[key].value.setdefault(field, 0)
            self._kv[key].value[field] += incr
            return self._kv[key].value[field]
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hkeys(self, key) -> List[Value]:
        """
        Retrieves values of a given key.
        :param key: Key.
        :return: List of values.
        """
        try:
            return list(self._kv[key].value)
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hlen(self, key) -> int:
        """
        Retrieves the length of the key's values.
        :param key: Key.
        :return: length of keys values
        """
        try:
            return len(self._kv[key].value)
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hmget(self, key, *fields) -> Dict:
        """
        Gets all fields from a key.
        :param key: Key to retrieve values
        :param fields: Fields to extract from values
        :return: dictionary mapping of fields to their values
        """
        try:
            accum = {}
            value = self._kv[key].value
            for field in fields:
                accum[field] = value.get(field)
            return accum
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hmset(self, key, data) -> int:
        """
        Updates key's value with new data
        :param key: Key to update
        :param data: New data to update
        :return: length of data
        """
        try:
            self._kv[key].value.update(data)
            return len(data)
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hset(self, key, field, value) -> int:
        """
        Update the value of a field for a given key.
        :param key: Key to update
        :param field: field to update
        :param value: new value to update field to
        :return: 1 if successful
        """
        try:
            self._kv[key].value[field] = value
            return 1
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hsetnx(self, key, field, value) -> int:
        """
        Updates a key's field with the given value if it is not in the key's value. Will return 1 if the field is not in
        the key's value and update is successful. Otherwise, returns 0 indicating that the field is not in the key's
        value
        :param key: Key to use to retrieve value
        :param field: field to update in the key's value.
        :param value: new value to update field to
        :return: 1 if successful, 0 otherwise
        """
        try:
            kval = self._kv[key].value
            if field not in kval:
                kval[field] = value
                return 1
            return 0
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    @enforce_datatype(HASH)
    def hvals(self, key) -> List:
        """
        Retrieves the values of a given key and returns them as a list of field value pairs
        :param key: Key to retrieve values from
        :return: List of values
        """
        try:
            return list(self._kv[key].value.values())
        except KeyError as error:
            raise CommandError(f"key {key} does not exist. Error: {error}") from error

    # ==== KV Commands
    def unexpire(self, key):
        """
        Removes an expired key from expiry map
        :param key: Key to remove
        """
        self._expiry_map.pop(key, None)

    def _kv_incr(self, key, delta: int) -> Union[Value, Any]:
        """
        Increments the key's value by n. If the key does not exist a new key value is created and they key is returned
        :param key: Key
        :param delta: Delta to increase the value by
        """
        if key in self._kv:
            value = self._kv[key].value + delta
        else:
            value = delta
        self._kv[key] = Value(KV, value)
        return value

    def kv_append(self, key, value):
        """
        Appends a new key value pair
        :param key: Key to add
        :param value: value to add
        """
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
                    self._kv[key] = kv_val
                except Exception as error:
                    raise CommandError(f"Incompatible data-types {value}") from error
        return self._kv[key].value

    def kv_set(self, key, value) -> int:
        """
        Sets a new key value pair and returns 1 if successful
        :param key: Key to add.
        :param value: Value to add
        """
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
        """
        Decrements a key's value by 1
        :param key: key to decrement.
        """
        return self._kv_incr(key=key, delta=-1)

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_decrby(self, key, delta: Union[float, int]):
        """
        Decrements a key's value by a set amount n
        :param key: key to decrement
        :param delta: Value to decrement key by
        """
        return self._kv_incr(key=key, delta=-1 * delta)

    def kv_delete(self, key) -> int:
        """
        Deletes a key. returns 1 if successful, 0 if key can not be found
        :param key: Key to delete
        """
        if key in self._kv:
            del self._kv[key]
            return 1
        return 0

    def kv_exists(self, key) -> int:
        """
        Checks if a key exists and has not expired
        :param key: Key to check
        :return: 1 if key is available, 0 if key is not available or has expired
        """
        return 1 if key in self._kv and not self.check_expired(key) else 0

    def kv_get(self, key) -> Optional[Value]:
        """
        Gets the value of a key if the key exists and has not expired
        :param key: Key to check
        :return: Key's value if it exists else None is returned if the key does not exist and has expired
        """
        if key in self._kv and not self.check_expired(key):
            return self._kv[key].value
        return None

    def kv_getset(self, key, value) -> Optional[Value]:
        """
        Retrieves the original value of a key if it exists and has not expired and updates it to a new value and returns
        the old value
        :param key: Key to update
        :param value: new value to update to
        :return: original value of the key
        """
        original_value = None
        if key in self._kv and not self.check_expired(key):
            original_value = self._kv[key].value

        self._kv[key] = Value(KV, value)
        return original_value

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_incr(self, key):
        """
        Increments the value of a key by 1
        :param key: key to increment value by
        """
        return self._kv_incr(key, 1)

    @enforce_datatype(KV, set_missing=False, subtype=(float, int))
    def kv_incrby(self, key, delta):
        """
        Increments the value of a key by n
        :param key: key to increment
        :param delta: delta to increment the value by
        """
        return self._kv_incr(key, delta)

    def kv_mdelete(self, *keys):
        """
        Tries deleting keys if available. Returns the total number of keys deleted
        :param keys: Keys to delete
        :return: number of keys deleted
        """
        deleted_key_count = 0
        for key in keys:
            try:
                del self._kv[key]
            except KeyError:
                pass
            else:
                deleted_key_count += 1
        return deleted_key_count

    def kv_mget(self, *keys) -> List[Optional[Value]]:
        """
        Retrieves the values of keys and returns a list of values for the keys. In this list, some values will be None.
        indicating that a value for that key was not found. For example: [1, None, 3, 5, None] for keys
        ['a', 'b', 'c', 'd', 'e']. This means values for keys 'b' and 'e' could not be found because they either do not
        exist or the keys have expired.
        :param keys: Keys
        :return: list of values
        """
        accum = []
        for key in keys:
            if key in self._kv and not self.check_expired(key):
                accum.append(self._kv[key].value)
            else:
                accum.append(None)
        return accum

    def kv_mpop(self, *keys) -> List[Optional[Value]]:
        """
        Retrieves the values of keys and removes them. This returns a list of values for the keys. In this list,
        some values will be None. indicating that a value for that key was not found. For example: [1, None, 3, 5, None]
        for keys  ['a', 'b', 'c', 'd', 'e']. This means values for keys 'b' and 'e' could not be found because they
        either do not exist or the keys have expired.

        :param keys: Keys
        :return: list of values
        """
        accum = []
        for key in keys:
            if key in self._kv and not self.check_expired(key):
                accum.append(self._kv.pop(key).value)
            else:
                accum.append(None)
        return accum

    def kv_mset(self, __data: Optional[Dict] = None, **kwargs) -> int:
        """
        Adds and unexpires key value pairs __data along with kwargs. This returns the number of updates performed.
        :param __data: key value pairs to add
        :param kwargs: Additional key value pairs to add
        :return: number of updates performed
        """
        update_count = 0
        data = {}
        if __data is not None:
            data.update(__data)
        if kwargs is not None:
            data.update(kwargs)

        for key_, _ in data.items():
            self.unexpire(key_)
            self._kv[key_] = Value(KV, data[key_])
            update_count += 1
        return update_count

    def kv_msetex(self, data: Dict, expires: Union[float, int]):
        """
        Calls on kv_mset with the provided key value pairs and sets an expiry time for the keys
        :param data: Key value pairs to add.
        :param expires: when a key should expire. This will apply to all keys in data
        """
        self.kv_mset(data)
        for key in data:
            self.expire(key, expires)

    def kv_pop(self, key) -> Optional[Value]:
        """
        Pops a key if the key is available and if it has expired
        :param key: Key to pop.
        :return: The value of the popped key
        """
        if key in self._kv and not self.check_expired(key):
            return self._kv.pop(key).value
        return None

    def kv_setnx(self, key, value) -> int:
        """
        Sets a value of a key if it's not available and has not expired.
        :param key: Key to add
        :param value: Value of key
        :return: 1 if the key is added, 0 if no operation is performed
        """
        if key in self._kv and not self.check_expired(key):
            return 0
        self.unexpire(key)
        self._kv[key] = Value(KV, value)
        return 1

    def kv_setex(self, key: Any, value: Value, expires: Union[float, int]) -> int:
        """
        Sets the value of a key and the expiry of the key.
        :param key: Key to set
        :param value: Value of the key
        :param expires: Expiry time of the key
        """
        self.kv_set(key, value)
        self.expire(key, expires)
        return 1

    def kv_len(self) -> int:
        """
        Returns the length of the keys
        :return: length of the keys.
        """
        return len(self._kv)

    def kv_flush(self) -> int:
        """
        Clears the keys, expiry and expiry_map and returns the original length of the keys.
        :return: length of the original key
        """
        kvlen = self.kv_len()
        self._kv.clear()
        self._expiry = []
        self._expiry_map = {}
        return kvlen

    # ====== Set Commands
    @enforce_datatype(SET)
    def sadd(self, key, *members):
        """
        Updates the key with the members
        :param key: Key to update
        :param members: members to add.
        :return: The new length of the key's values
        """
        try:
            self._kv[key].value.update(members)
            return len(self._kv[key].value)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def scard(self, key):
        """
        Returns the length of the key's values for a set
        :param key: Key to use
        :return: length of new key
        """
        return len(self._kv[key].value)

    @enforce_datatype(SET)
    def sdiff(self, key, *keys) -> List:
        """
        Returns the difference between the key and the set of keys
        :param key: Key to use
        :param keys: set of keys to check.
        :return: list of the difference between the keys.
        """
        try:
            src = set(self._kv[key].value)
            for key_ in keys:
                self.check_datatype(SET, key_)
                src -= self._kv[key_].value
            return list(src)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def sdiffstore(self, dest, key, *keys) -> int:
        """
        Finds the difference between the key and as set of keys before setting the value of the key "dest" with the
        difference from the set.
        :param dest: Destination key to store values
        :param key: Key to check for difference
        :param keys: collection of keys to check for difference
        :return: length of difference between the keys
        """
        try:
            src = set(self._kv[key].value)
            for key_ in keys:
                self.check_datatype(SET, key_)
                src -= self._kv[key_].value
            self.check_datatype(SET, dest)
            self._kv[dest] = Value(SET, src)
            return len(src)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def sinter(self, key, *keys) -> List:
        """
        Checks the intersection between key and set of keys and returns the list
        :param key: Key
        :param keys: set of keys to check
        :return: list of intersection
        """
        try:
            src = set(self._kv[key].value)
            for key_ in keys:
                self.check_datatype(SET, key_)
                src &= self._kv[key_].value
            return list(src)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def sinterstore(self, dest, key, *keys) -> int:
        """
        Checks the intersection between key and keys and stores the intersection in "dest"
        :param dest: Destination key
        :param key: Source key
        :param keys: Set of keys
        :return: length of intersection
        """
        try:
            src = set(self._kv[key].value)
            for key_ in keys:
                self.check_datatype(SET, key_)
                src &= self._kv[key_].value
            self.check_datatype(SET, dest)
            self._kv[dest] = Value(SET, src)
            return len(src)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def sismember(self, key, member):
        """
        Checks if a member is a member of a key's value.
        :param key: Key to check
        :param member: Member to check
        :return: 1 if member is a member of a set, else returns 0
        """
        try:
            return 1 if member in self._kv[key].value else 0
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def smembers(self, key):
        """
        returns the members of a key.
        :param key: Key to use
        :return: member values of the key.
        """
        try:
            return self._kv[key].value
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def spop(self, key, number_to_pop=1) -> List[Value]:
        """
        Pops n values from the key and returns them
        :param key: Key to pop
        :param number_to_pop: number of values
        :return: accumulated values
        """
        accum = []
        for _ in range(number_to_pop):
            try:
                accum.append(self._kv[key].value.pop())
            except KeyError:
                break
        return accum

    @enforce_datatype(SET)
    def srem(self, key, *members) -> int:
        """
        Removes a set of members from the given key's values
        :param key: Key to remove
        :param members: set of members
        :return: number of members removed
        """
        remove_count = 0
        for member in members:
            try:
                self._kv[key].value.remove(member)
            except KeyError:
                pass
            else:
                remove_count += 1
        return remove_count

    @enforce_datatype(SET)
    def sunion(self, key, *keys) -> List:
        """
        Returns the union of key and keys
        :param key: Key to check for union
        :param keys: Keys to check for union
        :return: list of union pairs
        """
        try:
            src = set(self._kv[key].value)
            for key_ in keys:
                self.check_datatype(SET, key_)
                src |= self._kv[key_].value
            return list(src)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    @enforce_datatype(SET)
    def sunionstore(self, dest, key, *keys) -> int:
        """
        Gets the union of key and keys and stores it in dest
        :param dest: Destination key
        :param key: source key
        :param keys: Set or collection of keys
        :return: length of union
        """
        try:
            src = set(self._kv[key].value)
            for key_ in keys:
                self.check_datatype(SET, key_)
                src |= self._kv[key_].value
            self.check_datatype(SET, dest)
            self._kv[dest] = Value(SET, src)
            return len(src)
        except KeyError as error:
            raise CommandError(f"Key {key} does not exist {error}") from error

    def _get_state(self) -> Dict[str, Any]:
        """
        Returns the current state of the store
        :return: dictionary mapping of state keys to mappings
        """
        return {"kv": self._kv, "schedule": self._schedule}

    def _set_state(self, state: Dict[str, Any], merge=False):
        """
        Sets the state to a new given state
        :param state: New state
        :param merge: whether to merge the state with the new state
        """
        if not merge:
            self._kv = state["kv"]
            self._schedule = state["schedule"]
        else:

            def merge(orig, updates):
                orig.update(updates)
                return orig

            self._kv = merge(state["kv"], self._kv)
            self._schedule = state["schedule"]

    def save_to_disk(self, filename) -> bool:
        """Saves the current state to disk given a filename."""
        with open(filename, "wb") as file_handle:
            pickle.dump(self._get_state(), file_handle, pickle.HIGHEST_PROTOCOL)
        return True

    def restore_from_disk(self, filename: str, merge=False):
        """
        Restores a file from disk if the file exists. It also performs a merge of the stored state with the current
        state if the merge argument is set to True
        :param filename: filename to use
        :param merge: whether to merge to the new state
        """
        if not os.path.exists(filename):
            return False
        with open(filename, "rb") as file_handle:
            state = pickle.load(file_handle)
        self._set_state(state, merge=merge)
        return True

    def merge_from_disk(self, filename) -> bool:
        """Merges stored file from disk with the current state of store"""
        return self.restore_from_disk(filename, merge=True)

    def client_quit(self):
        """Raises a client quit exception"""
        raise ClientQuit("client closed connection")

    def shutdown(self):
        """Raises a shutdown exception"""
        raise Shutdown("shutting down")

    def _decode_timestamp(self, timestamp: str) -> datetime:
        """Decodes a given timestamp"""
        timestamp_ = decode(timestamp)
        fmt = "%Y-%m-%d %H:%M:%S"
        if "." in timestamp_:
            fmt = fmt + ".%f"
        try:
            return datetime.datetime.strptime(timestamp_, fmt)
        except ValueError as error:
            raise CommandError(
                f"Timestamp {timestamp} must be formatted Y-m-d H:M:S"
            ) from error

    def schedule_add(self, timestamp, data) -> int:
        """
        Adds a new schedule to recorded schedules
        :param timestamp: timestamp to decode
        :param data: data to add to schedule
        """
        try:
            decoded_timestamp = self._decode_timestamp(timestamp)
            heapq.heappush(self._schedule, (decoded_timestamp, data))
            return 1
        except Exception as error:
            raise CommandError(
                f"timestamp {timestamp} does not exist {error}"
            ) from error

    def schedule_read(self, timestamp=None) -> List:
        """
        Reads a given timestamp and returns the schedules that are less than the given timestamp. This removes the
        schedules from the given schedule record.
        """
        try:
            decoded_timestamp = self._decode_timestamp(timestamp)
            accum = []
            while self._schedule and self._schedule[0][0] <= decoded_timestamp:
                _, data = heapq.heappop(self._schedule)
                accum.append(data)
            return accum
        except Exception as error:
            raise CommandError(f"Failed to read {timestamp}. Error: {error}") from error

    def schedule_flush(self) -> int:
        """
        Flushes the schedule and returns the previous length.
        """
        schedule_len = self.schedule_length()
        self._schedule = []
        return schedule_len

    def schedule_length(self) -> int:
        """
        Returns the length of the schedule
        """
        return len(self._schedule)
