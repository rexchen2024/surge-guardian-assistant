# Surge 守护助手 Codex Review

You are reviewing Surge 守护助手 as a Codex automation.

Default runtime assumption:

- Hermes remains the recommended production scheduler and notification layer.
- Codex is a lower-frequency analysis and maintenance layer.
- Do not turn healthy minute-level checks into model-heavy work.

Tasks:

1. Run `scripts/check`.
2. Run `scripts/surge-guardian-assistant update --check`.
3. Inspect recent repository changes and untracked files.
4. Check whether README/docs still describe Hermes as the recommended runtime.
5. Look for privacy leaks, including real user paths, IPs, domains, node names,
   tokens, subscription URLs, request bodies, profile content, and notification
   targets.
6. Review any provided non-silent incident package and decide whether it is
   transient, already handled, or requires user confirmation.

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
