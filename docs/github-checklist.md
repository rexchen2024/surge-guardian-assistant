# GitHub Release Checklist

Use this checklist before publishing a release or making the repository public.

## Repository

- README explains what the project does in the first screen.
- README includes install, requirements, update, feedback, license, and security links.
- `README.md` is Simplified Chinese by default.
- `README.zh-HK.md`, `README.zh-TW.md`, and `README.en.md` are present and linked from the homepage.
- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` are present.
- Issue templates and PR template are present.
- GitHub Actions check is passing.
- Release tag points to the intended commit.

## Privacy

- `.env` is ignored.
- No Surge profiles are committed.
- No subscription URLs, node credentials, request logs, DNS dumps, event dumps, real domains, real IPs, personal paths, or notification targets are committed.
- Sample config uses example values only.
- Screenshots or terminal snippets are reviewed before publishing.

## Validation

Run:

```bash
scripts/check
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant feedback --print
```

Then check:

```bash
git status --short
git tag --list
gh release list --repo rexchen2024/surge-guardian-assistant --limit 5
```

## Messaging

Describe the project as a Surge guardian assistant, not a Surge profile or proxy subscription.

Keep the promise narrow:

- quiet healthy checks
- safe self-healing
- Hermes Edition for always-on monitoring
- Codex Edition for lower-frequency maintenance
- no automatic telemetry
- no permanent Surge changes without confirmation
