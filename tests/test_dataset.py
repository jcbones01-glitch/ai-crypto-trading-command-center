from datetime import datetime, timezone

import pytest

from research_core.data_ingestion import RESEARCH_END, RESEARCH_START
from research_core.dataset import RESEARCH_PARTITIONS, ResearchPartition, first_common_valid_timestamp, validate_partitions


def test_preregistered_partitions_are_continuous():
    validate_partitions()
    assert RESEARCH_PARTITIONS[0].start == RESEARCH_START
    assert RESEARCH_PARTITIONS[-1].end == RESEARCH_END
    assert [p.name for p in RESEARCH_PARTITIONS] == ["development", "validation", "oos"]


def test_common_start_is_deterministic():
    a = datetime(2017, 8, 17, tzinfo=timezone.utc)
    b = datetime(2017, 9, 1, tzinfo=timezone.utc)
    assert first_common_valid_timestamp(a, b) == b


def test_common_start_requires_both_verified():
    with pytest.raises(ValueError):
        first_common_valid_timestamp(None, datetime(2017, 8, 17, tzinfo=timezone.utc))


def test_partitions_reject_gaps():
    bad = (
        ResearchPartition("a", RESEARCH_START, datetime(2022, 1, 1, tzinfo=timezone.utc)),
        ResearchPartition("b", datetime(2022, 1, 2, tzinfo=timezone.utc), datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ResearchPartition("oos", datetime(2024, 1, 1, tzinfo=timezone.utc), RESEARCH_END),
    )
    with pytest.raises(ValueError):
        validate_partitions(bad)
