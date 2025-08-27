"""Flask web application for Photo Trails."""

from __future__ import annotations

from pathlib import Path
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
from .ingest import PHOTO_DATA_DIR, ingest_photo, ingest_directory


def create_app(db_path: str | Path = "photos.db") -> Flask:
    app = Flask(__name__)
    init_db(db_path)
    photo_dir = PHOTO_DATA_DIR
    ingest_directory(data_dir=photo_dir)

    @app.route("/")
    def index():
        message = request.args.get("message")
        return render_template("index.html", message=message)

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        message = None
        log: list[str] = []
        if request.method == "POST":
            files = [f for f in request.files.getlist("photos") if f and f.filename]
            if files:
                success = 0
                with tempfile.TemporaryDirectory() as tmpdir:
                    for file in files:
                        tmp_path = Path(tmpdir) / secure_filename(file.filename)
                        file.save(tmp_path)
                        try:
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

        return render_template("upload.html", message=message, log=log)

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
        session = get_session()
        photos = session.query(Photo).all()
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
            for p in photos
        ]
        return jsonify(data)

    return app
