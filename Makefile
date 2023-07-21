# Installs dependencies
install:
	pipenv install

lint: # runs linting
	pylint kvault

test: # runs tests
	pytest

build: # builds and packages the application
	poetry build

test-cover: # Runs tests with coverage
	pytest --cov=kvault tests/

format: # Runs formatting with black
	black kvault

pre-commit-install: # installs pre commit hooks
	pre-commit install

pre-commit: # runs pre commit hooks
	pre-commit run --all-files
