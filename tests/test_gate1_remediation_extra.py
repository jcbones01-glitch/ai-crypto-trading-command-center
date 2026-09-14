from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from research_core.historical_dataset import ingest_archives


def test_archive_duplicate_members_are_rejected(tmp_path: Path):
    path = tmp_path / "BTCUSDT-1h-2021-01.zip"
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-1h-2021-01.csv", "1609459200000,100,105,99,103,1,0,0,0,0,0,0\n")
        archive.writestr("BTCUSDT-1h-2021-01-extra.csv", "1609459200000,100,105,99,103,1,0,0,0,0,0,0\n")
    with pytest.raises(ValueError, match="archive structure"):
        ingest_archives([path], "BTCUSDT")
