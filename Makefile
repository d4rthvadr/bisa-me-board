VENV_BIN := .venv/bin
PYTHON ?= $(VENV_BIN)/python
MANAGE := $(PYTHON) manage.py

.PHONY: help run test check migrate makemigrations shell superuser verify db-up db-down

help:
	@printf "Available targets:\n"
	@printf "  make db-up           Start the PostgreSQL container (detached)\n"
	@printf "  make db-down         Stop and remove the PostgreSQL container\n"
	@printf "  make run             Start the development server\n"
	@printf "  make test            Run the full test suite\n"
	@printf "  make check           Run Django system checks\n"
	@printf "  make migrate         Apply database migrations\n"
	@printf "  make makemigrations  Create new migrations for the board app\n"
	@printf "  make shell           Open the Django shell\n"
	@printf "  make superuser       Create a Django superuser\n"
	@printf "  make verify          Run the standard pre-commit verification sequence\n"

db-up:
	docker compose up -d db

db-down:
	docker compose down

run:
	$(MANAGE) runserver

test:
	$(MANAGE) test

check:
	$(MANAGE) check

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations board

shell:
	$(MANAGE) shell

superuser:
	$(MANAGE) createsuperuser

verify:
	$(MANAGE) check
	$(MANAGE) migrate --run-syncdb
	$(MANAGE) test