# Photo Trails

Photo Trails is a minimal web application that ingests photos, stores their
locations and metadata, and visualises them on an interactive world map. EXIF
data is used for geo-coordinates when available; otherwise a placeholder LLM
integration can be used to estimate the location or describe the image.

## Development

```bash
pip install -r requirements.txt
export FLASK_APP=app.web:create_app
flask run --port=8000
```

## Docker

Build and run the container:

```bash
docker build -t photo_trails .
docker run -p 8000:8000 -v $(pwd)/photos:/photos photo_trails
```

Images placed in the `photos/` directory can then be ingested using the
`ingest_photo` helper in `app/ingest.py`.
