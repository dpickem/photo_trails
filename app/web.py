"""Flask web application for Photo Trails."""

from __future__ import annotations

from pathlib import Path
import os
import tempfile

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from .database import Photo, get_session, init_db
from .ingest import PHOTO_DATA_DIR, ingest_photo


DEFAULT_DB_PATH = Path(os.environ.get("PHOTO_TRAILS_DB", str(Path(__file__).resolve().parent.parent / "photo_trails.db")))


def create_app(db_path: str | Path = DEFAULT_DB_PATH) -> Flask:
    app = Flask(__name__)
    init_db(db_path)
    photo_dir = PHOTO_DATA_DIR
    # Startup no longer scans directory automatically; ingestion happens via uploads.

    @app.route("/")
    def index():
        message = request.args.get("message")
        return render_template("index.html", message=message)

    @app.route("/upload", methods=["POST"])
    def upload():
        message = None
        log: list[str] = []
        files = [f for f in request.files.getlist("photos") if f and f.filename]
        if files:
            success = 0
            with tempfile.TemporaryDirectory() as tmpdir:
                for file in files:
                    tmp_path = Path(tmpdir) / secure_filename(file.filename)
                    file.save(tmp_path)
                    try:
                        log.append(f"Ingesting {tmp_path} to {photo_dir}")
                        photo = ingest_photo(tmp_path, data_dir=photo_dir)
                    except Exception as exc:  # pragma: no cover - log error
                        log.append(f"{file.filename}: {exc}")
                    else:
                        success += 1
                        if photo.latitude is None or photo.longitude is None:
                            log.append(f"{file.filename}: ingested (no GPS data)")
                        else:
                            log.append(f"{file.filename}: ingested")
            message = f"{success} of {len(files)} photo(s) ingested."
        else:
            message = "No file selected."

        return jsonify({"message": message, "log": log})

    @app.route("/clear-db", methods=["POST"])
    def clear_db():
        session = get_session()
        photos = session.query(Photo).all()
        for photo in photos:
            path = Path(photo.file_path)
            if path.exists():
                path.unlink()
            session.delete(photo)
        session.commit()
        return redirect(url_for("index", message="Database cleared."))

    @app.route("/images/<path:filename>")
    def image_file(filename: str):
        """Serve ingested photo files."""
        return send_from_directory(photo_dir, filename)

    @app.route("/photos")
    def photos():
        """Return photo records, optionally paginated.

        Query params:
            - offset: starting row (default 0)
            - limit: max rows to return; if omitted, returns all (legacy behavior)
            - with_gps: if truthy, only return rows with latitude and longitude
        If limit is provided, returns an object: { items, total, offset, limit, has_more }.
        Otherwise returns a simple list (backward compatible).
        """

        session = get_session()

        # Parse query params
        try:
            offset = int(request.args.get("offset", 0))
        except Exception:
            offset = 0
        try:
            limit = int(request.args.get("limit", 0))
        except Exception:
            limit = 0
        with_gps = request.args.get("with_gps", "0").lower() in {"1", "true", "yes"}

        query = session.query(Photo)
        if with_gps:
            query = query.filter(Photo.latitude.isnot(None)).filter(Photo.longitude.isnot(None))

        if limit:
            total = query.count()
            rows = (
                query.order_by(Photo.id.asc()).offset(offset).limit(limit).all()
            )
        else:
            rows = query.order_by(Photo.id.asc()).all()

        data = [
            {
                "id": p.id,
                "file_path": p.file_path,
                "url": url_for("image_file", filename=Path(p.file_path).name),
                "latitude": p.latitude,
                "longitude": p.longitude,
                "description": p.description,
                "people": p.people.split(",") if p.people else [],
            }
            for p in rows
        ]

        if limit:
            has_more = offset + len(rows) < total
            return jsonify({
                "items": data,
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": has_more,
            })

        return jsonify(data)

    return app
