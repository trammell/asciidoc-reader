
.PHONY: test

lint:
	poetry run isort asciidoc_reader.py
	poetry run black asciidoc_reader.py
	poetry run bandit asciidoc_reader.py
	poetry run flake8

test:
	poetry run pytest
