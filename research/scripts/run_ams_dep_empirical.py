"""Production AMS-DEP empirical shell.

No empirical stage is currently authorized. This command intentionally exposes
only --symbol. It has no gate-path, partition, loader, Validation/OOS, P&L, or
trading options.
"""
from __future__ import annotations

import argparse

from research_core.ams_dep_empirical_access import load_development_bundle
from research_core.release_gate import assert_ams_dep_empirical_release_allowed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, choices=("BTCUSDT", "ETHUSDT"))
    args = parser.parse_args()

    # Defense in depth: the runner itself must visibly enforce the canonical
    # machine gate before delegating to the access layer, which repeats it.
    assert_ams_dep_empirical_release_allowed()
    # Under the current gate this raises before any source adapter executes.
    # Future empirical work may consume the returned verified bundle, but this
    # shell does not run inference or calculate P&L.
    bundle = load_development_bundle(args.symbol)
    print(
        "AMS_DEP_DEVELOPMENT_BUNDLE_VERIFIED "
        f"symbol={bundle.symbol} rows={len(bundle.bars)}"
    )


if __name__ == "__main__":
    main()
