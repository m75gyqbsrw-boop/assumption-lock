# assumption-lock

`assumption-lock` is a deliberately small Python library and CLI for making engineering assumptions explicit, owned, reviewable, and enforceable in CI.

## What problem it solves

Engineering assumptions often live in comments, tickets, ADRs, Slack threads, or team memory. `assumption-lock` keeps those assumptions in code so they can be checked and reviewed.

## Install

```bash
pip install -e .
```

## Minimal library example

```python
from assumption_lock import assume

assume(
    "payments.stripe_webhook_latency",
    that=lambda: p95_webhook_delay_seconds() < 30,
    owner="payments-team",
    expires="2026-09-01",
    evidence="runbook:payments/webhooks",
    severity="fail",
)
```

Importing a module registers assumptions. Predicates are stored at registration time and only executed when checks are run explicitly.

## CLI examples

```bash
assumption-lock check --module my_app.assumptions
assumption-lock scan .
assumption-lock report --module my_app.assumptions --format markdown
assumption-lock report --module my_app.assumptions --format json
```

## CI example

```bash
pip install -e .
pytest
assumption-lock check --module my_app.assumptions
```

Use `severity="fail"` for assumptions that should fail CI and `severity="warn"` for assumptions that should remain visible without forcing a non-zero exit code.

## Runtime check vs static scan

- Runtime check imports only the modules you explicitly pass, registers assumptions, validates metadata, and optionally executes predicates.
- Static scan parses Python files with `ast` and finds simple `assume(...)` calls without importing application code.

## Known v0.1 limitations

- Static scan only extracts literal string names from simple calls such as `assume("name")` and `assumption_lock.assume("name")`.
- Static scan does not resolve aliases, dynamic variables, or indirect wrappers.

## Guidance

Keep assumptions in a dedicated `assumptions.py` file when possible so runtime imports stay explicit and easy to review.

## Non-goals for v0.1

- Web UI
- Database
- Background daemon
- Slack, Jira, or GitHub app integrations
- Auto-discovery that imports arbitrary application modules