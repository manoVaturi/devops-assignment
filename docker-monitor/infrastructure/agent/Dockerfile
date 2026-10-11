FROM docker/buildx-bin:0.17.1 AS buildx
FROM docker/compose-bin:v2.29.7 AS compose
FROM aquasec/trivy:0.58.1 AS trivy

FROM python:3.12.15-slim-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    docker-cli \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --chmod=755 --from=compose /docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
COPY --chmod=755 --from=buildx /buildx /usr/local/lib/docker/cli-plugins/docker-buildx

# Trivy image scanner
COPY --chmod=755 --from=trivy /usr/local/bin/trivy /usr/local/bin/trivy
