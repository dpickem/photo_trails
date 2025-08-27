"""Tests for ingest helpers."""

import sys
from pathlib import Path

from PIL.TiffImagePlugin import IFDRational

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ingest import _gps_from_exif


def test_gps_from_exif_handles_ifdrational():
    exif = {
        "GPSInfo": {
            1: "N",  # latitude reference
            2: (IFDRational(40, 1), IFDRational(30, 1), IFDRational(0, 1)),
            3: "W",  # longitude reference
            4: (IFDRational(74, 1), IFDRational(0, 1), IFDRational(0, 1)),
        }
    }

    lat, lon = _gps_from_exif(exif)
    assert lat == 40.5
    assert lon == -74.0

