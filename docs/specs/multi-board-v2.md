# QnA Board — Multi-Board V2 Spec

**Date:** 2026-08-26
**Status:** Draft for review

---

## Summary

Evolve the current single-board MVP into a lean multi-board application.

Each board is owned by an authenticated user. Owners can create and manage boards. Participants remain anonymous and can join a board by visiting its public URL. Boards support question submission, upvote-only voting, owner moderation, and simple live updates using HTMX polling.

This is intentionally a small product step, not a full event platform. The goal is to add ownership and multiple boards without taking on participant accounts, WebSockets, analytics, or complex permissions.

---

## Why This Is V2

The current MVP is explicitly single-board and anonymous by ADR 0002. This v2 changes core assumptions:

- one deployment can host many boards
- board owners authenticate
- questions belong to boards
- moderation becomes board-owner authorization, not a global staff-only concern
- board URLs are public entry points
- live board updates become part of the product surface

This means v2 is a product-shape change, not a template-only enhancement.

---

## Product Goals

A successful v2 should support this end-to-end flow:

1. An owner signs up and signs in.
2. The owner creates a board.
3. The system generates a public board URL with a random code.
4. Anonymous participants visit that URL and submit questions.
5. Anonymous participants upvote questions on that board.
6. The owner manages only their own board's questions.
7. The public board updates as new questions and votes arrive via simple polling.
8. The owner can close the board so it remains viewable but no longer accepts new questions or votes.

---

## Core Product Decisions

### Board model

The app becomes multi-board.

- a `Board` belongs to a Django `User`
- a `Question` belongs to a `Board`
- a board has a random public code used in the URL
- a board has a lifecycle state at minimum: `active` and `closed`

### Authentication boundary

Only board owners authenticate.

- owners can sign up, sign in, sign out
- participants do not need accounts
- participants access boards by URL only
- posting and voting remain anonymous

### Public board URL

Each board gets a random public code.

- URL shape: `/b/<code>/`
- code should be at least 8 lowercase alphanumeric characters
- code must be unique
- human-readable slugs are out of scope for the first cut

### Voting model

Voting stays anonymous and browser-scoped.

- keep browser token deduplication
- uniqueness remains per question and voter token
- no participant account model is introduced

### Moderation model

Moderation becomes owner-scoped.

- owners can moderate only boards they own
- existing question states remain useful: `active`, `hidden`, `archived`
- existing staff-only moderation should be replaced or clearly demoted once owner moderation exists

### Realtime model

Use HTMX polling, not SSE or WebSockets.

- polling updates only the question list region
- polling refreshes new questions, vote counts, and ordering
- flash messages and owner controls do not need live refresh in the first cut

### Board closure

Board closure is soft.

- a closed board remains viewable at its public URL
- participants can still read questions
- submitting and voting are disabled while closed
- reopening is optional and can be deferred if needed

---

## Domain Model

### Board

Minimum fields:

- `owner`
- `title`
- `code`
- `status`
- `created_at`
- `updated_at`

Minimum rules:

- `code` is unique and immutable after creation
- `status` defaults to active
- owner can edit title
- owner can close the board

### Question

Changes from MVP:

- add foreign key to `Board`
- existing question state machine remains
- board page only shows active questions to participants

### Vote

No major structural change required.

- votes remain tied to a question
- duplicate vote prevention still uses the browser token
- current uniqueness model remains adequate because uniqueness is already scoped through the question

---

## User Roles

### Owner

Can:

- sign up and sign in
- create a board
- view a list of owned boards
- open a board management page
- edit board title
- close a board
- moderate questions on owned boards
- copy or share the public board URL

Cannot:

- manage boards owned by other users

### Anonymous participant

Can:

- visit a public board URL
- view active questions on that board
- submit a question while the board is active
- vote once per question from the current browser
- see the board update as new votes and questions arrive

Cannot:

- create boards
- moderate questions
- post or vote on closed boards

---

## URL Model

### Public URLs

- `/b/<code>/` — public board page
- `/b/<code>/questions/new/` — create question on that board
- `/b/<code>/questions/<id>/vote/` — vote on a question in that board
- `/b/<code>/questions/` or similar fragment endpoint — HTMX polling target for question list refresh

### Owner URLs

- `/accounts/sign-up/`
- `/accounts/sign-in/`
- `/accounts/sign-out/`
- `/boards/` — list owned boards
- `/boards/new/` — create board
- `/boards/<id>/` — owner board detail/manage page
- `/boards/<id>/edit/` — edit title if separated from detail page
- `/boards/<id>/close/` — close board action
- `/boards/<id>/questions/<id>/state/` — owner moderation POST route

### Root URL

Preferred first cut:

- `/` becomes a landing page with sign-in, sign-up, and a short product description

Alternative:

- `/` redirects authenticated owners to `/boards/`

This can be decided during implementation, but `/` should stop being the public board itself once the app becomes multi-board.

