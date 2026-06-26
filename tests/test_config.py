from __future__ import annotations

from assumption_lock.config import PolicyConfig, load_policy_config


def test_load_policy_config_from_assumption_lock_toml(tmp_path) -> None:
    config_file = tmp_path / "assumption-lock.toml"
    config_file.write_text(
        "\n".join(
            [
                "expiring_within_days = 7",
                "require_evidence_for_fail = true",
            ]
        ),
        encoding="utf-8",
    )

    config = load_policy_config(config_file)

    assert config == PolicyConfig(expiring_within_days=7, require_evidence_for_fail=True)


def test_load_policy_config_defaults_when_missing(tmp_path) -> None:
    config = load_policy_config(cwd=tmp_path)

    assert config == PolicyConfig()