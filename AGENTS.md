# Handoff And PR Rule

When a task changes code, Codex must finish with a PR handoff instead of asking the user to move files around.

Required closeout steps:

1. Run `git status --short` and identify only task-related files.
2. Do not use `git add .`.
3. Stage only related files, or call `scripts/codex-handoff-pr --files ...`.
4. Create or update `docs/handoff/<task-id>.md`.
5. Commit on a task branch.
6. Push the branch and open a pull request.
7. Final response must include the PR link and the handoff file path.

The handoff must say:

- What changed
- Which files changed
- What was verified
- Known risks or gaps
- What was intentionally not changed
- Recommended next action: merge, request changes, or continue work

The user should make the final merge decision. Codex can recommend a decision, but should not merge unless the user explicitly asks.
