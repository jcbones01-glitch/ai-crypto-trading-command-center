#!/usr/bin/env python3
"""Bounded/offline-only entry point for PSR-01B Validation V1 implementation."""

from __future__ import annotations

import argparse
import json

from research_core.psr01b_validation import verify_bounded_static_contracts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("bounded-self-check",),
        default="bounded-self-check",
    )
    args = parser.parse_args()
    if args.mode != "bounded-self-check":
        raise RuntimeError("only bounded-self-check is implemented")
    result = verify_bounded_static_contracts()
    print(json.dumps(result, sort_keys=True))
    print("PSR01B_VALIDATION_BOUNDED_SELF_CHECK_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
