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
from .ingest import ingest_photo


def create_app(db_path: str | Path = "photos.db") -> Flask:
    app = Flask(__name__)
    init_db(db_path)
    photo_dir = Path(app.root_path).parent / "photos"

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        message = None
        if request.method == "POST":
            file = request.files.get("photo")
            if file and file.filename:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir) / secure_filename(file.filename)
                    file.save(tmp_path)
                    photo = ingest_photo(tmp_path, data_dir=photo_dir)
                if photo is None:
                    message = "No EXIF data found; photo not ingested."
                else:
                    return redirect(url_for("index"))
            else:
                message = "No file selected."
        return render_template("upload.html", message=message)

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
