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
import socket
import tempfile
import time
from urllib.error import HTTPError, URLError

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
MAX_DOWNLOAD_ATTEMPTS = 4
DOWNLOAD_RETRY_DELAYS_SECONDS = (5, 15, 45)


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


def _retryable_download_error(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    return isinstance(exc, (URLError, TimeoutError, socket.timeout, ConnectionError))


def _acquire_registered_archives(
    registration: dict,
    destination: Path,
    *,
    attempt_log: list[dict[str, object]] | None = None,
) -> list[Path]:
    expected = registration["source"]["archive_sha256"]
    attempts = [] if attempt_log is None else attempt_log
    paths: list[Path] = []
    for name in sorted(expected):
        match = ARCHIVE_RE.fullmatch(name)
        if match is None:
            raise RuntimeError(f"unexpected registered archive name: {name}")
        year, month = int(match.group(1)), int(match.group(2))
        path = destination / name
        for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
            if path.exists():
                path.unlink()
            try:
                checksum = download_archive(
                    archive_url("BTCUSDT", year, month),
                    path,
                    verify_checksum=True,
                )
                if checksum != str(expected[name]).lower():
                    raise RuntimeError(
                        f"official checksum differs from registration: {name}"
                    )
            except Exception as exc:
                attempts.append(
                    {
                        "archive": name,
                        "attempt": attempt,
                        "error_type": type(exc).__name__,
                    }
                )
                if path.exists():
                    path.unlink()
                if (
                    attempt >= MAX_DOWNLOAD_ATTEMPTS
                    or not _retryable_download_error(exc)
                ):
                    raise
                time.sleep(DOWNLOAD_RETRY_DELAYS_SECONDS[attempt - 1])
                continue

            attempts.append(
                {
                    "archive": name,
                    "attempt": attempt,
                    "error_type": None,
                }
            )
            paths.append(path)
            break
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
        "source_acquisition_attempts": [],
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
            archives = _acquire_registered_archives(
                registration,
                Path(temporary),
                attempt_log=incident["source_acquisition_attempts"],
            )
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
