"""Tests for ingest helpers."""

import sys
from pathlib import Path

from PIL import Image
from PIL.TiffImagePlugin import IFDRational

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import Photo, get_session, init_db
from app.ingest import _gps_from_exif, ingest_directory, ingest_photo


def _create_image(path: Path) -> None:
    """Create a tiny JPEG file with minimal EXIF data."""
    img = Image.new("RGB", (1, 1))
    exif = Image.Exif()
    exif[306] = "2023:01:01 00:00:00"  # DateTime tag to ensure EXIF exists
    img.save(path, exif=exif)


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


def test_ingest_photo_unique_names(tmp_path):
    init_db(tmp_path / "photos.db")
    src1 = tmp_path / "src1"
    src2 = tmp_path / "src2"
    data_dir = tmp_path / "data"
    src1.mkdir()
    src2.mkdir()
    img1 = src1 / "test.jpg"
    img2 = src2 / "test.jpg"
    _create_image(img1)
    _create_image(img2)

    ingest_photo(img1, data_dir=data_dir)
    ingest_photo(img2, data_dir=data_dir)

    files = sorted(p.name for p in data_dir.iterdir())
    assert len(files) == 2
    assert files[0] != files[1]

    session = get_session()
    assert session.query(Photo).count() == 2


def test_ingest_directory_skips_existing(tmp_path):
    init_db(tmp_path / "bulk.db")
    data_dir = tmp_path / "photos"
    data_dir.mkdir()
    img1 = data_dir / "one.jpg"
    img2 = data_dir / "two.jpg"
    _create_image(img1)
    _create_image(img2)

    ingest_directory(data_dir)
    session = get_session()
    assert session.query(Photo).count() == 2

    # Second call should not duplicate entries
    ingest_directory(data_dir)
    assert session.query(Photo).count() == 2

