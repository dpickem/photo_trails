FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY README.md .

ENV FLASK_APP=app.web:create_app
# Default locations can be overridden at runtime via env or bind mounts
ENV PHOTO_TRAILS_DB=/data/photo_trails.db
ENV PHOTO_DATA_DIR=/data/photos

# Create data directory inside container for volume mounting
RUN mkdir -p /data/photos && chown -R root:root /data
EXPOSE 8000

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
