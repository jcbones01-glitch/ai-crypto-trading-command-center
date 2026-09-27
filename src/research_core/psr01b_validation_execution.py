"""PSR-01B Validation V1 future execution-control implementation.

This module implements the prospective governed control path only.  Importing it
or running bounded tests grants no protected-data, OOS, rehearsal, empirical,
or trading authorization.  Protected transport is unreachable without a
durably verified claim token created after preflight and result reservation.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tarfile
import time
from typing import Any, Callable, Mapping, MutableMapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from . import psr01b_preflight as parent_preflight
from .data_quality import scan_archive
from .psr01b_core import PSR01BError
from . import psr01b_validation as validation

ROOT = validation.ROOT
FREEZE_V2_PATH = ROOT / "research/governance/psr01b_validation_implementation_freeze_v2.json"
RESULT_ROOT = ROOT / "research/experiments/psr01b_validation_v1"
RESULT_PATH = (RESULT_ROOT / "result.json").resolve()
INCIDENT_PATH = (RESULT_ROOT / "terminal_incident.json").resolve()
RAW_SOURCE_DIR = (RESULT_ROOT / "raw_source").resolve()
RAW_SOURCE_MANIFEST_PATH = (RESULT_ROOT / "raw_source_manifest.json").resolve()
RAW_SOURCE_PACKAGE_PATH = (RESULT_ROOT / "psr01b_validation_raw_source_v1.tar").resolve()
REHEARSAL_ROOT = (ROOT / "research/experiments/psr01b_validation_rehearsals").resolve()
REAL_CLAIM_REF = "refs/tags/psr01b-validation-one-shot-claim-v1"
FUTURE_REVIEWED_ANCHOR_REF = "refs/heads/psr-01b-validation-implementation-reviewed-v2"
MAX_DOWNLOAD_ATTEMPTS = 4
DOWNLOAD_RETRY_DELAYS_SECONDS = (5, 15, 45)
ARCHIVE_RE = re.compile(r"^BTCUSDT-1h-(\d{4})-(\d{2})\.zip$")
ALLOWED_POST_CANDIDATE_PATHS = {
    "research/governance/psr01b_validation_implementation_freeze_v2.json",
}
INHERITED_DEVELOPMENT_CONTROL_PINS = {
    "research/scripts/run_psr01b_development_v1.py": "7cc0bd7353d41502c4a0a07e7330b42bfea36ac5",
    "src/research_core/psr01b_preflight.py": "79993f11034ab0aa322e2bbc77d3f220902a242c",
    "src/research_core/psr01b_execution_lock.py": "d9f86758d7474075da4d8d7347b92fc7be3cde30",
    "src/research_core/psr01b_rehearsal.py": "d7da9797a1e5bd265cbd2eb5198ee864111f23d4",
}
_VERIFIED_CLAIM_SENTINEL = object()


class ValidationExecutionControlError(validation.ValidationContractError):
    """Fail-closed Validation execution-control failure."""


@dataclass(frozen=True)
class VerifiedClaim:
    ref: str
    target_sha: str
    tag_object_sha: str
    run_id: str
    run_attempt: str
    actor: str
    _marker: object


@dataclass(frozen=True)
class SourceAcquisition:
    archive_paths: tuple[Path, ...]
    ledger: tuple[dict[str, Any], ...]
    accepted: tuple[dict[str, Any], ...]
    source_access_occurred: bool
    first_protected_request_occurred: bool


def _git_head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationExecutionControlError(
            "cannot resolve Validation execution HEAD",
            failure_code="VALIDATION_GIT_HEAD_UNAVAILABLE",
        ) from exc


def _git_blob_at_commit(commit: str, relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", f"{commit}:{relative}"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationExecutionControlError(
            f"cannot resolve candidate blob: {relative}",
            failure_code="VALIDATION_CANDIDATE_BLOB_UNAVAILABLE",
        ) from exc


def _current_blob(relative: str) -> str:
    return validation.git_blob_sha1(ROOT / relative)


def execution_mode(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    mode = env.get("PSR01B_VALIDATION_EXECUTION_MODE", "execute")
    if mode not in {"execute", "rehearsal"}:
        raise ValidationExecutionControlError(
            "invalid Validation execution mode",
            failure_code="VALIDATION_EXECUTION_MODE_INVALID",
        )
    return mode


def claim_ref(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    if execution_mode(env) == "execute":
        return REAL_CLAIM_REF
    run_id = env.get("GITHUB_RUN_ID", "")
    attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    if not re.fullmatch(r"[0-9]+", run_id) or not re.fullmatch(r"[0-9]+", attempt):
        raise ValidationExecutionControlError(
            "invalid Validation rehearsal run/attempt identity",
            failure_code="VALIDATION_REHEARSAL_IDENTITY_INVALID",
        )
    ref = f"refs/tags/psr01b-validation-rehearsal-{run_id}-{attempt}"
    if ref == REAL_CLAIM_REF:
        raise ValidationExecutionControlError(
            "rehearsal must never use the real Validation claim",
            failure_code="VALIDATION_REHEARSAL_REAL_CLAIM_COLLISION",
        )
    return ref


def execution_result_path(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    if execution_mode(env) == "execute":
        return RESULT_PATH
    label = claim_ref(env).removeprefix("refs/tags/")
    path = (REHEARSAL_ROOT / label / "result.json").resolve()
    if path == RESULT_PATH or RESULT_ROOT in path.parents:
        raise ValidationExecutionControlError(
            "rehearsal result path overlaps real Validation namespace",
            failure_code="VALIDATION_REHEARSAL_RESULT_PATH_COLLISION",
        )
    return path


def reservation_path(result_path: Path) -> Path:
    canonical = Path(result_path).resolve()
    return canonical.with_name(canonical.name + ".reservation")


def _write_bytes_exclusive(path: Path, payload: bytes) -> None:
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise ValidationExecutionControlError(
            f"refusing to overwrite Validation evidence path: {path}",
            failure_code="VALIDATION_EVIDENCE_NO_OVERWRITE",
        )
    linked = False
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        linked = True
        temporary.unlink()
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    except Exception:
        if temporary.exists():
            temporary.unlink()
        if linked and path.exists():
            path.unlink()
        raise


def reserve_result_path(
    result_path: Path,
    *,
    candidate: str,
    executing_sha: str,
) -> dict[str, str]:
    canonical = Path(result_path).resolve()
    if canonical.exists():
        raise ValidationExecutionControlError(
            "Validation result path already exists",
            failure_code="VALIDATION_RESULT_ALREADY_EXISTS",
        )
    record = {
        "candidate": candidate,
        "executing_sha": executing_sha,
        "result_path": str(canonical),
    }
    marker = reservation_path(canonical)
    if marker.exists():
        try:
            observed = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationExecutionControlError(
                "Validation result reservation is invalid",
                failure_code="VALIDATION_RESERVATION_INVALID",
            ) from exc
        if observed != record:
            raise ValidationExecutionControlError(
                "Validation result path is reserved by another execution",
                failure_code="VALIDATION_RESERVATION_IDENTITY_MISMATCH",
            )
        return record
    validation.write_json_exclusive(marker, record)
    return record


def assert_result_reservation(
    result_path: Path,
    *,
    candidate: str,
    executing_sha: str,
) -> dict[str, str]:
    canonical = Path(result_path).resolve()
    if canonical.exists():
        raise ValidationExecutionControlError(
            "Validation result path already exists",
            failure_code="VALIDATION_RESULT_ALREADY_EXISTS",
        )
    marker = reservation_path(canonical)
    try:
        observed = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationExecutionControlError(
            "Validation result reservation is missing or invalid",
            failure_code="VALIDATION_RESERVATION_MISSING",
        ) from exc
    expected = {
        "candidate": candidate,
        "executing_sha": executing_sha,
        "result_path": str(canonical),
    }
    if observed != expected:
        raise ValidationExecutionControlError(
            "Validation result reservation identity mismatch",
            failure_code="VALIDATION_RESERVATION_IDENTITY_MISMATCH",
        )
    return observed


def _module_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    package = ROOT / "src/research_core"
    for path in sorted(package.glob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        module = "research_core" if path.name == "__init__.py" else f"research_core.{path.stem}"
        mapping[module] = rel
    return mapping


def discover_project_import_closure_paths() -> tuple[str, ...]:
    """AST-derived complete project-local import closure for the future runner."""
    roots = {
        "src/research_core/psr01b_validation.py",
        "src/research_core/psr01b_validation_execution.py",
        "research/scripts/run_psr01b_validation_execution_v1.py",
    }
    module_map = _module_map()
    package_init = module_map.get("research_core")
    pending = list(sorted(roots))
    seen: set[str] = set()
    while pending:
        relative = pending.pop(0)
        if relative in seen:
            continue
        path = ROOT / relative
        if not path.exists():
            raise ValidationExecutionControlError(
                f"import-closure path missing: {relative}",
                failure_code="VALIDATION_IMPORT_CLOSURE_PATH_MISSING",
            )
        seen.add(relative)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, SyntaxError) as exc:
            raise ValidationExecutionControlError(
                f"cannot parse import-closure path: {relative}",
                failure_code="VALIDATION_IMPORT_CLOSURE_PARSE_FAIL",
            ) from exc

        current_module = None
        if relative.startswith("src/research_core/"):
            stem = Path(relative).stem
            current_module = "research_core" if stem == "__init__" else f"research_core.{stem}"

        targets: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "research_core" or alias.name.startswith("research_core."):
                        targets.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and current_module:
                    package_parts = current_module.split(".")[:-1]
                    ascend = max(0, node.level - 1)
                    if ascend:
                        package_parts = package_parts[:-ascend]
                    base = ".".join(package_parts)
                    if node.module:
                        targets.add(f"{base}.{node.module}" if base else node.module)
                    else:
                        for alias in node.names:
                            targets.add(f"{base}.{alias.name}" if base else alias.name)
                elif node.module and (
                    node.module == "research_core"
                    or node.module.startswith("research_core.")
                ):
                    targets.add(node.module)
                    if node.module == "research_core":
                        for alias in node.names:
                            maybe = f"research_core.{alias.name}"
                            if maybe in module_map:
                                targets.add(maybe)

        if package_init:
            seen.add(package_init)
        for target in sorted(targets):
            candidate = target
            while candidate and candidate not in module_map and "." in candidate:
                candidate = candidate.rsplit(".", 1)[0]
            mapped = module_map.get(candidate)
            if mapped and mapped not in seen and mapped not in pending:
                pending.append(mapped)
    return tuple(sorted(seen))


def project_import_closure_blobs() -> dict[str, str]:
    return {
        path: _current_blob(path)
        for path in discover_project_import_closure_paths()
    }


def verify_complete_import_closure(freeze: Mapping[str, Any]) -> dict[str, str]:
    expected = freeze.get("complete_import_closure_git_blob_sha1") or {}
    observed = project_import_closure_blobs()
    if observed != expected:
        missing = sorted(set(observed) - set(expected))
        extra = sorted(set(expected) - set(observed))
        drift = sorted(
            path for path in set(observed) & set(expected)
            if observed[path] != expected[path]
        )
        raise ValidationExecutionControlError(
            f"Validation import-closure pin mismatch missing={missing} extra={extra} drift={drift}",
            failure_code="VALIDATION_IMPORT_CLOSURE_PIN_MISMATCH",
        )
    return observed


def verify_inherited_development_control_pins() -> dict[str, str]:
    observed = {path: _current_blob(path) for path in INHERITED_DEVELOPMENT_CONTROL_PINS}
    if observed != INHERITED_DEVELOPMENT_CONTROL_PINS:
        raise ValidationExecutionControlError(
            "pinned Development execution-control identity drift",
            failure_code="VALIDATION_INHERITED_EXECUTION_CONTROL_PIN_MISMATCH",
        )
    return observed


def load_freeze(path: Path = FREEZE_V2_PATH) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationExecutionControlError(
            "cannot load Validation implementation freeze-v2",
            failure_code="VALIDATION_FREEZE_V2_LOAD_FAIL",
        ) from exc
    if data.get("freeze_id") != "PSR01B-VALIDATION-IMPLEMENTATION-FREEZE-V2":
        raise ValidationExecutionControlError(
            "unexpected Validation freeze-v2 identity",
            failure_code="VALIDATION_FREEZE_V2_ID_MISMATCH",
        )
    return data


def verify_candidate_blob_contract(
    candidate: str,
    expected: Mapping[str, str],
) -> dict[str, str]:
    if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
        raise ValidationExecutionControlError(
            "invalid frozen Validation candidate SHA",
            failure_code="VALIDATION_CANDIDATE_SHA_INVALID",
        )
    if not expected:
        raise ValidationExecutionControlError(
            "Validation implementation blob inventory missing",
            failure_code="VALIDATION_IMPLEMENTATION_BLOB_INVENTORY_MISSING",
        )
    observed: dict[str, str] = {}
    for relative, wanted in expected.items():
        candidate_blob = _git_blob_at_commit(candidate, relative)
        current_blob = _current_blob(relative)
        if candidate_blob != wanted or current_blob != wanted:
            raise ValidationExecutionControlError(
                f"Validation candidate/current blob mismatch: {relative}",
                failure_code="VALIDATION_IMPLEMENTATION_BLOB_MISMATCH",
            )
        observed[relative] = current_blob
    return observed


def verify_execution_commit(candidate: str, executing_sha: str) -> tuple[str, ...]:
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, executing_sha],
            cwd=ROOT,
            check=False,
        )
        if ancestor.returncode != 0:
            raise ValidationExecutionControlError(
                "executing SHA is not descended from frozen Validation candidate",
                failure_code="VALIDATION_EXECUTION_ANCESTRY_FAIL",
            )
        changed = tuple(
            line for line in subprocess.check_output(
                ["git", "diff", "--name-only", candidate, executing_sha],
                cwd=ROOT,
                text=True,
            ).splitlines() if line
        )
    except ValidationExecutionControlError:
        raise
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationExecutionControlError(
            "cannot verify Validation execution ancestry/diff",
            failure_code="VALIDATION_EXECUTION_DIFF_UNAVAILABLE",
        ) from exc
    forbidden = sorted(set(changed) - ALLOWED_POST_CANDIDATE_PATHS)
    if forbidden:
        raise ValidationExecutionControlError(
            "unapproved post-candidate path changed: " + ", ".join(forbidden),
            failure_code="VALIDATION_POST_CANDIDATE_DRIFT",
        )
    return changed


def verify_frozen_execution_identity(
    *,
    runner_label: str,
    freeze: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    frozen = dict(load_freeze() if freeze is None else freeze)
    approved = frozen.get("approved_specification") or {}
    expected_approved = {
        "exact_approved_head": validation.APPROVED_SPEC_HEAD,
        "markdown_path": "docs/PSR01B_VALIDATION_SPEC_V1.md",
        "markdown_git_blob_sha1": validation.APPROVED_SPEC_MD_BLOB,
        "json_path": "research/governance/psr01b_validation_spec_v1.json",
        "json_git_blob_sha1": validation.APPROVED_SPEC_JSON_BLOB,
        "registration_id": validation.REGISTRATION_ID,
    }
    for key, wanted in expected_approved.items():
        if approved.get(key) != wanted:
            raise ValidationExecutionControlError(
                f"approved Validation specification identity drift: {key}",
                failure_code="VALIDATION_APPROVED_SPEC_IDENTITY_DRIFT",
            )
    if _current_blob(expected_approved["markdown_path"]) != validation.APPROVED_SPEC_MD_BLOB:
        raise ValidationExecutionControlError(
            "approved Validation Markdown blob mismatch",
            failure_code="VALIDATION_APPROVED_SPEC_BLOB_MISMATCH",
        )
    if _current_blob(expected_approved["json_path"]) != validation.APPROVED_SPEC_JSON_BLOB:
        raise ValidationExecutionControlError(
            "approved Validation JSON blob mismatch",
            failure_code="VALIDATION_APPROVED_SPEC_BLOB_MISMATCH",
        )

    implementation = frozen.get("implementation") or {}
    candidate = implementation.get("implementation_candidate_commit")
    expected_blobs = frozen.get("implementation_file_git_blob_sha1") or {}
    observed_implementation = verify_candidate_blob_contract(candidate, expected_blobs)
    closure = verify_complete_import_closure(frozen)
    inherited = verify_inherited_development_control_pins()
    validation.verify_pinned_module_identities(ROOT, validation.load_validation_spec())
    runtime = parent_preflight.verify_runtime_versions(runner_label=runner_label)
    threads = parent_preflight.verify_thread_environment(environ)

    executing_sha = (
        (os.environ if environ is None else environ).get("GITHUB_SHA")
        or _git_head_sha()
    )
    changed = verify_execution_commit(candidate, executing_sha)
    return {
        "candidate": candidate,
        "executing_sha": executing_sha,
        "post_candidate_changed_paths": list(changed),
        "implementation_file_git_blob_sha1": observed_implementation,
        "complete_import_closure_git_blob_sha1": closure,
        "inherited_development_execution_control_git_blob_sha1": inherited,
        "runtime_versions": runtime,
        "thread_environment": threads,
    }


def _request(url: str, token: str, *, method: str = "GET", data: bytes | None = None) -> Request:
    return Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )


def _github_json(
    request: Request,
    *,
    opener: Callable[..., Any] = urlopen,
) -> Any:
    try:
        response = opener(request)
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise ValidationExecutionControlError(
            f"GitHub governance request failed HTTP {exc.code}",
            failure_code="VALIDATION_GITHUB_GOVERNANCE_REQUEST_FAIL",
        ) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValidationExecutionControlError(
            "invalid GitHub governance response",
            failure_code="VALIDATION_GITHUB_GOVERNANCE_RESPONSE_INVALID",
        ) from exc


def _resolve_fixed_ref(
    repository: str,
    token: str,
    ref: str,
    *,
    opener: Callable[..., Any] = urlopen,
) -> str | None:
    suffix = quote(ref.removeprefix("refs/"), safe="/")
    data = _github_json(
        _request(f"https://api.github.com/repos/{repository}/git/ref/{suffix}", token),
        opener=opener,
    )
    if data is None:
        return None
    sha = ((data.get("object") or {}).get("sha"))
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValidationExecutionControlError(
            "GitHub ref resolved to invalid object",
            failure_code="VALIDATION_GITHUB_REF_INVALID",
        )
    return sha


def verify_ruleset(
    repository: str,
    token: str,
    *,
    ruleset_id: int,
    target: str,
    ref: str,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    data = _github_json(
        _request(
            f"https://api.github.com/repos/{repository}/rulesets/{int(ruleset_id)}",
            token,
        ),
        opener=opener,
    )
    if not isinstance(data, dict):
        raise ValidationExecutionControlError(
            "required Validation ruleset not found",
            failure_code="VALIDATION_RULESET_MISSING",
        )
    includes = ((data.get("conditions") or {}).get("ref_name") or {}).get("include") or []
    rules = {item.get("type") for item in data.get("rules") or []}
    if (
        data.get("enforcement") != "active"
        or data.get("target") != target
        or includes != [ref]
        or rules != {"deletion", "non_fast_forward", "update"}
        or (data.get("bypass_actors") or [])
    ):
        raise ValidationExecutionControlError(
            "Validation ruleset protection contract mismatch",
            failure_code="VALIDATION_RULESET_CONTRACT_MISMATCH",
        )
    return data


def _review_protection(freeze: Mapping[str, Any]) -> Mapping[str, Any]:
    return (freeze.get("ref_protection") or {}).get("reviewed_v2_anchor") or {}


def _claim_protection(freeze: Mapping[str, Any]) -> Mapping[str, Any]:
    return (freeze.get("ref_protection") or {}).get("future_real_claim") or {}


def assert_review_anchor(
    candidate: str,
    freeze: Mapping[str, Any],
    *,
    repository: str,
    token: str,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    protection = _review_protection(freeze)
    if protection.get("ref") != FUTURE_REVIEWED_ANCHOR_REF:
        raise ValidationExecutionControlError(
            "future reviewed-v2 anchor ref is not frozen",
            failure_code="VALIDATION_REVIEW_ANCHOR_REF_MISMATCH",
        )
    if protection.get("created") is not True:
        raise ValidationExecutionControlError(
            "reviewed-v2 anchor has not been created",
            failure_code="VALIDATION_REVIEW_ANCHOR_NOT_CREATED",
        )
    observed = _resolve_fixed_ref(repository, token, FUTURE_REVIEWED_ANCHOR_REF, opener=opener)
    if observed != candidate:
        raise ValidationExecutionControlError(
            "reviewed-v2 anchor does not resolve to frozen candidate",
            failure_code="VALIDATION_REVIEW_ANCHOR_SHA_MISMATCH",
        )
    ruleset_id = protection.get("ruleset_id")
    if not isinstance(ruleset_id, int):
        raise ValidationExecutionControlError(
            "reviewed-v2 anchor ruleset ID missing",
            failure_code="VALIDATION_REVIEW_ANCHOR_RULESET_MISSING",
        )
    verify_ruleset(
        repository,
        token,
        ruleset_id=ruleset_id,
        target="branch",
        ref=FUTURE_REVIEWED_ANCHOR_REF,
        opener=opener,
    )
    return {"ref": FUTURE_REVIEWED_ANCHOR_REF, "sha": observed, "ruleset_id": ruleset_id}


def assert_future_claim_ruleset(
    freeze: Mapping[str, Any],
    *,
    repository: str,
    token: str,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    protection = _claim_protection(freeze)
    if protection.get("ref") != REAL_CLAIM_REF:
        raise ValidationExecutionControlError(
            "future real-claim ref drift",
            failure_code="VALIDATION_REAL_CLAIM_REF_MISMATCH",
        )
    ruleset_id = protection.get("ruleset_id")
    if not isinstance(ruleset_id, int):
        raise ValidationExecutionControlError(
            "future real-claim ruleset ID missing",
            failure_code="VALIDATION_REAL_CLAIM_RULESET_MISSING",
        )
    data = verify_ruleset(
        repository,
        token,
        ruleset_id=ruleset_id,
        target="tag",
        ref=REAL_CLAIM_REF,
        opener=opener,
    )
    return {"ref": REAL_CLAIM_REF, "ruleset_id": ruleset_id, "ruleset": data}


def assert_manual_confirmation(
    candidate: str,
    executing_sha: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    env = os.environ if environ is None else environ
    prefix = (
        "PSR01B_VALIDATION_V1"
        if execution_mode(env) == "execute"
        else "PSR01B_VALIDATION_REHEARSAL_V1"
    )
    expected = f"{prefix}:{candidate}:{executing_sha}"
    observed = env.get("PSR01B_VALIDATION_V1_CONFIRMATION", "")
    if observed != expected:
        raise ValidationExecutionControlError(
            "Validation manual confirmation mismatch",
            failure_code="VALIDATION_MANUAL_CONFIRMATION_MISMATCH",
        )
    return observed


def verify_authorization_scope(
    freeze: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, bool]:
    env = os.environ if environ is None else environ
    mode = execution_mode(env)
    auth = dict(freeze.get("authorizations") or {})
    future = dict(freeze.get("future_governance") or {})
    if future.get("independent_implementation_review_approved") is not True:
        raise ValidationExecutionControlError(
            "independent Validation implementation review is not approved",
            failure_code="VALIDATION_INDEPENDENT_REVIEW_NOT_APPROVED",
        )
    if mode == "rehearsal":
        if auth.get("rehearsal_authorized") is not True:
            raise ValidationExecutionControlError(
                "Validation rehearsal authorization is not approved",
                failure_code="VALIDATION_REHEARSAL_NOT_AUTHORIZED",
            )
        required_false = (
            "validation_source_access_authorized",
            "validation_empirical_feature_generation_authorized",
            "validation_empirical_model_fit_authorized",
            "validation_empirical_forecast_generation_authorized",
            "validation_strategy_pnl_authorized",
            "oos_access_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
            "leverage_authorized",
            "derivatives_execution_authorized",
            "empirical_validation_execution_authorized",
            "real_validation_claim_creation_authorized",
        )
        if any(auth.get(key) is not False for key in required_false):
            raise ValidationExecutionControlError(
                "rehearsal scope contains protected/empirical/trading authority",
                failure_code="VALIDATION_REHEARSAL_SCOPE_TOO_BROAD",
            )
    else:
        if future.get("separate_execution_authorization_approved") is not True:
            raise ValidationExecutionControlError(
                "separate Validation execution authorization is not approved",
                failure_code="VALIDATION_EXECUTION_AUTHORIZATION_NOT_APPROVED",
            )
        required_true = (
            "validation_source_access_authorized",
            "validation_empirical_feature_generation_authorized",
            "validation_empirical_model_fit_authorized",
            "validation_empirical_forecast_generation_authorized",
            "validation_strategy_pnl_authorized",
            "empirical_validation_execution_authorized",
            "real_validation_claim_creation_authorized",
        )
        required_false = (
            "oos_access_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
            "leverage_authorized",
            "derivatives_execution_authorized",
            "rehearsal_authorized",
        )
        if any(auth.get(key) is not True for key in required_true) or any(
            auth.get(key) is not False for key in required_false
        ):
            raise ValidationExecutionControlError(
                "Validation execution authorization scope mismatch",
                failure_code="VALIDATION_EXECUTION_SCOPE_MISMATCH",
            )
    return {key: bool(value) for key, value in auth.items()}


def _claim_message(
    ref: str,
    executing_sha: str,
    *,
    run_id: str,
    run_attempt: str,
    actor: str,
) -> str:
    return json.dumps(
        {
            "claim_ref": ref,
            "execution_sha": executing_sha,
            "run_id": run_id,
            "run_attempt": run_attempt,
            "actor": actor,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def resolve_claim_record(
    repository: str,
    token: str,
    *,
    ref: str,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, str] | None:
    tag_object_sha = _resolve_fixed_ref(repository, token, ref, opener=opener)
    if tag_object_sha is None:
        return None
    data = _github_json(
        _request(
            f"https://api.github.com/repos/{repository}/git/tags/{tag_object_sha}",
            token,
        ),
        opener=opener,
    )
    if not isinstance(data, dict):
        raise ValidationExecutionControlError(
            "Validation claim tag object missing",
            failure_code="VALIDATION_CLAIM_TAG_OBJECT_MISSING",
        )
    try:
        record = json.loads(str(data.get("message", "")).strip())
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValidationExecutionControlError(
            "Validation claim tag message invalid",
            failure_code="VALIDATION_CLAIM_MESSAGE_INVALID",
        ) from exc
    obj = data.get("object") or {}
    if (
        data.get("sha") != tag_object_sha
        or data.get("tag") != ref.removeprefix("refs/tags/")
        or obj.get("type") != "commit"
        or record.get("claim_ref") != ref
        or record.get("execution_sha") != obj.get("sha")
    ):
        raise ValidationExecutionControlError(
            "Validation durable claim identity mismatch",
            failure_code="VALIDATION_CLAIM_IDENTITY_MISMATCH",
        )
    for key in ("execution_sha", "run_id", "run_attempt", "actor"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise ValidationExecutionControlError(
                "Validation durable claim provenance incomplete",
                failure_code="VALIDATION_CLAIM_PROVENANCE_INCOMPLETE",
            )
    return {
        "ref": ref,
        "target_sha": record["execution_sha"],
        "tag_object_sha": tag_object_sha,
        "run_id": record["run_id"],
        "run_attempt": record["run_attempt"],
        "actor": record["actor"],
    }


def assert_claim_absent(
    repository: str,
    token: str,
    *,
    ref: str,
    opener: Callable[..., Any] = urlopen,
) -> None:
    if resolve_claim_record(repository, token, ref=ref, opener=opener) is not None:
        raise ValidationExecutionControlError(
            f"Validation claim already exists: {ref}",
            failure_code="VALIDATION_CLAIM_ALREADY_EXISTS",
        )


def create_claim(
    repository: str,
    executing_sha: str,
    token: str,
    *,
    environ: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, str]:
    env = os.environ if environ is None else environ
    ref = claim_ref(env)
    run_id = env.get("GITHUB_RUN_ID", "")
    run_attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    actor = env.get("GITHUB_ACTOR", "")
    if not re.fullmatch(r"[0-9]+", run_id) or not re.fullmatch(r"[0-9]+", run_attempt) or not actor:
        raise ValidationExecutionControlError(
            "Validation claim run provenance incomplete",
            failure_code="VALIDATION_CLAIM_PROVENANCE_INCOMPLETE",
        )
    message = _claim_message(
        ref,
        executing_sha,
        run_id=run_id,
        run_attempt=run_attempt,
        actor=actor,
    )
    tag_payload = json.dumps(
        {
            "tag": ref.removeprefix("refs/tags/"),
            "message": message,
            "object": executing_sha,
            "type": "commit",
        }
    ).encode("utf-8")
    created = _github_json(
        _request(
            f"https://api.github.com/repos/{repository}/git/tags",
            token,
            method="POST",
            data=tag_payload,
        ),
        opener=opener,
    )
    if not isinstance(created, dict):
        raise ValidationExecutionControlError(
            "Validation annotated tag creation failed",
            failure_code="VALIDATION_CLAIM_TAG_CREATE_FAIL",
        )
    tag_object_sha = created.get("sha")
    if (
        created.get("tag") != ref.removeprefix("refs/tags/")
        or str(created.get("message", "")).strip() != message
        or ((created.get("object") or {}).get("sha")) != executing_sha
        or ((created.get("object") or {}).get("type")) != "commit"
        or not isinstance(tag_object_sha, str)
        or not re.fullmatch(r"[0-9a-f]{40}", tag_object_sha)
    ):
        raise ValidationExecutionControlError(
            "GitHub returned unexpected Validation claim tag object",
            failure_code="VALIDATION_CLAIM_TAG_CREATE_MISMATCH",
        )
    ref_payload = json.dumps({"ref": ref, "sha": tag_object_sha}).encode("utf-8")
    created_ref = _github_json(
        _request(
            f"https://api.github.com/repos/{repository}/git/refs",
            token,
            method="POST",
            data=ref_payload,
        ),
        opener=opener,
    )
    if not isinstance(created_ref, dict) or created_ref.get("ref") != ref:
        raise ValidationExecutionControlError(
            "Validation fixed claim ref creation failed",
            failure_code="VALIDATION_CLAIM_REF_CREATE_FAIL",
        )
    return {
        "ref": ref,
        "target_sha": executing_sha,
        "tag_object_sha": tag_object_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "actor": actor,
    }


def verify_claim_environment(
    executing_sha: str,
    *,
    repository: str,
    token: str,
    environ: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> VerifiedClaim:
    env = os.environ if environ is None else environ
    ref = claim_ref(env)
    forwarded = {
        "ref": env.get("PSR01B_VALIDATION_V1_CLAIM_REF"),
        "target_sha": env.get("PSR01B_VALIDATION_V1_CLAIM_SHA"),
        "tag_object_sha": env.get("PSR01B_VALIDATION_V1_CLAIM_TAG_OBJECT_SHA"),
        "run_id": env.get("PSR01B_VALIDATION_V1_CLAIM_RUN_ID"),
    }
    if forwarded["ref"] != ref or forwarded["target_sha"] != executing_sha:
        raise ValidationExecutionControlError(
            "forwarded Validation claim ref/SHA mismatch",
            failure_code="VALIDATION_FORWARDED_CLAIM_MISMATCH",
        )
    current_run = env.get("GITHUB_RUN_ID", "")
    current_attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    current_actor = env.get("GITHUB_ACTOR", "")
    if forwarded["run_id"] != current_run:
        raise ValidationExecutionControlError(
            "forwarded Validation claim run ID mismatch",
            failure_code="VALIDATION_FORWARDED_CLAIM_RUN_MISMATCH",
        )
    record = resolve_claim_record(repository, token, ref=ref, opener=opener)
    if record is None:
        raise ValidationExecutionControlError(
            "durable Validation claim does not exist",
            failure_code="VALIDATION_DURABLE_CLAIM_MISSING",
        )
    expected = {
        "ref": ref,
        "target_sha": executing_sha,
        "tag_object_sha": forwarded["tag_object_sha"],
        "run_id": current_run,
        "run_attempt": current_attempt,
        "actor": current_actor,
    }
    if record != expected:
        raise ValidationExecutionControlError(
            "durable Validation claim provenance mismatch",
            failure_code="VALIDATION_DURABLE_CLAIM_PROVENANCE_MISMATCH",
        )
    return VerifiedClaim(
        ref=record["ref"],
        target_sha=record["target_sha"],
        tag_object_sha=record["tag_object_sha"],
        run_id=record["run_id"],
        run_attempt=record["run_attempt"],
        actor=record["actor"],
        _marker=_VERIFIED_CLAIM_SENTINEL,
    )


def _require_verified_claim(claim: VerifiedClaim) -> None:
    if not isinstance(claim, VerifiedClaim) or claim._marker is not _VERIFIED_CLAIM_SENTINEL:
        raise ValidationExecutionControlError(
            "protected transport requires a durably verified Validation claim",
            failure_code="VALIDATION_TRANSPORT_BEFORE_VERIFIED_CLAIM",
        )
    if claim.ref != REAL_CLAIM_REF:
        raise ValidationExecutionControlError(
            "protected transport is forbidden for rehearsal claims",
            failure_code="VALIDATION_REHEARSAL_TRANSPORT_FORBIDDEN",
        )


def assert_preclaim_environment(
    *,
    repository: str,
    token: str,
    executing_sha: str,
    runner_label: str,
    freeze: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    frozen = dict(load_freeze() if freeze is None else freeze)
    provenance = verify_frozen_execution_identity(
        runner_label=runner_label, freeze=frozen, environ=env
    )
    if provenance["executing_sha"] != executing_sha:
        raise ValidationExecutionControlError(
            "workflow SHA differs from verified Validation execution SHA",
            failure_code="VALIDATION_EXECUTION_SHA_MISMATCH",
        )
    auth = verify_authorization_scope(frozen, environ=env)
    anchor = assert_review_anchor(
        provenance["candidate"],
        frozen,
        repository=repository,
        token=token,
        opener=opener,
    )
    claim_ruleset = assert_future_claim_ruleset(
        frozen, repository=repository, token=token, opener=opener
    )
    manual = assert_manual_confirmation(
        provenance["candidate"], executing_sha, environ=env
    )
    ref = claim_ref(env)
    if execution_mode(env) == "execute":
        assert_claim_absent(repository, token, ref=REAL_CLAIM_REF, opener=opener)
    else:
        # Rehearsal must prove the protected real claim is still absent as well.
        assert_claim_absent(repository, token, ref=REAL_CLAIM_REF, opener=opener)
        assert_claim_absent(repository, token, ref=ref, opener=opener)
    reservation = reserve_result_path(
        execution_result_path(env),
        candidate=provenance["candidate"],
        executing_sha=executing_sha,
    )
    return {
        **provenance,
        "authorization_scope": auth,
        "review_anchor": anchor,
        "future_claim_ruleset": claim_ruleset,
        "manual_confirmation": manual,
        "result_reservation": reservation,
        "claim_ref": ref,
    }


def assert_postclaim_environment(
    *,
    repository: str,
    token: str,
    executing_sha: str,
    runner_label: str,
    freeze: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> tuple[dict[str, Any], VerifiedClaim]:
    env = os.environ if environ is None else environ
    frozen = dict(load_freeze() if freeze is None else freeze)
    provenance = verify_frozen_execution_identity(
        runner_label=runner_label, freeze=frozen, environ=env
    )
    if provenance["executing_sha"] != executing_sha:
        raise ValidationExecutionControlError(
            "workflow SHA differs from verified Validation execution SHA",
            failure_code="VALIDATION_EXECUTION_SHA_MISMATCH",
        )
    auth = verify_authorization_scope(frozen, environ=env)
    anchor = assert_review_anchor(
        provenance["candidate"],
        frozen,
        repository=repository,
        token=token,
        opener=opener,
    )
    claim_ruleset = assert_future_claim_ruleset(
        frozen, repository=repository, token=token, opener=opener
    )
    manual = assert_manual_confirmation(
        provenance["candidate"], executing_sha, environ=env
    )
    reservation = assert_result_reservation(
        execution_result_path(env),
        candidate=provenance["candidate"],
        executing_sha=executing_sha,
    )
    verified = verify_claim_environment(
        executing_sha,
        repository=repository,
        token=token,
        environ=env,
        opener=opener,
    )
    return (
        {
            **provenance,
            "authorization_scope": auth,
            "review_anchor": anchor,
            "future_claim_ruleset": claim_ruleset,
            "manual_confirmation": manual,
            "result_reservation": reservation,
        },
        verified,
    )


def _retryable_source_error(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    return isinstance(exc, (URLError, TimeoutError, socket.timeout, ConnectionError))


def _protected_archive(name: str) -> bool:
    match = ARCHIVE_RE.fullmatch(name)
    return bool(match and int(match.group(1)) >= 2022)


def _source_url(spec: Mapping[str, Any], name: str) -> str:
    match = ARCHIVE_RE.fullmatch(name)
    if match is None:
        raise ValidationExecutionControlError(
            f"unexpected registered Validation archive name: {name}",
            failure_code="VALIDATION_ARCHIVE_NAME_INVALID",
        )
    year, month = int(match.group(1)), int(match.group(2))
    pattern = str(spec["source"]["url_pattern"])
    url = pattern.replace("{YYYY}", f"{year:04d}").replace("{MM}", f"{month:02d}")
    if not url.startswith("https://data.binance.vision/"):
        raise ValidationExecutionControlError(
            "registered Validation source URL is not exact Binance HTTPS",
            failure_code="VALIDATION_SOURCE_URL_INVALID",
        )
    return url


def _request_source_bytes(
    url: str,
    *,
    archive: str,
    attempt: int,
    kind: str,
    ledger: list[dict[str, Any]],
    state: MutableMapping[str, bool],
    opener: Callable[..., Any],
) -> tuple[bytes, dict[str, Any]]:
    state["source_access_occurred"] = True
    if _protected_archive(archive):
        state["first_protected_request_occurred"] = True
    entry: dict[str, Any] = {
        "archive": archive,
        "attempt": attempt,
        "request_kind": kind,
        "url": url,
        "accepted": False,
    }
    ledger.append(entry)
    try:
        response = opener(Request(url, method="GET"), timeout=60)
        with response:
            payload = response.read()
            entry["http_status"] = int(getattr(response, "status", 200))
            entry["outcome"] = "RESPONSE_RECEIVED"
    except Exception as exc:
        entry["outcome"] = "ERROR"
        entry["error_type"] = type(exc).__name__
        if isinstance(exc, HTTPError):
            entry["http_status"] = exc.code
        raise
    return payload, entry


def _parse_checksum(payload: bytes) -> str:
    try:
        token = payload.decode("utf-8").strip().split()[0].lower()
    except (UnicodeDecodeError, IndexError) as exc:
        raise ValidationExecutionControlError(
            "official Validation checksum document malformed",
            failure_code="VALIDATION_CHECKSUM_DOCUMENT_INVALID",
        ) from exc
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise ValidationExecutionControlError(
            "official Validation checksum value malformed",
            failure_code="VALIDATION_CHECKSUM_VALUE_INVALID",
        )
    return token


def _deterministic_raw_package(paths: Sequence[Path], destination: Path) -> None:
    destination = Path(destination).resolve()
    temporary = destination.with_name(destination.name + ".tmp")
    if destination.exists() or temporary.exists():
        raise ValidationExecutionControlError(
            "raw-source package path already exists",
            failure_code="VALIDATION_RAW_PACKAGE_NO_OVERWRITE",
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(temporary, "w") as archive:
            for path in sorted((Path(p) for p in paths), key=lambda p: p.name):
                payload = path.read_bytes()
                info = tarfile.TarInfo(name=path.name)
                info.size = len(payload)
                info.mtime = 0
                info.mode = 0o444
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                import io
                archive.addfile(info, io.BytesIO(payload))
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.link(temporary, destination)
        temporary.unlink()
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def acquire_registered_archives(
    verified_claim: VerifiedClaim,
    *,
    destination_root: Path,
    spec: Mapping[str, Any] | None = None,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
    ledger: list[dict[str, Any]] | None = None,
    accepted_records: list[dict[str, Any]] | None = None,
    state: MutableMapping[str, bool] | None = None,
) -> SourceAcquisition:
    """Acquire exact registered bytes only after a verified real claim."""
    _require_verified_claim(verified_claim)
    registration = dict(spec or validation.load_validation_spec())
    inventory = validation.registered_archive_inventory(registration)
    destination_root = Path(destination_root).resolve()
    raw_dir = destination_root / "raw_source"
    raw_dir.mkdir(parents=True, exist_ok=True)
    request_ledger = [] if ledger is None else ledger
    accepted = [] if accepted_records is None else accepted_records
    access_state: MutableMapping[str, bool] = (
        {
            "source_access_occurred": False,
            "first_protected_request_occurred": False,
        }
        if state is None
        else state
    )
    overlap = (
        registration["source"]["archive_identity_contract"][
            "historical_overlap_2020_08_through_2021_12"
        ]["sha256_from_parent_revision_4"]
    )
    latched: dict[str, str] = {}
    paths: list[Path] = []

    for name in inventory:
        url = _source_url(registration, name)
        path = raw_dir / name
        if path.exists():
            raise ValidationExecutionControlError(
                f"raw-source destination already exists: {name}",
                failure_code="VALIDATION_RAW_SOURCE_NO_OVERWRITE",
            )
        for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
            try:
                archive_bytes, archive_entry = _request_source_bytes(
                    url,
                    archive=name,
                    attempt=attempt,
                    kind="archive",
                    ledger=request_ledger,
                    state=access_state,
                    opener=opener,
                )
                checksum_bytes, checksum_entry = _request_source_bytes(
                    url + ".CHECKSUM",
                    archive=name,
                    attempt=attempt,
                    kind="checksum",
                    ledger=request_ledger,
                    state=access_state,
                    opener=opener,
                )
                official = _parse_checksum(checksum_bytes)
                digest = hashlib.sha256(archive_bytes).hexdigest()
                if digest != official:
                    raise ValidationExecutionControlError(
                        f"official Validation checksum mismatch: {name}",
                        failure_code="VALIDATION_OFFICIAL_CHECKSUM_MISMATCH",
                    )
                if name in overlap and digest != str(overlap[name]).lower():
                    raise ValidationExecutionControlError(
                        f"historical overlap identity mismatch: {name}",
                        failure_code="VALIDATION_OVERLAP_IDENTITY_MISMATCH",
                    )
                if name in latched and latched[name] != digest:
                    raise ValidationExecutionControlError(
                        f"latched Validation source identity conflict: {name}",
                        failure_code="VALIDATION_LATCHED_IDENTITY_CONFLICT",
                    )
                latched[name] = digest
                _write_bytes_exclusive(path, archive_bytes)
                archive_entry["accepted"] = True
                checksum_entry["accepted"] = True
                record = {
                    "filename": name,
                    "byte_length": len(archive_bytes),
                    "sha256": digest,
                    "official_checksum_value": official,
                    "source_url": url,
                }
                accepted.append(record)
                paths.append(path)
                break
            except Exception as exc:
                if path.exists():
                    path.unlink()
                if (
                    attempt >= MAX_DOWNLOAD_ATTEMPTS
                    or not _retryable_source_error(exc)
                ):
                    raise
                sleeper(DOWNLOAD_RETRY_DELAYS_SECONDS[attempt - 1])
        else:
            raise AssertionError("unreachable retry loop")

    manifest_record = {
        "registration_id": validation.REGISTRATION_ID,
        "claim_ref": verified_claim.ref,
        "claim_tag_object_sha": verified_claim.tag_object_sha,
        "claim_target_sha": verified_claim.target_sha,
        "archives": accepted,
    }
    validation.write_json_exclusive(
        destination_root / "raw_source_manifest.json",
        manifest_record,
    )
    _deterministic_raw_package(
        paths,
        destination_root / "psr01b_validation_raw_source_v1.tar",
    )
    return SourceAcquisition(
        tuple(paths),
        tuple(dict(item) for item in request_ledger),
        tuple(dict(item) for item in accepted),
        bool(access_state.get("source_access_occurred")),
        bool(access_state.get("first_protected_request_occurred")),
    )


def assert_result_finite_and_seeded(result: Mapping[str, Any]) -> dict[str, Any]:
    """Reject NaN/Infinity and verify registered final-model seed coordinates."""
    def walk(value: Any, path: str) -> None:
        if isinstance(value, float) and not __import__("math").isfinite(value):
            raise ValidationExecutionControlError(
                f"nonfinite Validation result value at {path}",
                failure_code="VALIDATION_RESULT_NONFINITE",
            )
        if isinstance(value, Mapping):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
    walk(result, "result")
    from . import psr01b_model
    checked = 0
    for arm in validation.ARM_ORDER:
        for fold in result["arms"][arm]["folds"]:
            expected = psr01b_model.final_seed(
                arm,
                int(fold["fold_index"]),
                int(fold["selected_trial_index"]),
            )
            if int(fold["final_model_seed"]) != expected:
                raise ValidationExecutionControlError(
                    "Validation final-model seed drift",
                    failure_code="VALIDATION_MODEL_SEED_MISMATCH",
                )
            checked += 1
    if checked != 16:
        raise ValidationExecutionControlError(
            "Validation result does not contain exact 8x2 fold seed evidence",
            failure_code="VALIDATION_SEED_EVIDENCE_COUNT_MISMATCH",
        )
    json.dumps(result, allow_nan=False)
    return {"verified_fold_seeds": checked, "json_finite": True}


def rehearsal_evidence_path(environ: Mapping[str, str] | None = None) -> Path:
    return execution_result_path(environ).parent / "rehearsal.json"


def write_rehearsal_evidence(
    verified_claim: VerifiedClaim,
    provenance: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    if execution_mode(env) != "rehearsal" or verified_claim.ref == REAL_CLAIM_REF:
        raise ValidationExecutionControlError(
            "rehearsal evidence requires a verified throwaway rehearsal claim",
            failure_code="VALIDATION_REHEARSAL_CLAIM_REQUIRED",
        )
    record = {
        "success_token": "PSR01B_VALIDATION_REHEARSAL_V1_PRE_SOURCE_PASS",
        "stage": "PRE_SOURCE",
        "market_data_accessed": False,
        "protected_validation_accessed": False,
        "oos_accessed": False,
        "execution_sha": provenance["executing_sha"],
        "candidate": provenance["candidate"],
        "run_id": verified_claim.run_id,
        "run_attempt": verified_claim.run_attempt,
        "actor": verified_claim.actor,
        "claim_ref": verified_claim.ref,
        "claim_tag_object_sha": verified_claim.tag_object_sha,
        "real_claim_ref": REAL_CLAIM_REF,
        "real_claim_created": False,
    }
    validation.write_json_exclusive(rehearsal_evidence_path(env), record)
    return record


def _write_github_output(path: str, values: Mapping[str, str]) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "claim"):
        item = sub.add_parser(name)
        item.add_argument("--repository", required=True)
        item.add_argument("--sha", required=True)
        item.add_argument("--runner-label", default="ubuntu-24.04")
        if name == "claim":
            item.add_argument("--github-output", required=True)
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise ValidationExecutionControlError(
            "GITHUB_TOKEN is required for Validation governance checks",
            failure_code="VALIDATION_GITHUB_TOKEN_MISSING",
        )
    if args.command == "preflight":
        assert_preclaim_environment(
            repository=args.repository,
            token=token,
            executing_sha=args.sha,
            runner_label=args.runner_label,
        )
        print("PSR01B_VALIDATION_PREFLIGHT_PASS")
        return 0

    freeze = load_freeze()
    provenance = verify_frozen_execution_identity(
        runner_label=args.runner_label, freeze=freeze
    )
    verify_authorization_scope(freeze)
    assert_review_anchor(
        provenance["candidate"],
        freeze,
        repository=args.repository,
        token=token,
    )
    assert_future_claim_ruleset(freeze, repository=args.repository, token=token)
    assert_manual_confirmation(provenance["candidate"], args.sha)
    assert_result_reservation(
        execution_result_path(),
        candidate=provenance["candidate"],
        executing_sha=args.sha,
    )
    assert_claim_absent(args.repository, token, ref=REAL_CLAIM_REF)
    if execution_mode() == "rehearsal":
        assert_claim_absent(args.repository, token, ref=claim_ref())
    created = create_claim(args.repository, args.sha, token)
    _write_github_output(
        args.github_output,
        {
            "claim_ref": created["ref"],
            "claim_sha": created["target_sha"],
            "claim_tag_object_sha": created["tag_object_sha"],
            "claim_run_id": created["run_id"],
        },
    )
    print("PSR01B_VALIDATION_CLAIM_CREATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
