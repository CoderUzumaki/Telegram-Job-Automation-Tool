import json
import re
from pathlib import Path

from job_radar import worker_version

ROOT = Path(__file__).resolve().parents[2]


def test_worker_package_imports_and_reports_version() -> None:
    assert worker_version() == "0.1.0"


def test_v1_ipc_schema_is_valid_json_schema_document() -> None:
    schema_path = ROOT / "contracts" / "v1" / "ipc-envelope.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["title"] == "Job Radar IPC envelope v1"
    assert schema["oneOf"]


def test_example_config_contains_no_credential_fields_or_secret_values() -> None:
    config = (ROOT / "worker" / "config.example.toml").read_text(encoding="utf-8")
    credential_names = r"(?i)(api[_-]?hash|api[_-]?key|password|session[_-]?string|token)"

    assert not re.search(credential_names, config)
    assert not re.search(r"(?i)(sk-[A-Za-z0-9]{16,}|[A-F0-9]{32,})", config)
