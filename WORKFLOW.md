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
3. **Do the work** in the worktree, following [AGENTS.md](AGENTS.md)'s
   conventions and Boundaries (lint, tests, stub regeneration after binding
   changes, etc.), committing incrementally.
4. **Open a PR** (`gh pr create`), referencing the issue if there is one
   (`Fixes #<number>`), and iterate against CI / CodeRabbit review until green.
5. **Clean up** once the task is done — the PR is merged, or the user says so:
   - `git worktree remove <path>` (run from this main checkout)
   - `git branch -d <branch>` — plain `-d`, not `-D`, so git itself refuses if
     the branch isn't actually merged
   - delete the remote branch too, if GitHub's "delete branch on merge" hasn't
     already done it

Don't skip the worktree, even for a small-looking fix — it keeps the task's
changes isolated from whatever else is in progress in the main checkout, and
keeps `main` clean for the next task.
