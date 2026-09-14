from decimal import Decimal

import pytest

from research_core.provenance import ResearchResult


def test_provenance_round_trip_is_serializable_and_nested_data_is_immutable():
    result = ResearchResult(
        "H-001", "S-001", "V0.1", "synthetic-v0", "2026-01-01", "2026-01-03", "1h",
        {"example": {"values": [1, 2]}}, Decimal("0.001"), Decimal("0.0005"), "git:test",
        {"total_return": "0.10"}, "synthetic verification only", "continue research",
    )
    with pytest.raises(TypeError):
        result.parameters["example"] = "changed"
    with pytest.raises(TypeError):
        result.parameters["example"]["values"] = (3,)
    output = result.to_record()
    assert output["hypothesis_id"] == "H-001"
    assert output["transaction_cost_assumptions"] == "0.001"
    assert output["parameters"] == {"example": {"values": [1, 2]}}
