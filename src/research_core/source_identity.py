"""Deterministic source-artifact identity binding for Gate 1A."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

from .data_quality_treatment import ResearchTreatmentManifest


def source_identity(paths: list[Path]) -> str:
    records = []
    for path in sorted(paths, key=lambda value: value.name):
        records.append((path.name, hashlib.sha256(path.read_bytes()).hexdigest()))
    payload = json.dumps(records, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def bind_source_identity(manifest: ResearchTreatmentManifest, paths: list[Path]) -> ResearchTreatmentManifest:
    """Bind immutable raw-artifact hashes without storing filesystem paths."""
    version = f"binance-public-data-spot-1h:{source_identity(paths)}"
    base = asdict(manifest)
    base["source_version"] = version
    base.pop("dataset_identity", None)
    identity = hashlib.sha256(json.dumps(base, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    return replace(manifest, source_version=version, dataset_identity=identity)
