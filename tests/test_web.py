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


def test_upload_and_clear_endpoints(tmp_path, monkeypatch):
    data_dir = tmp_path / "photos"
    data_dir.mkdir()
    monkeypatch.setattr(ingest_module, "PHOTO_DATA_DIR", data_dir)
    monkeypatch.setattr("app.web.PHOTO_DATA_DIR", data_dir)

    pre_img = data_dir / "pre.jpg"
    _create_image(pre_img)

    app = create_app(tmp_path / "photos.db")
    app.config["TESTING"] = True

    session = get_session()
    assert session.query(Photo).count() == 1

    img1 = tmp_path / "one.jpg"
    img2 = tmp_path / "two.jpg"
    _create_image(img1)
    _create_image(img2)

    client = app.test_client()
    with img1.open("rb") as f1, img2.open("rb") as f2:
        data = {"photos": [(f1, "one.jpg"), (f2, "two.jpg")]}
        resp = client.post("/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302

    assert session.query(Photo).count() == 3

    resp = client.post("/clear-db")
    assert resp.status_code == 302
    assert session.query(Photo).count() == 0
