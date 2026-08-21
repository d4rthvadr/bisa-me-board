---
description: >
  Manages git worktree branches and GitHub PRs for the QnA Board project.
  Use when doing parallel feature work in worktrees, creating individual PRs,
  creating stacked PRs where branches depend on each other, or pushing branches
  before PR creation. Enforces a human review gate before any merge.
tools:
  - run_in_terminal
  - mcp_github_mcp_se_create_pull_request
  - mcp_github_mcp_se_list_pull_requests
  - mcp_github_mcp_se_pull_request_read
  - mcp_github_mcp_se_update_pull_request
---

# Worktree PR Skill

You manage git worktree branches and GitHub pull requests for the QnA Board project.

## Repo root

`/Users/mac/Documents/Ghost rider/frontend masters/playwright-pg/qna-board`

## Conventions

- Worktrees live at `../qna-board-<slice>` relative to the repo root
- Branches follow `feat/<slice>`
- Venv: `source <repo-root>/.venv/bin/activate`
- Tests require a `.env` in the worktree root (gitignored — user must create it)

---

## Worktree workflow

### 1. Per-worktree: implement and commit

Work only inside the assigned worktree directory. Never touch sibling worktrees.

Before committing:

```bash
python manage.py check        # must be zero errors
python manage.py test         # must be all green
```

Commit format:

```
feat(<slice>): <short imperative summary>

- what changed and why (one bullet per logical change)
- new tests: <count> added, covering <what>
```

### 2. After committing: stop and present for review

Do NOT merge. Present this to the human:

```
Branch:  feat/<slice>
Commit:  <hash>  <message>
---
<git show <hash> --stat output>
---
Tests:   <before> → <after>
Manual checks needed: <list anything the human should verify in the browser>
Next step options: merge to main / hold / individual PR / stacked PR
```

Wait for explicit approval before proceeding.

### 3. If the human requests changes

Make the changes, re-run check + test, amend or add a new commit, and re-present the review block above.

### 4. On merge approval

Merge with `--no-ff` from the main repo directory:

```bash
git merge --no-ff feat/<slice> -m "Merge feat/<slice>: <summary>"
```

After merging, run `python manage.py test` on `main` before touching the next branch.

---

## PR creation

### Before creating any PR

1. Run `git worktree list` to confirm the branch and worktree path.
2. Run `python manage.py test` in the worktree — must be green.
3. Push: `git push -u origin feat/<slice>` from inside the worktree.
4. Confirm the push succeeded before opening a PR.

### Individual PR (branch → `main`)

Title: matches the branch's conventional commit summary (strip the `feat(<scope>): ` prefix for the PR title).

Body template:

```
## What
<one sentence>

## Why
Implements Phase <X> from [docs/specs/enhancement-phases.md](docs/specs/enhancement-phases.md).

## Tests
<N> new tests added: <brief description of what they cover>.
`manage.py test` — all green.

## Checklist
- [ ] `manage.py check` passes
- [ ] `manage.py test` passes
- [ ] Manual smoke test done
```

### Stacked PRs (branch B depends on branch A)

Create in dependency order — the base of each PR is its dependency branch, not `main`.

| PR  | Head            | Base            |
| --- | --------------- | --------------- |
| 1   | `feat/phase-1b` | `main`          |
| 2   | `feat/phase-2a` | `feat/phase-1b` |

Add to each PR body: "**Stack order:** PR #<n> must merge before this one."

After PR 1 merges into `main`, rebase PR 2:

```bash
git rebase main feat/phase-2a --onto main
git push --force-with-lease origin feat/phase-2a
```

Then update PR 2's base branch to `main` on GitHub.

### Dependency map for this project

```
feat/env-hardening  ──► feat/moderation-panel
feat/ui-polish      ──► feat/htmx-votes
```

---

## Rules

- Never push directly to `main`.
- Never force-push a branch that already has an open PR without warning the user first.
- Never merge or close a PR — that is always the human's action.
- Never skip the review gate between commit and merge.
