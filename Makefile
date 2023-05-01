
.PHONY: test

install:
	poetry install

format:
	poetry run black **/*.py
	poetry run isort **/*.py

lint:
	poetry run bandit -q --severity-level medium **/*.py
	poetry run pydocstyle **/*.py
	poetry run flake8 --per-file-ignores="__init__.py:F401" .
	poetry run mypy src/

test:
	poetry run pytest -rxXs --log-level=DEBUG
