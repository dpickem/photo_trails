"""Flask web application for Photo Trails."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template

from .database import Photo, get_session, init_db


def create_app(db_path: str | Path = "photos.db") -> Flask:
    app = Flask(__name__)
    init_db(db_path)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/photos")
    def photos():
        session = get_session()
        photos = session.query(Photo).all()
        data = [
            {
                "id": p.id,
                "file_path": p.file_path,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "description": p.description,
                "people": p.people.split(",") if p.people else [],
            }
            for p in photos
        ]
        return jsonify(data)

    return app
