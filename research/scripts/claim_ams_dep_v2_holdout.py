"""Create the durable one-shot claim for AMS-DEP V2 reserved holdout execution.

This script performs governance only. It does not import the synthetic generator
or instantiate any RNG. GitHub's create-ref endpoint is used because creation is
atomic: a second creation of the same fixed ref fails instead of becoming an
idempotent "already up to date" push.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DEFAULT_CLAIM_REF = "refs/tags/ams-dep-v2-holdout-execution-claimed-v1"


class HoldoutClaimError(RuntimeError):
    """Raised when the one-shot execution claim cannot be created."""


def create_claim(
    repository: str,
    sha: str,
    token: str,
    ref: str = DEFAULT_CLAIM_REF,
    opener: Callable = urlopen,
) -> dict:
    if not repository or "/" not in repository:
        raise HoldoutClaimError("repository must be owner/name")
    if not sha:
        raise HoldoutClaimError("claim commit SHA is required")
    if ref != DEFAULT_CLAIM_REF:
        raise HoldoutClaimError("unexpected holdout claim ref")
    if not token:
        raise HoldoutClaimError("GitHub token is required")

    payload = json.dumps({"ref": ref, "sha": sha}).encode("utf-8")
    request = Request(
        f"https://api.github.com/repos/{repository}/git/refs",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ams-dep-v2-holdout-claim",
        },
    )
    try:
        response = opener(request)
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            raise HoldoutClaimError(
                f"one-shot holdout claim already exists or cannot be created: {ref}"
            ) from exc
        raise HoldoutClaimError(
            f"GitHub create-ref failed with HTTP {exc.code}"
        ) from exc

    try:
        created = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HoldoutClaimError("invalid GitHub create-ref response") from exc
    if created.get("ref") != ref:
        raise HoldoutClaimError("GitHub returned unexpected claim ref")
    if created.get("object", {}).get("sha") != sha:
        raise HoldoutClaimError("GitHub returned unexpected claim SHA")
    return {"ref": ref, "sha": sha}


def _write_github_output(path: str | None, claim: dict) -> None:
    if not path:
        return
    p = Path(path)
    with p.open("a", encoding="utf-8") as handle:
        handle.write(f"claim_ref={claim['ref']}\n")
        handle.write(f"claim_sha={claim['sha']}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--ref", default=DEFAULT_CLAIM_REF)
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    claim = create_claim(
        repository=args.repository,
        sha=args.sha,
        token=token,
        ref=args.ref,
    )
    _write_github_output(args.github_output, claim)
    print(json.dumps(claim, sort_keys=True))


if __name__ == "__main__":
    main()
