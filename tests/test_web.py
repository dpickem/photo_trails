"""Tests for web application endpoints."""

from pathlib import Path

from PIL import Image

from app import ingest as ingest_module
from app.database import Photo, get_session
from app.web import create_app


def _create_image(path: Path) -> None:
    img = Image.new("RGB", (1, 1))
    exif = Image.Exif()
    exif[306] = "2023:01:01 00:00:00"
    img.save(path, exif=exif)


def test_bulk_ingest_endpoint(tmp_path, monkeypatch):
    data_dir = tmp_path / "photos"
    data_dir.mkdir()
    monkeypatch.setattr(ingest_module, "PHOTO_DATA_DIR", data_dir)
    monkeypatch.setattr("app.web.PHOTO_DATA_DIR", data_dir)

    app = create_app(tmp_path / "photos.db")
    app.config["TESTING"] = True

    img1 = data_dir / "one.jpg"
    img2 = data_dir / "two.jpg"
    _create_image(img1)
    _create_image(img2)

    client = app.test_client()
    resp = client.post("/ingest-directory")
    assert resp.status_code == 302

    session = get_session()
    assert session.query(Photo).count() == 2

