from decimal import Decimal

from research_core.provenance import ResearchResult


def test_provenance_round_trip_is_serializable() -> None:
    record = ResearchResult(
        "H-001", "S-001", "V0.1", "synthetic-v0", "2026-01-01", "2026-01-03", "1h",
        {"example": "deterministic"}, Decimal("0.001"), Decimal("0.0005"), "git:test",
        {"total_return": "0.10"}, "synthetic verification only", "continue research"
    )
    output = record.to_record()
    assert output["hypothesis_id"] == "H-001"
    assert output["transaction_cost_assumptions"] == "0.001"
