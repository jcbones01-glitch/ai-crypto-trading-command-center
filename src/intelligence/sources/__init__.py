"""Approved deterministic external-source adapters."""

from .federal_reserve_fomc import discover_fomc_statement_urls, parse_fomc_statement

__all__ = ["discover_fomc_statement_urls", "parse_fomc_statement"]
