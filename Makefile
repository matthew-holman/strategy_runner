requirements:
	poetry install --no-root --with dev
	# pre-commit install --install-hooks
	export BETTER_EXCEPTIONS=1

isort:
	pre-commit run --all isort

black:
	pre-commit run --all black

pycln:
	pre-commit run --all pycln

flake8:
	pre-commit run --all flake8

mypy:
	pre-commit run --all mypy

pytest:
	poetry run pytest tests --cov-config=.coveragerc --cov-fail-under=50 --cov=app --cov-report term-missing

run-all-pre-commit-hooks:
	pre-commit run --all

check: run-all-pre-commit-hooks pytest

## Commands for other projects local development environments
migrations:
	poetry run alembic upgrade head

start-db:
	docker-compose up -d db

main:
	poetry run python3 main.py

start: requirements start-db migrations main
