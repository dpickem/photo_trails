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
from .ingest import PHOTO_DATA_DIR, ingest_directory, ingest_photo


def create_app(db_path: str | Path = "photos.db") -> Flask:
    app = Flask(__name__)
    init_db(db_path)
    photo_dir = PHOTO_DATA_DIR

    @app.route("/")
    def index():
        ingested = request.args.get("ingested", type=int)
        return render_template("index.html", ingested=ingested)

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        message = None
        if request.method == "POST":
            files = [f for f in request.files.getlist("photos") if f and f.filename]
            if files:
                with tempfile.TemporaryDirectory() as tmpdir:
                    for file in files:
                        tmp_path = Path(tmpdir) / secure_filename(file.filename)
                        file.save(tmp_path)
                        ingest_photo(tmp_path, data_dir=photo_dir)
                return redirect(url_for("index"))
            message = "No file selected."
            
        return render_template("upload.html", message=message)

    @app.route("/ingest-directory", methods=["POST"])
    def bulk_ingest():
        photos = ingest_directory(data_dir=photo_dir)
        return redirect(url_for("index", ingested=len(photos)))

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
