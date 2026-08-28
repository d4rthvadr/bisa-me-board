# QnA Board

A lean Django + HTMX prototype for a Q&A board inspired by Slido.

## What this is

This project is a minimal end-to-end prototype for a single-board Q&A experience:

- anonymous submission with nickname
- question listing
- upvote-only voting
- ordering by highest votes, then newest
- duplicate-vote prevention by browser token
- simple Django server-rendered UI using HTMX

## Tech stack

- Python 3.8+
- Django 4.2
- PostgreSQL 16 (via Docker for local development)
- HTMX for lightweight UI updates

## Project structure

- `qna_board/` — Django project settings and root config
- `board/` — app with models, views, routes, templates, and tests
- `docs/` — specs, ADRs, and handoff notes

## Local run

### Prerequisites

- Docker (for PostgreSQL)
- Python 3.8+ with a virtual environment

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy env template and fill in your values
cp .env.example .env

# 3. Start the PostgreSQL container
make db-up

# 4. Apply migrations
make migrate

# 5. Start the dev server
make run
```

Then open:

```text
http://127.0.0.1:8000/
```

The Make targets use `.venv/bin/python` directly, so you do not need to activate the virtual environment manually if it exists at `.venv/`.

### Environment variables

Copy `.env.example` to `.env` and adjust as needed. The defaults in `.env.example` match the Docker Compose service, so no changes are required for local development.

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | *(required)* |
| `DJANGO_DEBUG` | Enable debug mode | `true` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `127.0.0.1,localhost` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `qna_board` |
| `DB_USER` | Database user | `qna_board` |
| `DB_PASSWORD` | Database password | `qna_board` |

## Tests

```bash
make test
```

Note: tests require the PostgreSQL container to be running (`make db-up`).

## Common commands

```bash
make help            # list available targets
make db-up           # start PostgreSQL container
make db-down         # stop PostgreSQL container
make check           # run Django system checks
make migrate         # apply database migrations
make makemigrations  # create migrations for the board app
make shell           # open Django shell
make superuser       # create an admin user
make verify          # check + migrate --run-syncdb + test
```

## Notes

This is intentionally a prototype-first MVP and not production-ready. The prototype is designed to validate the core loop quickly before expanding to moderation polish, environment hardening, or a larger system.
