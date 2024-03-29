import functools
import sys
import threading
import unittest
import gevent

from client import Client
from kvault.queue_server import QueueServer

TEST_HOST = '127.0.0.1'
TEST_PORT = 31339


def run_queue_server():
    queue_server = QueueServer(host=TEST_HOST, port=TEST_PORT)
    greenlet = gevent.spawn(queue_server.run)
    gevent.sleep()
    return greenlet, queue_server


class KeyPartial:
    def __init__(self, client, key):
        self.client = client
        self.key = key

    def __getattr__(self, attr):
        return functools.partial(getattr(self.client, attr), self.key)


class KvaultMiniDatabaseTestCases(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        run_queue_server()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self):
        self.c = Client(host=TEST_HOST, port=TEST_PORT)

    def tearDown(self) -> None:
        self.c.flush()

    def test_list(self):
        key_partial = KeyPartial(self.c, 'queue')

        key_partial.lpush('i1')
        key_partial.lpush('i2')
        key_partial.rpush('i3')
        key_partial.rpush('i4')
        result = key_partial.lrange(0)
        self.assertEqual(result, ['i2', 'i1', 'i3', 'i4'])

        self.assertEqual(key_partial.lpop(), 'i2')
        self.assertEqual(key_partial.rpop(), 'i4')
        self.assertEqual(key_partial.llen(), 2)

        self.assertEqual(key_partial.lrem('i3'), 1)
        self.assertEqual(key_partial.lrem('i3'), 0)

        key_partial.lpush('a1', 'a2', 'a3', 'a4')
        self.assertEqual(key_partial.lindex(2), 'a2')

        key_partial.lset(2, 'x')
        self.assertEqual(key_partial.lrange(1, 3), ['a3', 'x'])

        key_partial.ltrim(1, 4)
        self.assertEqual(key_partial.lrange(0), ['a3', 'x', 'a1'])
        self.assertEqual(key_partial.lflush(), 3)

    def test_kv(self):
        kp = KeyPartial(self.c, 'k1')
        kp.set(['alpha', 'beta', 'gamma'])
        self.assertEqual(kp.get(), ['alpha', 'beta', 'gamma'])

        res = kp.append(['pi', b'omega'])
        self.assertEqual(res, ['alpha', 'beta', 'gamma', 'pi', b'omega'])

        kp.set([b'foo', b'bar', b'baz'])
        self.assertEqual(kp.get(), [b'foo', b'bar', b'baz'])

    def test_incr_decr(self):
        self.assertEqual(self.c.incr('i'), 1)
        self.assertEqual(self.c.decr('i'), 0)
        self.assertEqual(self.c.incrby('i2', 3), 3)
        self.assertEqual(self.c.incrby('i2', 2), 5)

    def test_persistence(self):
        self.c.set('k1', 'v1')
        self.c.hset('h1', 'k1', 'v1')
        self.c.sadd('s1', 'v1', 'v2')
        self.assertTrue(self.c.save('/tmp/simpledb.state'))
        self.c.flushall()

        self.assertTrue(self.c.get('k1') is None)
        self.assertTrue(self.c.hget('h1', 'k1') is None)
        self.assertTrue(self.c.scard('s1') == 0)

        self.c.set('k1', 'x1')
        self.c.set('k2', 'x2')
        self.assertTrue(self.c.restore('/tmp/simpledb.state'))
        self.assertEqual(self.c.get('k1'), 'v1')
        self.assertTrue(self.c.get('k2') is None)
        self.assertEqual(self.c.hget('h1', 'k1'), 'v1')
        self.assertEqual(self.c.scard('s1'), 2)

        self.c.flushall()
        self.c.set('k1', 'x1')
        self.c.set('k2', 'x2')
        self.assertTrue(self.c.merge('/tmp/simpledb.state'))
        self.assertEqual(self.c.get('k1'), 'x1')
        self.assertEqual(self.c.get('k2'), 'x2')
        self.assertEqual(self.c.hget('h1', 'k1'), 'v1')
        self.assertEqual(self.c.scard('s1'), 2)

    def test_expiry(self):
        self.c.mset({'k1': 'v1', 'k2': 'v2', 'k3': 'v3'})

        # Make it appear to expire in the past.
        self.c.expire('k2', -1)
        self.c.expire('k3', 3)
        self.assertEqual(self.c.mget('k1', 'k2', 'k3'), ['v1', None, 'v3'])


if __name__ == '__main__':
    server_t, server = run_queue_server()
    unittest.main(argv=sys.argv)
