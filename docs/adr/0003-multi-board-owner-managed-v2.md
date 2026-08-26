# ADR 0003: Evolve the MVP to a Multi-Board, Owner-Managed V2

- Status: Proposed
- Date: 2026-08-26

## Context
The current MVP proved the core Q&A loop with a single board, anonymous participation, and lightweight moderation. That scope was the right first cut for learning-focused delivery and is captured in ADR 0002.

The next product step needs to support more realistic usage without taking on the full complexity of a production event platform. Specifically, the application now needs multiple boards in one deployment, board ownership, owner sign-up and sign-in, public board URLs that participants can visit directly, and simple live updates as new questions and votes arrive.

At the same time, the project still needs to remain lean:
- participants should remain anonymous
- the app should stay server-rendered
- HTMX should remain the interactivity layer
- real-time infrastructure should stay simple
- permissions should stay narrow and board-scoped

## Decision
Evolve the product from a single-board MVP to a multi-board, owner-managed v2.

This means:
- one deployment can host many boards
- each board belongs to an authenticated owner using Django's built-in `User` model
- owners can sign up, sign in, sign out, create boards, and manage only their own boards
- participants remain anonymous and can join a board by visiting its public URL
- each board gets a unique random public code, with URLs shaped like `/b/<code>/`
- questions belong to boards
- voting remains browser-token based and anonymous
- moderation becomes board-owner scoped instead of global staff-only workflow
- board closure is soft: the board remains viewable, but posting and voting are disabled
- live updates use HTMX polling for the question list only
- ADR 0001 remains in force: server-rendered Django templates plus HTMX, no SPA, no separate API layer
- ADR 0002 remains historically correct for the MVP, but its single-board and no-auth assumptions are superseded for v2

## Consequences
### Positive
- supports many boards without requiring a separate deployment per event
- introduces ownership without forcing participant accounts
- keeps the public participation flow simple and low-friction
- preserves the Django Templates + HTMX architecture
- keeps real-time behavior operationally simple by using polling instead of WebSockets
- creates a path toward a more realistic product while staying within a lean scope

### Negative
- requires a schema change by introducing `Board` and attaching `Question` to it
- replaces several single-board assumptions in routing, tests, and authorization
- adds authentication, which increases product and codebase complexity
- owner moderation and legacy staff moderation can conflict unless one becomes the clear primary path
- polling adds repeated requests and partial-template paths that need to stay consistent

## Related artifacts
- ADR 0001: 0001-django-templates-htmx.md
- ADR 0002: 0002-single-board-v1.md
- V2 spec draft: ../specs/multi-board-v2.md
