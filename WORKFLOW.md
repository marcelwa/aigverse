# Workflow

## When faced with larger work

This applies whether the task comes from a GitHub issue, PR review feedback, or
is assigned directly by the user — anything bigger than a quick one-off edit.
Don't freelance straight against `main`; follow this loop instead:

1. **Understand the task first.** If it originates from a GitHub issue, read it
   in full (`gh issue view <number>`, or the GitHub MCP tool if configured) —
   title, body, comments — before writing any code. If it's PR feedback, read
   the actual review comments, not just the diff. If it's assigned directly,
   make sure the ask is concrete before starting; ask the user rather than
   guessing at scope.
2. **Create a worktree on a new branch**, as a sibling of this checkout, scoped
   to the task:

   ```console
   git worktree add ../aigverse-<slug> -b <branch>
   ```

   All work happens on that branch — never directly on `main`. Name the sibling
   dir and branch after the task, e.g. `../aigverse-issue357` /
   `fix-issue-357-dup-po-targets`.
3. **Plan.** Hand the task off to a subagent whose only job is to draft an
   implementation plan — reading the relevant code, not writing any of it yet.
4. **Adversarially verify the plan.** Hand the plan to a second, fresh subagent
   whose only job is to attack it: wrong assumptions, missed edge cases, scope
   creep, violations of [AGENTS.md](AGENTS.md)'s conventions/Boundaries. Revise
   the plan in light of that critique before moving on.
5. **Implement.** Hand the revised plan to a fresh implementation subagent — no
   memory of the planning/critique conversation, just the approved plan — to
   build it in the worktree, following [AGENTS.md](AGENTS.md)'s conventions and
   Boundaries (lint, tests, stub regeneration after binding changes, etc.),
   committing incrementally.
6. **Adversarially verify the implementation.** Once a base version exists,
   have it reviewed against the actual diff, not the plan — either a fresh
   review subagent, or outsource this step to CodeRabbit (`cr --agent`, or its
   review comments on an open PR via the CodeRabbit MCP tool). Treat findings
   the same way regardless of which one raised them.
7. **Open a PR** (`gh pr create`), referencing the issue if there is one
   (`Fixes #<number>`), and iterate against CI / further CodeRabbit review
   until green.
8. **Clean up** once the task is done — the PR is merged, or the user says so:
   - `git worktree remove <path>` (run from this main checkout)
   - `git branch -d <branch>` — plain `-d`, not `-D`, so git itself refuses if
     the branch isn't actually merged
   - delete the remote branch too, if GitHub's "delete branch on merge" hasn't
     already done it

Don't skip the worktree, even for a small-looking fix — it keeps the task's
changes isolated from whatever else is in progress in the main checkout, and
keeps `main` clean for the next task.
