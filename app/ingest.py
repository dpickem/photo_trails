"""Photo ingestion helpers."""

from __future__ import annotations

import datetime as dt
import shutil
import warnings
from pathlib import Path

from PIL import Image, ExifTags

from .database import Photo, get_session
from .llm import describe_photo, identify_people

# Shared directory where photo data is stored
PHOTO_DATA_DIR = Path(__file__).resolve().parent.parent / "photos"


def _get_exif(image_path: Path) -> dict:
    img = Image.open(image_path)
    exif_data = img._getexif() or {}
    exif = {}
    for tag_id, value in exif_data.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        exif[tag] = value
    return exif


def _gps_from_exif(exif: dict) -> tuple[float, float] | None:
    gps_info = exif.get("GPSInfo")
    if not gps_info:
        return None

    def _convert(value):
        def _to_float(item):
            """Return a float from either an IFDRational or (num, den) tuple."""
            try:
                return float(item)
            except TypeError:
                return float(item[0]) / item[1]

        d, m, s = (_to_float(x) for x in value)
        return d + m / 60 + s / 3600

    lat = _convert(gps_info[2])
    if gps_info[1] == 'S':
        lat = -lat
    lon = _convert(gps_info[4])
    if gps_info[3] == 'W':
        lon = -lon
    return lat, lon


def ingest_photo(
    path: str | Path,
    *,
    describe: bool = False,
    identify: bool = False,
    data_dir: str | Path = PHOTO_DATA_DIR,
) -> Photo | None:
    """Ingest a single photo into the database.

    Parameters
    ----------
    path:
        Path to the image file.
    describe:
        If ``True``, request a description from the LLM.
    identify:
        If ``True``, attempt to identify known people via the LLM.
    """
    image_path = Path(path)
    exif = _get_exif(image_path)
    if not exif:
        warnings.warn(f"No EXIF data found for {image_path}, skipping ingestion")
        return None

    gps = _gps_from_exif(exif)
    taken_at = None
    if (dt_str := exif.get("DateTime")):
        try:
            taken_at = dt.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass

    description = describe_photo(image_path) if describe else None

    people = []
    if identify:
        people = identify_people(image_path)

    dest_dir = Path(data_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # If the source is already in the destination directory, avoid copying.
    if image_path.parent == dest_dir:
        dest_path = image_path
    else:
        dest_path = dest_dir / image_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{image_path.stem}_{counter}{image_path.suffix}"
            counter += 1
        shutil.copy2(image_path, dest_path)

    session = get_session()
    photo = Photo(
        file_path=str(dest_path),
        latitude=gps[0] if gps else None,
        longitude=gps[1] if gps else None,
        taken_at=taken_at,
        description=description,
        people=",".join(people) if people else None,
    )
    session.add(photo)
    session.commit()
    return photo


def ingest_directory(
    data_dir: str | Path = PHOTO_DATA_DIR,
    *,
    describe: bool = False,
    identify: bool = False,
) -> list[Photo]:
    """Ingest all photos in ``data_dir`` not already present in the DB."""

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    session = get_session()
    existing = {Path(p.file_path).name for p in session.query(Photo.file_path).all()}

    ingested: list[Photo] = []
    for path in data_dir.iterdir():
        if path.is_file() and path.name not in existing:
            photo = ingest_photo(
                path, describe=describe, identify=identify, data_dir=data_dir
            )
            if photo:
                ingested.append(photo)
    return ingested
