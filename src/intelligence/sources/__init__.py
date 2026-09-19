"""Approved deterministic external-source adapters."""

from .bls_cpi import discover_cpi_release_urls, parse_cpi_release
from .bls_employment_situation import (
    discover_employment_situation_urls,
    parse_employment_situation_release,
)
from .federal_reserve_fomc import discover_fomc_statement_urls, parse_fomc_statement

__all__ = [
    "discover_cpi_release_urls",
    "discover_employment_situation_urls",
    "discover_fomc_statement_urls",
    "parse_cpi_release",
    "parse_employment_situation_release",
    "parse_fomc_statement",
]
