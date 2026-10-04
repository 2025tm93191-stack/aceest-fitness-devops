# syntax=docker/dockerfile:1

# ---------- base: shared settings ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser

# ---------- deps: install runtime packages only ----------
FROM base AS deps
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- test: runtime + dev tools + tests (used by CI) ----------
FROM base AS test
COPY --from=deps /install /usr/local
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
CMD ["pytest", "--cov=fitness", "--cov=app", "--cov-report=term-missing"]

# ---------- runtime: small, non-root production image (default target) ----------
FROM base AS runtime
COPY --from=deps /install /usr/local
COPY app.py .
COPY fitness/ fitness/
COPY templates/ templates/
RUN mkdir -p /app/instance && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
