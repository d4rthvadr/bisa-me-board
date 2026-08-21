# QnA Board MVP Spec

## Status

Draft for prototype-first implementation.

## Summary

Build a lean, single-board Q&A application inspired by Slido, implemented with Django Templates + HTMX. The MVP should let anonymous users submit questions, vote on them, and display them in ranked order. A host can hide or archive questions using a simple moderator workflow. The goal is to validate end-to-end Django fundamentals without introducing a React frontend or production-grade auth.

## Related Artifacts

- Session plan: /memories/session/plan.md
- Handoff notes: /Users/mac/.vscode/tmp/tmp_vscode_11/qna-board-handoff-2026-08-18.md

## Product Goal

Create a working prototype that proves a complete board loop end-to-end in one short iteration:

- a user can type a question and nickname
- the question is saved and appears on the board
- other users can upvote it
- the board remains sorted by popularity
- a host can hide or archive entries

## Scope

### In scope

- Single board / one event feed
- Anonymous submission with nickname
- Upvote-only voting
- Question ordering: most votes, then newest
- Question states: active, hidden, archived
- Host moderation via simple secret-based access guard
- Local development via Django + SQLite + Docker Compose
- HTMX-driven server-rendered interactions

### Out of scope

- Multi-room sessions
- Authentication and user accounts
- Real-time WebSockets
- Spam protection / rate limiting
- Search, tagging, analytics, or reporting dashboards
- React frontend or SPA architecture
- Production deployment hardening

## User Roles

### Anonymous participant

- Can submit a question with a nickname and message
- Can view the active board
- Can upvote a question once per browser
- Cannot moderate or change state

### Host / moderator

- Can hide an active question
- Can archive a hidden or active question
- Can restore an archived question to active state
- Uses a minimal secret-based access control for a local prototype

## Functional Requirements

### 1. Submit a question

A user enters:

- nickname (required)
- question text (required, bounded length)

Validation:

- nickname must be non-empty
- question text must be non-empty and trimmed
- content must not be excessively long for v1

Result:

- question is saved with default state: active
- question appears in the board list with initial vote count of 0

### 2. View the board

The board shows active questions only.

Default ordering:

1. highest vote count
2. newest questions first within equal vote totals

Each item includes:

- nickname
- text
- vote count
- created timestamp
- action controls for vote and moderation

### 3. Upvote a question

A user can upvote a question from the board.

Rules:

- one vote per browser per question
- duplicate votes from the same browser are rejected
- vote count increments immediately after successful action

Implementation approach for v1:

- generate a browser fingerprint token in a cookie or session value
- use a unique constraint on question + voter token

### 4. Moderate questions

Host actions:

- hide question
- archive question
- unarchive question

Rules:

- moderation actions are only allowed for authorized host access
- actions update the question state without deleting the record
- hidden and archived questions are not shown in the active board

### 5. Local prototype flow

The app must run locally with one common command path using Docker Compose, or a simple Django manage.py runserver flow if Compose is too heavy for the prototype.

## Data Model

### Question

Fields:

- id
- nickname
- text
- state (active | hidden | archived)
- vote_count
- created_at
- updated_at

### Vote

Fields:

- id
- question_id
- voter_token
- created_at

Constraints:

- unique together on question_id + voter_token

## User Experience Requirements

- Minimal but readable page layout
- Form is immediately visible at top of page
- Questions are clearly separated and easy to scan
- Vote interaction is obvious and fast
- Hidden or archived questions are visually removed from the main board
- Host controls are distinct from participant controls

## Technical Requirements

### Stack

- Django
- Django Templates
- HTMX
- SQLite for prototype
- Python standard tooling only unless a clear need appears

### Architecture constraints

- Use server-rendered templates as the primary frontend pattern
- Avoid React or SPA structure for MVP
- Keep logic in Django views or lightweight service helpers, not ad hoc logic spread across templates
- Prefer a single app for prototype simplicity unless project grows clearly

### HTMX behavior

- use HTMX for partial refresh after question creation, voting, and moderation actions
- keep responses as HTML fragments where possible
- avoid adding a separate API layer in v1 unless there is a compelling need

## Acceptable Validation

Prototype is successful if all of the following are true:

1. A participant can create a question and see it appear in the board.
2. The board orders questions by vote count, then recency.
3. A browser cannot vote on the same question twice.
4. A moderator can hide or archive a question successfully.
5. The app runs from a clean local setup in a development environment without additional framework setup beyond Django and dependencies.

## Prototype Plan

Phase 1 should focus only on the tracer-bullet flow:

1. Scaffold Django project and board app
2. Create models for Question and Vote
3. Build board page with question form
4. Add HTMX-based vote and hide workflow
5. Add duplicate vote prevention
6. Validate end-to-end with smoke tests

## Risks / Trade-offs

- The prototype may feel slightly less dynamic than a SPA, but it is the best fit for lean Django learning.
- Moderation via simple secret-based access is intentionally temporary and not production-safe.
- Anonymous voting without strong identity is acceptable for a prototype but not for production.

## Definition of Done for Prototype

The prototype is complete when:

- the app boots locally
- a user can submit a question
- the board updates after submission
- the question can be voted on
- duplicate votes are blocked
- the host can hide/archive through a simple admin path
- the manual flow is documented clearly enough to use in a short demo
