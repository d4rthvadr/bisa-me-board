# Copilot Instructions — QnA Board

## Project Overview

A lean single-board Q&A application inspired by Slido. Anonymous users submit questions with a nickname and upvote them. Questions are sorted by popularity. A host can hide or archive questions via a minimal secret-based guard. No auth, no WebSockets, no SPA.

**Status:** prototype-first MVP. Validate the core loop before hardening.

---

## Stack & Versions

| Layer     | Technology                           | Version     |
| --------- | ------------------------------------ | ----------- |
| Runtime   | Python                               | 3.8         |
| Framework | Django                               | 4.2.30      |
| UI        | Django Templates + HTMX              | HTMX 1.9.12 |
| Database  | SQLite (local dev)                   | —           |
| Tests     | Django `TestCase` (`manage.py test`) | —           |

---

## Architecture

```
qna_board/          Django project config (settings, root urls, wsgi/asgi)
board/              Single Django app
  models.py         Question (state, vote_count) + Vote (unique per token+question)
  views.py          board_home / create_question / vote_question
  urls.py           app_name='board'; routes: / | questions/new/ | questions/<id>/vote/
  templates/board/  home.html — single server-rendered page
  tests.py          Django TestCase unit/integration tests
  migrations/       Managed by Django; never edit by hand
docs/
  qna-board-spec.md     Product spec
  adr/              Architecture decisions (ADRs 0001, 0002)
```

**Data flow:** every interaction is a standard POST → redirect (PRG pattern). HTMX can replace full-page POSTs with partial `hx-post` swaps on top of the same views.

**Vote dedup:** `board_voter` cookie (32-char hex token) + `UniqueConstraint` on `(question, voter_token)`. Duplicate votes are caught by `IntegrityError` inside `transaction.atomic()`.

**Question states:** `active` → `hidden` → `archived` (or `active`). Only `active` questions are shown on the board.

---

## Available Commands

```bash
# Activate venv first
source .venv/bin/activate

# Run dev server
python manage.py runserver              # http://127.0.0.1:8000/

# Run all tests
python manage.py test

# Run a single test class
python manage.py test board.tests.QuestionBoardTests

# Apply migrations
python manage.py migrate

# Create a new migration after model changes
python manage.py makemigrations board

# Open Django shell
python manage.py shell

# Check for config/deployment issues
python manage.py check
```

---

## Verification Steps

After any change, run this sequence before committing:

1. `python manage.py check` — zero errors
2. `python manage.py migrate --run-syncdb` — no unapplied migrations
3. `python manage.py test` — all tests green
4. Manually hit `http://127.0.0.1:8000/` and submit a question + vote

For view changes, also verify:

- POST → 302 redirect (PRG pattern preserved)
- HTMX swap target renders correctly without a full-page reload

---

## Lean Best Practices

- **One app, one board.** Do not add multi-room or multi-board logic in v1.
- **PRG everywhere.** Every POST view must redirect; never return a rendered response from a POST.
- **Thin views.** Business logic belongs in model methods or standalone functions, not in views.
- **Minimal template logic.** No Python-style computation in templates; derive values in the view.
- **Atomic votes.** Always wrap `Vote.create` + `question.vote_count` increment in `transaction.atomic()`.
- **Explicit `update_fields`.** When saving a partial model update, pass `update_fields` to avoid clobbering unrelated fields.
- **Cookie-based dedup only.** Do not add session auth or IP tracking for vote dedup in v1.
- **No dead code.** Remove view scaffolding stubs (`# Register your models here.`) when the file is actually used.

---

## Common Mistakes

| Mistake                                                               | Correct approach                                                           |
| --------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Returning `render()` from a POST view                                 | Always redirect after POST (`HttpResponseRedirect`)                        |
| Incrementing `vote_count` outside a transaction                       | Wrap in `transaction.atomic()` to prevent race conditions                  |
| Querying `Question.objects.all()` on the board                        | Filter by `state=Question.STATE_ACTIVE`                                    |
| Hardcoding ordering in a queryset differently from the model `Meta`   | Use the model's `Meta.ordering` or be explicit and consistent              |
| Creating a `Vote` without checking the cookie first                   | Always call `_get_or_create_voter_token(request)` before creating a vote   |
| Setting `max_age` on the voter cookie inside the view that _reads_ it | Only set the cookie on the response from `vote_question`, not `board_home` |
| Editing migration files by hand                                       | Always use `makemigrations`; never edit generated migration files          |
| Adding `SECRET_KEY` or credentials to source control                  | Keep secrets in `.env` and out of `settings.py` for any non-throwaway env  |

---

## Forbidden Patterns

- **No React / SPA.** All rendering is server-side Django templates. HTMX handles interactivity.
- **No WebSockets / channels in v1.** Real-time is out of scope per ADR 0002.
- **No user authentication.** Anonymous posting only; do not add `django.contrib.auth` flows.
- **No multi-board logic.** There is one board per deployment. Do not add `Board` or `Room` models in v1.
- **No raw SQL.** Use the Django ORM exclusively.
- **No `get_object_or_404` bypass.** When looking up by PK in views, use `get_object_or_404` (or handle `DoesNotExist`) — never a bare `.get()` that can raise an unhandled 500.
- **No inline styles in new templates.** Add CSS to the `<style>` block in `home.html` or a static file; do not use `style=""` attributes on new elements.
- **No unstaged `db.sqlite3` commits.** The database file is `.gitignore`d; never force-add it.

---

## Key URL Names (app namespace `board`)

| Name                    | Method | Purpose                      |
| ----------------------- | ------ | ---------------------------- |
| `board:home`            | GET    | Show board + submission form |
| `board:create_question` | POST   | Submit a new question        |
| `board:vote_question`   | POST   | Cast an upvote               |

Use `{% url 'board:home' %}` in templates and `reverse('board:home')` in views.

---

## ADR Summary

- **ADR 0001** — Django Templates + HTMX (no React, no SPA, no separate API layer)
- **ADR 0002** — Single board MVP with anonymous posting and simple moderation; no WebSockets, no auth, no multi-room in v1

---

## Parallel Worktree Work

When doing parallel worktree development or creating PRs from feature branches, use the `worktree-pr` skill. Always pause for human review before merging any worktree branch, merge reviewed sub-branches into a parent integration branch instead of directly into `main`, and clean up merged worktrees after validation.
