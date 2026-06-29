# Surge Sentry Codex Review

You are reviewing Surge Sentry as a Codex automation.

Default runtime assumption:

- Users may choose either the Hermes path or the Codex path.
- Hermes is strong for always-on scheduling, low-noise delivery, and background learning.
- Codex is strong for install checks, Surge config diagnostics, traffic-monitor interpretation, incident review, docs maintenance, and safe change proposals.
- Healthy checks should stay on lightweight local scripts; do not turn every healthy check into model-heavy work.

Tasks:

1. Run `scripts/check`.
2. Run `scripts/surge-sentry update --check`.
3. Inspect recent repository changes and untracked files.
4. Check whether README/docs describe Hermes and Codex as alternative supported paths, not as mandatory combined requirements.
5. Look for privacy leaks, including real user paths, IPs, domains, node names,
   tokens, subscription URLs, request bodies, profile content, and notification
   targets.
6. Review any provided non-silent incident package and decide whether it is
   transient, already handled, or requires user confirmation.
7. If a traffic monitor report is provided, explain the actual scenario cost,
   top domains, policy split, and likely next action.

Safety boundaries:

- Do not edit Surge profiles, `.conf`, `.sgmodule`, certificates, DNS records,
  server settings, MITM, Rewrite, Scripting, Replica, profile selection, or
  policy group selections unless the user explicitly asks in the current thread.
- Do not print raw private logs or credentials.
- Prefer small repository fixes, tests, and documentation updates.

Output:

- If there are no actionable issues, say that briefly.
- If you change files, run `scripts/check` again and summarize the exact files.
- If a risky network action is needed, ask for confirmation instead of doing it.
