# Installs dependencies
install:
	pipenv install

# Runs application
run:
	python asgi_server.py

# Runs the application with reload flag set
run-reload:
	uvicorn app:app --port 5000 --reload

# Runs tests
test:
	pytest

# Runs tests with coverage
test-cover:
	pytest --cov=app tests/

format:
	black app

lint:
	pylint app

load-test:
	locust --config .locust.conf
