# MetroFlow API
#
# Two things here are load-bearing and easy to break:
#   1. The entrypoint must be `app.main:socket_app`, not `app.main:app`. The app
#      is mounted *inside* a Socket.IO ASGI wrapper; launching the bare FastAPI
#      app serves the REST API but silently drops the realtime feed.
#   2. The healthcheck must hit /api/v1/health - the probe is registered under
#      the API prefix, and there is no unprefixed alias.
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# build-essential and libpq-dev are only needed while building wheels; psycopg2,
# numpy and scikit-learn have no manylinux wheel for every architecture.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
# The venv is built here and copied verbatim into the runtime stage: copying a
# venv whose absolute paths change between stages breaks its shebangs.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt


FROM python:3.12-slim AS runtime

# libpq5 is psycopg2's runtime dependency; curl is only for the healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 metroflow

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY --chown=metroflow:metroflow app ./app
COPY --chown=metroflow:metroflow scripts ./scripts
COPY --chown=metroflow:metroflow models_store ./models_store
COPY --chown=metroflow:metroflow data ./data
# Models are read at import time; keep the directory even if the build context
# was assembled without artifacts.
RUN mkdir -p models_store && chown -R metroflow:metroflow /app

USER metroflow
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

# One worker per container, scaled with replicas rather than --workers: the
# realtime broadcast loop and the hourly simulation clock are per-process, so
# several workers would each run their own clock over the same buckets.
#
# The simulation is left ON by default to match the previous behaviour and the CI
# job. A real deployment must set METROFLOW_ENABLE_SIMULATION=0: the simulator
# writes synthetic rows into the live tables. The app refuses to start in
# production with it enabled.
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
