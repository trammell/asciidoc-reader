
.PHONY: test

lint:
	poetry run isort asciidoc_reader.py
	poetry run black asciidoc_reader.py
	poetry run bandit -q --severity-level medium asciidoc_reader.py
	poetry run pydocstyle asciidoc_reader.py
	poetry run flake8

test:
	poetry run pytest -vv