---

## UX Boundaries

### Public board

The public board page should remain lean.

- title at the top
- question form visible while board is active
- closed-state message visible when board is closed
- active questions only
- vote button state visible for the current browser
- polling refresh limited to the question list area

### Owner surface

The owner surface should not become a dashboard product.

Minimum UI:

- board list
- create board form
- board detail/manage page
- question moderation actions
- board close action
- visible public URL for sharing

---

## Authorization Rules

- owner-only pages require login
- owner-only actions require ownership checks, not just authentication
- participants never access owner routes
- public board routes must verify the board exists by code
- vote and submit actions must verify the target board is active
- owner moderation must verify the question belongs to the owner’s board

---

## HTMX / Live Update Strategy

Keep the existing server-rendered pattern.

- the public board renders normally on first load
- a polling region refreshes only the question list HTML
- the question list endpoint returns HTML partials only
- no separate JSON API is introduced
- no SSE or WebSocket infrastructure is introduced

Polling interval should be conservative, for example every 5 seconds, until there is a demonstrated need to tighten it.

---

## Migration Impact

This v2 requires schema and route changes.

Expected database changes:

- add `Board` model
- add `Question.board_id`
- potentially update question uniqueness, query filters, and moderation lookups to be board-aware
- existing question and vote data may need a one-time migration path or can be discarded if this remains prototype-only

Expected code changes:

- root routing changes
- board views become board-scoped
- moderation authorization logic changes from staff-based to ownership-based
- tests need board-aware fixtures throughout

---

## Recommended Execution Order

Use a parent integration branch and implement these as separate vertical slices.

```text
feat/multi-board-v2
├── feat/boards-foundation
├── feat/owner-auth
├── feat/owner-moderation
├── feat/board-close-state
└── feat/live-polling
```

### 1. `feat/boards-foundation`

Scope:

- add `Board`
- attach questions to boards
- move public board from `/` to `/b/<code>/`
- make board-scoped question creation and voting work

Why first:

Everything else depends on board identity existing in the domain model.

### 2. `feat/owner-auth`

Scope:

- sign-up, sign-in, sign-out
- owner board list
- create board
- owner board detail page scaffold

Why second:

Owner flows can now operate against a real board model.

### 3. `feat/owner-moderation`

Scope:

- replace staff-only moderation with board-owner authorization
- restrict owner actions to owned boards only
- add moderation controls to owner board detail page

Dependency:

- depends on `boards-foundation`
- depends on `owner-auth`

### 4. `feat/board-close-state`

Scope:

- add close action and closed-state rendering
- disable question submission and voting on closed boards

Dependency:

- depends on `boards-foundation`
- owner action surface is easier once `owner-auth` exists

### 5. `feat/live-polling`

Scope:

- add HTMX polling for question list updates on the public board
- refresh ordering, new questions, and vote counts

Dependency:

- depends on `boards-foundation`
- can be implemented independently from owner moderation once the public board is board-scoped

### Integration order

A safe integration order is:

1. `boards-foundation`
2. `owner-auth`
3. `owner-moderation`
4. `board-close-state`
5. `live-polling`

`board-close-state` and `live-polling` can run in parallel after `boards-foundation`, but the parent integration branch should absorb them only after their dependencies are green.

---

## Testing Strategy

Prefer behavior tests at the view and route boundary.

### High-value tests

- owner can sign up and sign in
- owner can create a board and gets a public code URL
- public board by code shows only that board’s active questions
- question submit creates a question on the addressed board only
- vote on one board does not affect another board
- owner cannot manage another owner’s board
- owner can moderate only questions belonging to owned boards
- closed board rejects submit and vote actions
- HTMX polling endpoint returns only the question list partial for the target board

### Testing seam preference

Keep using Django `TestCase` at the view level where possible.

- route + request + response behavior
- database state changes
- ownership and permission checks
- no heavy client-side testing needed for the first cut

---

## Out of Scope

- participant accounts
- invite systems
- private boards or access control by password
- analytics or reporting dashboards
- tagging, search, or filtering
- WebSockets
- SSE if polling is good enough
- notifications
- email verification
- board themes or branding
- multi-owner or team-managed boards
- audit logs
- production deployment hardening beyond current basics

---

## Risks

- adding auth and board ownership can bloat the project if the owner UI becomes a dashboard product
- replacing single-board assumptions will ripple through tests and routing
- polling is simpler than SSE, but still adds ongoing request traffic and template branching
- owner moderation and staff moderation can conflict if both are left active without a clear precedence model

---

## Recommended Follow-Up After Spec Review

1. Add a new ADR that supersedes or narrows ADR 0002 for v2.
2. Create a parent integration branch such as `feat/multi-board-v2`.
3. Split implementation into the five slices above.
4. Review each slice before merging it into the parent branch.
5. Merge the parent branch into `main` only after integration testing passes.
