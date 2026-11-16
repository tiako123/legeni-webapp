# syntax=docker/dockerfile:1
# ---------- Étape 1 : dépendances communes ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Étape 2a : contrôle de style (docker build --target lint) ----------
FROM base AS lint
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN flake8 .

# ---------- Étape 2b : tests + couverture >= 80 % (docker build --target test) ----------
FROM base AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN mkdir -p /reports && pytest -q --junitxml=/reports/junit.xml --cov=app --cov-report=term --cov-report=xml:/reports/coverage.xml --cov-fail-under=80

# ---------- Étape 3 : image finale de production ----------
FROM base AS runtime
ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="legeni-webapp" \
      org.opencontainers.image.version="${APP_VERSION}"
ENV APP_VERSION=${APP_VERSION}
RUN useradd --create-home --uid 10001 appuser
COPY app.py .
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
