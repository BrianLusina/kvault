from gevent import monkey

monkey.patch_all()

from client import Client

import contextlib
import time


@contextlib.contextmanager
def timed(s):
    start = time.time()
    yield
    duration = round(time.time() - start, 3)
    print('%s: %s' % (s, duration))


def run_benchmark(client):
    number = 10000
    with timed('get/set'):
        for i in range(number):
            client.set('k%d' % i, 'v%d' % i)

        for i in range(number + int(number * 0.1)):
            client.get('k%d' % i)

    with timed('serializing arrays'):
        arr = [1, 2, 3, 4, 5, 6, [7, 8, 9, [10, 11, 12], 13], 14, 15]
        for i in range(number):
            client.set('k%d' % i, arr)

        for i in range(number):
            client.get('k%d' % i)

    with timed('serializing dicts'):
        key_value_pairs = {'k1': 'v1', 'k2': 'v2', 'k3': {'v3': {'v4': 'v5'}}}
        for i in range(number):
            client.set('k%d' % i, key_value_pairs)

        for i in range(number):
            client.get('k%d' % i)


def main():
    client = Client()

    try:
        run_benchmark(client)
    finally:
        client.close()


if __name__ == '__main__':
    main()
