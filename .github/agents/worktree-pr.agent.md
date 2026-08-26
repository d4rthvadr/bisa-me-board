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
- Parent integration branches follow `feat/<initiative>` and collect reviewed sub-branches before anything reaches `main`
- Venv: `source <repo-root>/.venv/bin/activate`
- Tests require a `.env` in the worktree root (gitignored — user must create it)

---

## Worktree workflow

### 0. Create a parent integration branch first

Before opening parallel worktrees for a larger initiative, create one parent branch from `main`.

```bash
git checkout -b feat/<initiative>
git worktree add "../qna-board-<initiative>" feat/<initiative>
```

Then create each sub-branch from that parent branch, not from `main`.

```bash
git checkout feat/<initiative>
git branch feat/<slice>
git worktree add "../qna-board-<slice>" feat/<slice>
```

The parent branch is the integration target for reviewed work. `main` stays clean until the initiative is integrated and re-tested.

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
Next step options: merge to parent branch / hold / individual PR / stacked PR
```

Wait for explicit approval before proceeding.

### 3. If the human requests changes

Make the changes, re-run check + test, amend or add a new commit, and re-present the review block above.

### 4. On merge approval

Merge with `--no-ff` into the parent integration branch from the main repo directory:

```bash
git checkout feat/<initiative>
git merge --no-ff feat/<slice> -m "Merge feat/<slice>: <summary>"
```

After merging, run `python manage.py test` on the parent integration branch before touching the next branch.

### 5. Cleanup after a successful merge

Once a reviewed sub-branch is merged and the parent integration branch is green, clean up the worktree you just finished.

```bash
git worktree remove "../qna-board-<slice>"
```

If the branch is fully merged and no longer needed, ask the human whether to delete it locally and remotely. Do not delete branches without explicit approval.

### 6. Final integration to `main`

Only after the parent integration branch has absorbed its approved sub-branches and passed integration testing should it be merged into `main` or turned into a PR.

```bash
git checkout main
git merge --no-ff feat/<initiative> -m "Merge feat/<initiative>: <summary>"
```

Run `python manage.py test` on `main` after this final merge.

After the final merge is validated, remove the parent integration worktree as well. Ask before deleting the parent branch.

---

## PR creation

### Before creating any PR

1. Run `git worktree list` to confirm the branch and worktree path.
2. Run `python manage.py test` in the worktree — must be green.
3. Push: `git push -u origin feat/<slice>` from inside the worktree.
4. Confirm the push succeeded before opening a PR.

### Individual PR (parent integration branch → `main`)

Title: matches the parent branch goal and summarizes the integrated slices.

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

Create in dependency order — sub-branches target their dependency or parent branch first, not `main`.

| PR  | Head                    | Base                 |
| --- | ----------------------- | -------------------- |
| 1   | `feat/env-hardening`    | `feat/product-phase` |
| 2   | `feat/ui-polish`        | `feat/product-phase` |
| 3   | `feat/moderation-panel` | `feat/env-hardening` |
| 4   | `feat/htmx-votes`       | `feat/ui-polish`     |
| 5   | `feat/product-phase`    | `main`               |

Add to each PR body: "**Stack order:** PR #<n> must merge before this one."

After a dependency PR merges, rebase the dependent branch onto the updated parent branch or `main`, whichever is now the correct base.

```bash
git rebase <new-base>
git push --force-with-lease origin feat/<slice>
```

Then update the PR base branch on GitHub.

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
- Never merge a sub-branch directly into `main` when it belongs to a larger initiative; merge it into the parent integration branch first.
- After a merge and passing validation, remove the finished worktree before moving on.
