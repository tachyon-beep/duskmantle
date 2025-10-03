# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} AS builder

ENV KM_HOME=/opt/knowledge \
    VENV_PATH=/opt/knowledge/.venv \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:${PATH}"

WORKDIR ${KM_HOME}/src

COPY pyproject.toml README.md ./
COPY gateway gateway

RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS runtime

ENV KM_HOME=/opt/knowledge \
    KM_VAR=/opt/knowledge/var \
    KM_BIN=/opt/knowledge/bin \
    KM_ETC=/opt/knowledge/etc \
    KM_APP=/opt/knowledge/app \
    PATH="/opt/knowledge/.venv/bin:/opt/knowledge/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tini \
        curl \
        ca-certificates \
        bash \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1000 km \
    && adduser --system --uid 1000 --ingroup km --home ${KM_HOME} --shell /bin/bash km

RUN mkdir -p ${KM_HOME} ${KM_VAR} ${KM_BIN} ${KM_ETC} ${KM_APP} /workspace/repo \
    && chown -R km:km ${KM_HOME} /workspace

COPY --from=builder /opt/knowledge/.venv /opt/knowledge/.venv
COPY --from=builder /opt/knowledge/src/gateway ${KM_APP}/gateway
COPY --from=builder /opt/knowledge/src/pyproject.toml ${KM_APP}/pyproject.toml
COPY README.md ${KM_APP}/README.md
COPY bin ${KM_BIN}
COPY docs ${KM_HOME}/docs
COPY infra ${KM_HOME}/infra
COPY infra/docker-entrypoint.sh ${KM_BIN}/docker-entrypoint.sh

RUN find ${KM_BIN} -type f -exec chmod +x {} \; \
    && chmod +x ${KM_BIN}/docker-entrypoint.sh \
    && chown -R km:km ${KM_HOME}

USER km
WORKDIR ${KM_APP}

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/knowledge/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "gateway.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
