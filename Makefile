# Installs dependencies
install:
	pipenv install

lint-pylint: ## runs linting
	poetry run pylint kvault

lint-mypy: ## runs type checking
	poetry run mypy .

lint-flake8: ## Runs formatting with flake8
	poetry run flake8 kvault

lint-black: ## Runs formatting with black
	black kvault

lint: lint-black lint-flake8 lint-mypy

test: # runs tests
	pytest

start: ## starts server
	python kvault.py

build: # builds and packages the application
	poetry self add "poetry-dynamic-versioning[plugin]"
	poetry build

test-cover: # Runs tests with coverage
	poetry run pytest --cov=kvault tests/

pre-commit-install: # installs pre commit hooks
	pre-commit install

pre-commit: # runs pre commit hooks
	pre-commit run --all-files

publish: build # publishes library to PyPI
	twine upload --verbose -u '__token__' dist/*
