import datetime
from typing import Union, Optional, List, Dict, Set, Any, Callable
import json
from io import BytesIO
from collections import deque
from .exceptions import Error
from .types import unicode
from .utils import encode
from .utils.mixins import MetaUtils
from .logger import logger


class ProtocolHandler(MetaUtils):
    """
    ProtocolHandler is based on Redis Wire protocol
    Client sends requests as an array of bulk strings.

    Server replies, indicating response type using the first byte:

    * "+" - simple string
    * "-" - error
    * ":" - integer
    * "$" - bulk string
    * "^" - bulk unicode string
    * "@" - json string (uses bulk string rules)
    * "*" - array
    * "%" - dict
    * "&" - set

    Simple strings: "+string content\r\n"  <-- cannot contain newlines

    Error: "-Error message\r\n"

    Integers: ":1337\r\n"

    Bulk String: "$number of bytes\r\nstring data\r\n"

    * Empty string: "$0\r\n\r\n"
    * NULL: "$-1\r\n"

    Bulk unicode string (encoded as UTF-8): "^number of bytes\r\ndata\r\n"

    JSON string: "@number of bytes\r\nJSON string\r\n"

    Array: "*number of elements\r\n...elements..."

    * Empty array: "*0\r\n"

    Dictionary: "%number of elements\r\n...key0...value0...key1...value1..\r\n"

    Set: "&number of elements\r\n...elements..."
    """

    def __init__(self):
        self.handlers: Dict[bytes, Callable] = {
            b'+': self.handle_simple_string,
            b'-': self.handle_error,
            b':': self.handle_integer,
            b'$': self.handle_string,
            b'^': self.handle_unicode,
            b'@': self.handle_json,
            b'*': self.handle_array,
            b'%': self.handle_dict,
            b'&': self.handle_set,
        }

    def handle_request(self, socket_file) -> bytes:
        """
        Parse a request from the client into its components parts
        :param socket_file: Socket file
        :return:
        """
        first_byte = socket_file.read(1)
        if not first_byte:
            logger.error(f"[{self.name}] failed to handle request, missing first byte {first_byte}")
            raise EOFError()

        handler = self.handlers.get(first_byte, None)
        if handler:
            return handler(socket_file)
        else:
            logger.error(f"{self.name}> failed to handle request, missing value for key {first_byte}")
            rest = socket_file.readline().rstrip(b'\r\n')
            return first_byte + rest

    def write_response(self, socket_file, data: Any):
        """
        Serialize the response data and send it to the client
        :param socket_file:
        :param data:
        :return:
        """
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        socket_file.write(buf.getvalue())
        socket_file.flush()

    def _write(self, buf: BytesIO, data: Any):
        if isinstance(data, bytes):
            buf.write(b'$%d\r\n%s\r\n' % (len(data), data))
        elif isinstance(data, unicode):
            bdata = data.encode('utf-8')
            buf.write(b'^%d\r\n%s\r\n' % (len(bdata), bdata))
        elif data is True or data is False:
            buf.write(b':%d\r\n' % (1 if data else 0))
        elif isinstance(data, (int, float)):
            buf.write(b':%d\r\n' % data)
        elif isinstance(data, Error):
            buf.write(b'-%s\r\n' % encode(data.message))
        elif isinstance(data, (list, tuple, deque)):
            buf.write(b'*%d\r\n' % len(data))
            for item in data:
                self._write(buf, item)
        elif isinstance(data, dict):
            buf.write(b'%%%d\r\n' % len(data))
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])
        elif isinstance(data, set):
            buf.write(b'&%d\r\n' % len(data))
            for item in data:
                self._write(buf, item)
        elif data is None:
            buf.write(b'$-1\r\n')
        elif isinstance(data, datetime.datetime):
            self._write(buf, str(data))

    def handle_simple_string(self, socket_file) -> bytes:
        return socket_file.readline().rstrip(b'\r\n')

    def handle_error(self, socket_file) -> Error:
        return Error(socket_file.readline().rstrip(b'\r\n'))

    def handle_integer(self, socket_file) -> Union[float, int]:
        number = socket_file.readline().rstrip(b'\r\n')
        if b'.' in number:
            return float(number)
        return int(number)

    def handle_string(self, socket_file) -> Optional[bytes]:
        # read the length ($<length>\r\n)
        length = int(socket_file.readline().rstrip(b'\r\n'))
        if length == -1:
            # special case for NULLs
            return None
        # include the trailing \r\n in count
        length += 2
        return socket_file.read(length)[:-2]

    def handle_unicode(self, socket_file) -> Optional[str]:
        string_ = self.handle_string(socket_file=socket_file)
        if string_:
            return string_.decode('utf-8')
        return None

    def handle_json(self, socket_file):
        return json.loads(self.handle_string(socket_file=socket_file))

    def handle_array(self, socket_file) -> List:
        num_elements = int(socket_file.readline().rstrip(b'\r\n'))
        return [self.handle_request(socket_file=socket_file) for _ in range(num_elements)]

    def handle_dict(self, socket_file) -> Dict:
        num_items = int(socket_file.readline().rstrip(b'\r\n'))
        elements = [self.handle_request(socket_file=socket_file) for _ in range(num_items * 2)]
        return dict(zip(elements[::2], elements[1::2]))

    def handle_set(self, socket_file) -> Set:
        return set(self.handle_array(socket_file=socket_file))
