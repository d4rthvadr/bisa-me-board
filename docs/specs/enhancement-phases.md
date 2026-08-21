# QnA Board — Enhancement Phases Spec

**Date:** 2026-08-21
**Status:** Ready for implementation

---

## Execution Order & Dependency Map

```
Phase 1a: feat/ui-polish       ─┐
                                 ├─► Phase 2b: feat/htmx-votes
Phase 1b: feat/env-hardening   ─┤
                                 └─► Phase 2a: feat/moderation-panel
```

- Phase 1a and 1b are **independent** — run in parallel worktrees.
- Phase 2a depends on 1b (needs `get_object_or_404` fix and validated inputs before adding more POST views).
- Phase 2b depends on 1a (HTMX swaps build on the polished template structure).
- Phase 2a and 2b are independent of each other once both Phase 1 slices have merged.

---

---

## Phase 1a — UI Polish

### Problem Statement

The board is fully functional but visually bare and unusable on mobile. A participant joining from a phone cannot comfortably submit a question or read the board. There is also no visual feedback after casting a vote, so participants cannot tell whether their vote registered without counting manually.

### Solution

A single-pass UI improvement to `home.html` that makes the board readable on mobile, improves visual hierarchy on desktop, and communicates vote state to the participant without requiring JavaScript or a separate API call.

### User Stories

1. As a participant on a mobile device, I want the form fields to stack vertically and fill the screen width, so that I can type a question without zooming or scrolling horizontally.
2. As a participant on a mobile device, I want the question cards to be readable at normal font size, so that I can read others' questions without pinching.
3. As a participant, I want a clear visual difference between the nickname/timestamp and the question body, so that I can scan the board quickly.
4. As a participant, I want the vote button to appear disabled after I have already voted on a question, so that I know my vote was counted and I am not tempted to click again.
5. As a participant, I want the vote button label to change (e.g. "Voted") after I have already voted, so that the state is clear without relying on colour alone.
6. As a participant, I want adequate spacing between question cards, so that the board does not feel cramped during a live event.
7. As a host, I want the board to look presentable when projected on a screen, so that the audience can read questions from a distance.

### Implementation Decisions

- Vote button state is driven server-side. `board_home` reads the `board_voter` cookie and queries `Vote.objects.filter(voter_token=token).values_list('question_id', flat=True)` to build a `voted_ids` set. This set is passed into the template context. No JavaScript state management is needed.
- The template uses `{% if question.id in voted_ids %}` to disable the button and swap the label. The `disabled` attribute on the `<button>` is sufficient for the PRG flow — the browser will not submit a disabled button's form.
- All styling is added to the `<style>` block in `home.html`. No inline `style=""` attributes. No external CSS file introduced in this phase.
- No changes to URL patterns, model, or migrations.

### Testing Decisions

Good tests check external behaviour: what the view returns in context and what the template renders, not how the queryset is built.

- Test that `board_home` includes a `voted_ids` key in the context.
- Test that a question the current voter has already voted on has its ID present in `voted_ids`.
- Test that a question the current voter has not voted on is absent from `voted_ids`.
- Prior art: `QuestionBoardTests.test_same_browser_can_only_vote_once_per_question` in `board/tests.py` — same cookie-passing pattern applies.
- Visual layout correctness is not covered by `TestCase`; manual verification on a mobile viewport is sufficient for this phase.

### Out of Scope

- HTMX partial swaps (Phase 2b).
- Dark mode or theming.
- Animations or transitions.
- Any backend view or model changes beyond the `voted_ids` context addition.

---

---

## Phase 1b — Environment Hardening

### Problem Statement

The codebase has a hardcoded `SECRET_KEY` in `settings.py`, `DEBUG=True` with no production path, and a bare `Question.objects.get()` call in `vote_question` that raises an unhandled 500 if the question ID is invalid. The `create_question` view silently drops the POST if inputs are blank instead of returning a validation error the participant can act on. The `admin.py` file contains an unused scaffold stub comment. These issues make the code unsuitable for production-quality review.

