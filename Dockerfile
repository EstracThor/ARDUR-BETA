FROM python:3.14-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends gdal-bin libgdal36 libgeos-c1t64 libproj25 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --uid 10001 --create-home ardur && mkdir -p /app/media /app/staticfiles && chown -R ardur:ardur /app
USER ardur
EXPOSE 8000
CMD ["sh", "scripts/web.sh"]
