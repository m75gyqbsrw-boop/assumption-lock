# assumption-lock

`assumption-lock` is a deliberately small Python library and CLI for making engineering assumptions explicit, owned, reviewable, and enforceable in CI.

## What problem it solves

Engineering assumptions often live in comments, tickets, ADRs, Slack threads, or team memory. `assumption-lock` keeps those assumptions in code so they can be checked and reviewed.

## What is an assumption?

In this project, an assumption is a statement like:

> "We believe X is true, and this code depends on X."

Examples:

- "Webhook latency stays under 30 seconds"
- "This table stays under 1M rows this quarter"
- "Service Y keeps the same cache contract"

If the assumption stops being true, behavior, reliability, or performance can regress. `assumption-lock` turns these into explicit, trackable records in code.

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
assumption-lock inventory --module my_app.assumptions --format json
```

Use `report` when you want a human-readable register, and `inventory` when you want a machine-friendly inventory payload with a top-level summary and the full assumption list.

## CI example

```bash
pip install -e .
pytest
assumption-lock check --module my_app.assumptions
```

Use `severity="fail"` for assumptions that should fail CI and `severity="warn"` for assumptions that should remain visible without forcing a non-zero exit code.

## What this enforces in practice

`assumption-lock` only enforces behavior when you run checks (typically in CI).

When `assumption-lock check` runs, developers are effectively required to keep assumptions healthy according to policy, including:

- declaring assumptions explicitly in code with `assume(...)`
- keeping required metadata valid (for example owner and expiry)
- keeping assumptions from expiring
- providing evidence when your policy requires it (for example `require_evidence_for_fail = true`)
- keeping predicates passing when predicates are used

Exit behavior:

- failures on assumptions with `severity="fail"` produce a non-zero exit code
- failures on assumptions with `severity="warn"` remain visible but do not fail CI

## Runtime check vs static scan

- Runtime check imports only the modules you explicitly pass, registers assumptions, validates metadata through the policy engine, and optionally executes predicates.
- Static scan parses Python files with `ast` and finds simple `assume(...)` calls without importing application code.

You can configure the policy engine with either `assumption-lock.toml` or a `[tool.assumption_lock]` table in `pyproject.toml`.

The default policy checks for:

- missing owners
- expired assumptions
- assumptions expiring soon
- predicate failures or exceptions

Supported config settings today:

- `expiring_within_days` — number of days before expiry to treat an assumption as expiring soon
- `require_evidence_for_fail` — require `evidence` on assumptions with `severity = "fail"`

## Known v0.1 limitations

- Static scan only extracts literal string names from simple calls such as `assume("name")` and `assumption_lock.assume("name")`.
- Static scan does not resolve aliases, dynamic variables, or indirect wrappers.

## Guidance

Keep assumptions in a dedicated `assumptions.py` file when possible so runtime imports stay explicit and easy to review.

The Markdown report now includes an inventory summary so you can quickly see total assumptions, missing owners, expiry risk, and predicate usage before drilling into the full table.

Use `assumption-lock inventory --format json` when you want a machine-readable inventory payload with a top-level summary and the full assumption list.

Typical output choices:

- `assumption-lock report --format markdown` for a readable register in docs or CI logs
- `assumption-lock report --format json` for a flat assumption list
- `assumption-lock inventory --format json` for structured tooling, dashboards, or downstream automation

Inventory can also be filtered and grouped:

```bash
assumption-lock inventory --module my_app.assumptions --format markdown --owner platform
assumption-lock inventory --module my_app.assumptions --format json --severity fail --group-by status
```

Supported inventory filters today:

- `--owner`
- `--severity`
- `--status active|expired|expiring_soon`
- `--has-predicate`
- `--group-by owner|severity|status`

Example `assumption-lock.toml`:

```toml
expiring_within_days = 14
require_evidence_for_fail = true
```

## Non-goals for v0.1

- Web UI
- Database
- Background daemon
- Slack, Jira, or GitHub app integrations
- Auto-discovery that imports arbitrary application modules