### Solution

Harden the environment configuration, fix the 404 gap, add backend input validation with visible error feedback, and register models in admin.

### User Stories

1. As a developer, I want `SECRET_KEY` loaded from a `.env` file, so that it is never committed to version control.
2. As a developer, I want a `.env.example` file in the repo, so that a new contributor knows which variables to set without reading the settings file.
3. As a developer, I want `DEBUG` controlled by a `DJANGO_DEBUG` environment variable, so that I can run the app in a production-like mode locally.
4. As a developer, I want `ALLOWED_HOSTS` loaded from an environment variable, so that the app does not rely on an open `[]` list outside of debug mode.
5. As a participant, I want a 404 response when I POST a vote to a question ID that does not exist, so that I see a clear error instead of a 500 crash page.
6. As a participant, I want an error message when I submit a question with a nickname longer than 50 characters, so that I know why my submission was rejected.
7. As a participant, I want an error message when I submit a question with body text longer than 500 characters, so that I know why my submission was rejected.
8. As a participant, I want form field errors to appear on the board page inline, so that I can correct my input without losing context.
9. As a host, I want `Question` and `Vote` visible in the Django admin, so that I can inspect and manage records during a live event.

### Implementation Decisions

- `python-dotenv` is the chosen loader — lighter than `django-environ`, no casting helpers needed for the variables in scope.
- `settings.py` reads `SECRET_KEY` with `os.environ` after loading `.env`. A missing key raises `ImproperlyConfigured` at startup rather than silently falling back to an insecure default.
- `vote_question` replaces `Question.objects.get(pk=question_id)` with `get_object_or_404(Question, pk=question_id)`. This is required by the Forbidden Patterns rule in the project conventions.
- `create_question` validates nickname ≤ 50 chars and text ≤ 500 chars after stripping. Validation failures use `messages.error` and redirect to `board:home` with the error displayed — keeping PRG intact and not introducing a form class in this phase.
- `admin.py` registers `Question` and `Vote` using `admin.site.register`. The scaffold stub comment is removed.
- No model changes. No new migrations.

### Testing Decisions

Good tests check external behaviour at the view boundary: HTTP status codes, redirect targets, message presence, and database state.

- Test that `vote_question` with a non-existent question ID returns 404.
- Test that `create_question` with a nickname over 50 chars returns a redirect and does not create a `Question`.
- Test that `create_question` with text over 500 chars returns a redirect and does not create a `Question`.
- Test that a validation failure results in an `error`-tagged message being present on the next response.
- Settings loading is not unit tested; `python manage.py check` with a valid `.env` present is sufficient.
- Prior art: all existing tests in `QuestionBoardTests` in `board/tests.py`.

### Out of Scope

- Static file serving (WhiteNoise or similar) — not needed until a deployment target is chosen.
- Database swap (Postgres) — SQLite is adequate until deployed.
- Rate limiting or spam protection.
- HTTPS enforcement settings.

---

---

## Phase 2a — Moderation Panel

_Depends on: Phase 1b merged._

### Problem Statement

The `Question` model already supports three states (`active`, `hidden`, `archived`) but there are no views or templates for a host to change question state. A host currently has no way to remove disruptive or off-topic questions from the board during a live event.

### Solution

Add a moderation panel — a separate Django-admin-protected route at `/manage/` — where the host can transition question states. Access is guarded by Django's built-in admin login so no bespoke auth logic is introduced.

### User Stories

1. As a host, I want a `/manage/` page that lists all questions grouped by state, so that I can see the full picture during an event.
2. As a host, I want to hide an active question with one click, so that it disappears from the participant board immediately.
3. As a host, I want to archive a hidden question, so that it is permanently removed from the active management view.
4. As a host, I want to restore an archived question to active, so that I can reverse a mistaken moderation action.
5. As a host, I want the moderation panel to require a login, so that participants cannot moderate each other's questions.
6. As a participant, I want hidden and archived questions to remain absent from the board after the host acts, so that the board stays on-topic.
7. As a host, I want each state-transition action to redirect back to `/manage/` after completing, so that I can keep moderating without navigating back.

