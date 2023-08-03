"""
Contains Queue commands
"""
from typing import Dict, Any
from collections import deque
from ..utils import enforce_datatype
from ..types import Value, QUEUE
from ..utils.mixins import Guards
from ..exceptions import CommandError


class QueueCommands(Guards):
    """
    Contains Queue Commands
    """

    def __init__(self, kv: Dict[Any, Value], expiry_map: Dict[Any, float]):
        """Creates an instance of QueueCommands"""
        self._kv = kv
        super().__init__(kv, expiry_map)

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
        except IndexError as ie:
            raise CommandError(f"Failed to find key with error {ie}. Key {key} does not exist")

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
        except IndexError as ie:
            raise CommandError(f"Failed to find key with error {ie}. Key {key} does not exist")

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
        else:
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
        except IndexError as ie:
            raise CommandError(f"Failed to find key with error {ie}. Key {key} does not exist")

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
        except IndexError:
            return 0
        else:
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
        except IndexError as ie:
            raise CommandError(f"Failed to find key with error {ie}. Key {key} does not exist")

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
        except IndexError:
            return 0
        else:
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
        except IndexError as ie:
            raise CommandError(f"Failed to find key with error {ie}. Key {key} does not exist")

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
        except IndexError as ie:
            raise CommandError(f"Failed to find key with error {ie}. Key {key} does not exist")
