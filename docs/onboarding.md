# Onboarding

## Install

```bash
git clone <private-repo-url>
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
```

The setup flow writes `.env`. It does not edit Surge profiles.

## First Checks

```bash
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

If `tick` prints `{"wakeAgent": false}`, the guardian is healthy and quiet.

## Hermes

Use the command printed by setup to create a one-minute Hermes cron job. The job
should run the script from this repository and use the prompt in
`hermes/job-prompts/guardian.md`.

## Common Mistakes

- Do not commit `.env`.
- Do not paste real subscription URLs into issues or docs.
- Do not turn temporary rules into permanent profile edits without reviewing why they were needed.
- Do not use a weak model for the analysis job if you expect autonomous reasoning.

