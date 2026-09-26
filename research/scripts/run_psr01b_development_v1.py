"""Manual-only PSR-01B Development V1 wrapper.

The workflow creates and verifies the durable one-shot claim before this script
is allowed to acquire or open registered source archives.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

from research_core.data_ingestion import archive_url, download_archive
from research_core.psr01b_execution_lock import DEFAULT_RESULT_PATH, assert_execution_environment
from research_core.psr01b_runner import (
    execute_registered_one_shot,
    load_implementation_freeze,
    verify_frozen_execution_identity,
)
from research_core.psr01b_preflight import load_registration

OUTPUT_DIR = DEFAULT_RESULT_PATH.parent
INCIDENT_PATH = OUTPUT_DIR / "incident.json"
ARCHIVE_RE = re.compile(r"^BTCUSDT-1h-(\d{4})-(\d{2})\.zip$")


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite evidence path: {path}")
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(text + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _acquire_registered_archives(registration: dict, destination: Path) -> list[Path]:
    expected = registration["source"]["archive_sha256"]
    paths: list[Path] = []
    for name in sorted(expected):
        match = ARCHIVE_RE.fullmatch(name)
        if match is None:
            raise RuntimeError(f"unexpected registered archive name: {name}")
        year, month = int(match.group(1)), int(match.group(2))
        path = destination / name
        checksum = download_archive(
            archive_url("BTCUSDT", year, month),
            path,
            verify_checksum=True,
        )
        if checksum != str(expected[name]).lower():
            raise RuntimeError(f"official checksum differs from registration: {name}")
        paths.append(path)
    return paths


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    incident = {
        "stage": "PRE_SOURCE",
        "executing_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "actor": os.environ.get("GITHUB_ACTOR"),
        "workflow_event": os.environ.get("GITHUB_EVENT_NAME"),
        "market_data_accessed": False,
        "completed": False,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        freeze = load_implementation_freeze()
        provenance = verify_frozen_execution_identity(runner_label="ubuntu-24.04")
        assert_execution_environment(
            provenance["implementation_candidate_commit"],
            freeze,
            DEFAULT_RESULT_PATH,
        )
        registration = load_registration()

        with tempfile.TemporaryDirectory(
            prefix="psr01b-development-v1-",
            dir=os.environ.get("RUNNER_TEMP"),
        ) as temporary:
            incident["stage"] = "SOURCE_ACQUISITION"
            incident["market_data_accessed"] = True
            archives = _acquire_registered_archives(registration, Path(temporary))
            incident["stage"] = "REGISTERED_EXECUTION"
            result = execute_registered_one_shot(
                archives,
                result_path=DEFAULT_RESULT_PATH,
                runner_label="ubuntu-24.04",
            )
        incident["stage"] = "COMPLETE"
        incident["completed"] = True
        incident["success_token"] = result.get("success_token")
    except Exception as exc:
        incident["error_type"] = type(exc).__name__
        incident["error"] = str(exc)
        if not INCIDENT_PATH.exists():
            _atomic_json(INCIDENT_PATH, incident)
        raise

    if not INCIDENT_PATH.exists():
        _atomic_json(INCIDENT_PATH, incident)


if __name__ == "__main__":
    main()
