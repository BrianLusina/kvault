# Installs dependencies
install:
	pipenv install

# Runs tests
test:
	pytest

# Runs tests with coverage
test-cover:
	pytest --cov=kvault tests/

format:
	black kvault

lint:
	pylint kvault

load-test:
	locust --config .locust.conf

pre-commit-install:
	pre-commit install

pre-commit:
	pre-commit run --all-files
