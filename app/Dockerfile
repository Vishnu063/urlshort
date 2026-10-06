# ---- build stage ----
FROM python:3.12-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim
RUN useradd -r -u 10001 appuser && mkdir /data && chown appuser /data
WORKDIR /app
COPY --from=build /install /usr/local
COPY app.py index.html ./
ENV DB_PATH=/data/urls.db PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "app:app"]
