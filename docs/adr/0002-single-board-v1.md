# ADR 0002: Scope the MVP to a Single Board With Simple Moderation

- Status: Accepted
- Date: 2026-08-18

## Context
The goal is to build a lean Q&A board that demonstrates Django expertise without turning into a full event platform. There are multiple tempting features that improve realism but also increase hidden complexity: rooms, multi-session flows, real-time updates, authentication, spam prevention, and analytics.

For a prototype-first build, those features would distract from the core learning objective and slow the path to a working end-to-end system.

## Decision
Limit the MVP to a single board and a lightweight moderator workflow.

This means:
- one board per event, not multiple rooms
- anonymous posting with nickname, not user accounts
- one vote per browser per question, not a full identity system
- moderation via simple host controls (hide/archive), not a complex permissions system
- no realtime WebSocket layer in v1

## Consequences
### Positive
- much smaller surface area for the prototype
- faster delivery of an end-to-end demo
- easier to reason about data model and behavior
- better fit for a learning-focused Django project

### Negative
- not representative of a production event platform
- anonymous and minimal-moderation behavior is intentionally limited
- future extension to multiple rooms or auth will require a more deliberate redesign

## Related artifacts
- Product spec: ../qna-board-spec.md
- ADR 0001: 0001-django-templates-htmx.md
- Session plan: /memories/session/plan.md
