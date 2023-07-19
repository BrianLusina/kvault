"""
Test kvault with many concurrent connections.
"""
from gevent import monkey

monkey.patch_all()

import time

import gevent
from client import Client

client = Client()

def get_sleep_set(k, v, n=1):
    client.set(k, v)
    time.sleep(n)
    assert client.get(k) == v
    client.close()

if __name__ == '__main__':
    n = 3
    t = 256
    start = time.time()

    greenlets = []
    for i in range(t):
        greenlets.append(gevent.spawn(get_sleep_set, 'k%d' % i, 'v%d' % i, n))

    for g in greenlets:
        g.join()

    client.flush()
    stop = time.time()
    print('done. slept=%s, took %.2f for %s threads.' % (n, stop - start, t))