### Implementation Decisions

- Access guard: the `/manage/` route uses Django's `@staff_member_required` decorator (or `@login_required` with an `is_staff` check). This reuses the Django admin session and login page — no new auth views needed.
- A superuser is created via `python manage.py createsuperuser` for local dev. This is documented in the README.
- State transition logic lives in a model method (e.g. `question.transition_to(state)`) that validates the allowed transitions, keeping views thin.
- Allowed transitions: `active → hidden`, `active → archived`, `hidden → active`, `hidden → archived`, `archived → active`. These match the spec.
- Moderation views are POST-only for state changes (PRG pattern). The GET for `/manage/` renders the management template.
- URL namespace stays `board`; moderation URLs are added under `board/urls.py`.
- No new models. No migrations.

### Testing Decisions

Good tests check state transitions and access control at the view boundary.

- Test that a GET to `/manage/` by an unauthenticated client redirects to the login page.
- Test that an authenticated staff user can transition `active → hidden` and the question is absent from the participant board.
- Test that an invalid state transition (e.g. `archived → hidden`) is rejected with a 400 or a no-op redirect.
- Test that the moderation page lists questions in each state bucket.
- Prior art: `QuestionBoardTests` — same `self.client.post` / redirect / database assertion pattern.

### Out of Scope

- Bulk moderation actions.
- Moderation audit log.
- Non-staff access tiers.
- Real-time push of moderation changes to participants (Phase 2b or later).

---

---

## Phase 2b — HTMX Partial Vote Updates

_Depends on: Phase 1a merged._

### Problem Statement

Every vote POST triggers a full-page reload. On a board with many questions this produces visible flicker and resets scroll position, which is disruptive during a live event where participants are actively watching the board.

### Solution

Replace the full-page reload on vote with an HTMX partial swap that re-renders only the question list. The PRG pattern is preserved — the vote view still redirects — and the same Django views are used without an API layer.

### User Stories

1. As a participant, I want the question list to update in place after I vote, so that my scroll position is not reset.
2. As a participant, I want to see the updated vote count immediately after voting, so that I have confirmation my vote was counted.
3. As a participant, I want the rest of the page (header, form) to remain stable while the list updates, so that the page does not flicker.
4. As a host projecting the board, I want the question order to visually update after votes without a full-page blink, so that the display looks stable on screen.

### Implementation Decisions

- The vote form uses `hx-post` targeting a named swap region (`id="question-list"`) in the template.
- `board_home` returns the full page for standard requests and a partial (`board/partials/question_list.html`) for HTMX requests, detected via `HX-Request` header.
- The partial template contains only the question list markup — extracted from `home.html` into `board/templates/board/partials/question_list.html`.
- `vote_question` returns an `HX-Redirect` response header pointing to `board:home` for HTMX requests, instead of a standard 302. This lets HTMX follow the redirect and swap in the refreshed list.
- `voted_ids` context logic (introduced in Phase 1a) is reused unchanged in the partial response.
- No new URL patterns. No model or migration changes.

### Testing Decisions

Good tests check that the correct response is returned for each request type, not implementation details of the HTMX header inspection.

- Test that a standard (non-HTMX) GET to `board:home` returns the full page template.
- Test that an HTMX GET to `board:home` (with `HTTP_HX_REQUEST=true`) returns only the partial template.
- Test that a vote POST with `HTTP_HX_REQUEST=true` returns an `HX-Redirect` header pointing to `board:home`.
- Prior art: `QuestionBoardTests` — same `self.client.post` / header assertion pattern, extended with custom `HTTP_HX_REQUEST` kwarg.

### Out of Scope

- SSE or WebSocket-based real-time score push to other participants.
- HTMX swaps for question submission form (a separate future slice).
- Optimistic UI updates.
- Polling intervals.
