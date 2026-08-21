# ADR 0001: Use Django Templates + HTMX for the MVP

- Status: Accepted
- Date: 2026-08-18

## Context
We want a lean, end-to-end Q&A board that demonstrates Django competence with a small footprint and a fast prototype path. The original idea of using React added framework setup, client/server coordination, and maintenance overhead, which conflicts with the goal of learning Django fundamentals and shipping quickly.

We also need a UI pattern that feels interactive without introducing a full SPA architecture or API-first complexity.

## Decision
Use Django Templates with HTMX for the MVP board.

This means:
- server-rendered Django templates for the main UI
- HTMX for lightweight partial refreshes and interaction flows
- SQLite for the initial prototype and local dev
- no React, no full SPA, and no separate API layer for v1

## Consequences
### Positive
- Faster to scaffold and understand end-to-end
- Less frontend complexity and fewer moving parts
- Good fit for learning Django fundamentals and server-rendered patterns
- Easy to keep the prototype lean and debuggable

### Negative
- The UX is less dynamic than a modern SPA
- Some interactions are more server-roundtrip oriented
- It is not the best long-term architecture for a highly interactive product

## Related artifacts
- Product spec: ../qna-board-spec.md
- Prototype plan: /memories/session/plan.md
