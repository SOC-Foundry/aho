# syntax=docker/dockerfile:1.7
# 0.2.18 W1 - base-tier production container image for aho.
#
# Multistage. Builder compiles deps into a venv; runtime layer copies the
# venv plus source. Targets <800MB final size. Python 3.14-slim base.
# No credentials baked. Tier auto-detected at runtime via aho.tier_detect.
# Health endpoints on :8080. Secrets reached via host-mounted unix socket.
#
# 0.2.18 delta from 0.2.17-rc2:
#   - OTEL_EXPORTER_OTLP_ENDPOINT default points at NZXTcos Tailscale FQDN
#     (cross-host posture per CLAUDE.md §OTEL Environment).
#   - OTEL_EXPORTER_OTLP_PROTOCOL=grpc baked as default.
#   - Source layer pulls W0 embed-timeout fix (30s→120s) automatically via COPY.
#   - aho package version bumped to 0.2.18 (pyproject.toml + __init__.py + health.py).

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/aho

COPY pyproject.toml /opt/aho/pyproject.toml
COPY src /opt/aho/src

RUN python -m venv /opt/aho/.venv \
    && /opt/aho/.venv/bin/pip install --upgrade pip wheel \
    && /opt/aho/.venv/bin/pip install -e /opt/aho

FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/aho/.venv/bin:${PATH}" \
    AHO_TIER_FILE=/var/run/aho/tier \
    AHO_HEALTH_PORT=8080 \
    AHO_SECRETS_SOCKET=/run/host-services/aho-secrets.sock \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://nzxtcos.tail8492.ts.net:4317 \
    OTEL_EXPORTER_OTLP_PROTOCOL=grpc

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/aho

COPY --from=builder /opt/aho/.venv /opt/aho/.venv
COPY --from=builder /opt/aho/src /opt/aho/src
COPY --from=builder /opt/aho/pyproject.toml /opt/aho/pyproject.toml

RUN mkdir -p /var/run/aho /var/lib/aho/chroma /var/log/aho

VOLUME /var/lib/aho/chroma

EXPOSE 8080

LABEL org.opencontainers.image.source="https://github.com/soc-foundry/aho" \
      org.opencontainers.image.description="aho base-tier container - 0.2.18 (W1 cross-host OTLP endpoint default + W0 embed-timeout fix)" \
      io.aho.iteration="0.2.18" \
      io.aho.workstream="W1"

ENTRYPOINT ["aho"]
CMD ["serve"]
