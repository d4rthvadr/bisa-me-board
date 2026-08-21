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
- SQLite for local development
- HTMX for lightweight UI updates

## Project structure

- `qna_board/` — Django project settings and root config
- `board/` — app with models, views, routes, templates, and tests
- `docs/` — specs, ADRs, and handoff notes

## Local run

```bash
cd "/Users/mac/Documents/Ghost rider/frontend masters/playwright-pg/qna-board"
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## Tests

```bash
cd "/Users/mac/Documents/Ghost rider/frontend masters/playwright-pg/qna-board"
source .venv/bin/activate
python manage.py test
```

## Notes

This is intentionally a prototype-first MVP and not production-ready. The prototype is designed to validate the core loop quickly before expanding to moderation polish, environment hardening, or a larger system.
