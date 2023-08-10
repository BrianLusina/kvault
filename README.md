# kvault

[![License](https://img.shields.io/github/license/brianlusina/kvault)](https://github.com/brianlusina/kvault/blob/main/LICENSE)
[![Tests](https://github.com/BrianLusina/kvault/actions/workflows/tests.yaml/badge.svg)](https://github.com/BrianLusina/kvault/actions/workflows/tests.yaml)
[![Lint](https://github.com/BrianLusina/kvault/actions/workflows/lint.yml/badge.svg)](https://github.com/BrianLusina/kvault/actions/workflows/lint.yml)
[![Docker](https://github.com/BrianLusina/kvault/actions/workflows/docker.yaml/badge.svg)](https://github.com/BrianLusina/kvault/actions/workflows/docker.yaml)
[![Version](https://img.shields.io/github/v/release/brianlusina/kvault?color=%235351FB&label=version)](https://github.com/brianlusina/kvault/releases)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/fbb1708155284277be89e61c867d94ff)](https://www.codacy.com/gh/BrianLusina/kvault/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=BrianLusina/kvault&amp;utm_campaign=Badge_Grade)

`kvault` is a simple Miniature Key-Value Datastore in Python with a [Redis](https://redis.io)-like interface.

## Requirements

1. [Python 3.10+](https://www.python.org/downloads/)

   Python is the programming language of choice for this project, therefore, will be required to be available in
   the system. One can download and setup Python in their local development environment following the steps provided in
   the link.

2. [Poetry](https://python-poetry.org/)

   Poetry is the dependency manager & packaging tool used for this project and can be installed following the setup
   provided in the link as well.

3. [virtualenv](https://virtualenv.pypa.io/)

   Used to create virtual environments for installing & setting up Python dependencies.

## Setup

Running locally, will require a [virtualenv](https://virtualenv.pypa.io/) setup and that can be done by following the
instructions:

```shell
virtualenv .venv
```

> This will create a virtual environment in the current root directory of the project.

Next, install the required dependencies:

```shell
poetry install
```

> This installs the dependencies for the project.

## Running

by default, the `kvault` server runs on localhost:31337.

The following options are supported:

```plain
Usage: kvault.py [options]

Options:
  -h, --help            show this help message and exit
  -d, --debug           Log debug messages.
  -e, --errors          Log error messages only.
  -t, --use-threads     Use threads instead of gevent.
  -H HOST, --host=HOST  Host to listen on.
  -m MAX_CLIENTS, --max-clients=MAX_CLIENTS
                        Maximum number of clients.
  -p PORT, --port=PORT  Port to listen on.
  -l LOG_FILE, --log-file=LOG_FILE
                        Log file.
  -x EXTENSIONS, --extension=EXTENSIONS
                        Import path for Python extension module(s).
```

Note that the above output can be obtained from the below command:

```shell
python cli.py -h
```

To run with debug logging on port 31339, for example:

``` shell
python kvault.py -d -p 31339
``` 

This will result in an output like below:

```plain
  .--.
 /( @ >    ,-.  KVault 127.0.0.1:31339
/ ' .'--._/  /
:   ,    , .'
'. (___.'_/
 ((-((-''

```

> This indicates that the server is running and awaiting client connections

Client setup should be simple, in another terminal, open a new Python console to interact with the kvault server:

```python
from client import Client

client = Client()
client.set('key', {'name': 'Charlie', 'pets': ['mickey', 'huey']})

print(client.get('key'))  # {'name': 'Charlie', 'pets': ['mickey', 'huey']}
```

> A sample of the expected interaction of a client and `kvault` server

##