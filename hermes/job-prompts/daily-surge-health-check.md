# Daily Surge Health Check

Run the repository health-check script.

Behavior:

- If it exits 0 with no output, stay silent.
- If it prints a warning or error summary, send that summary to the operator.
- Do not add extra commentary for healthy runs.
- Do not change Surge profiles, policy groups, DNS, certificates, servers, or permanent rules without confirmation.
