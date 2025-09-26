# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ARG QDRANT_VERSION=1.7.4
ARG NEO4J_VERSION=5.28.0
ENV KM_HOME=/opt/knowledge \
    KM_VAR=/opt/knowledge/var \
    KM_BIN=/opt/knowledge/bin \
    KM_ETC=/opt/knowledge/etc \
    PATH="/opt/knowledge/.venv/bin:/opt/knowledge/bin:${PATH}"

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        unzip \
        supervisor \
        openjdk-17-jre-headless \
        procps \
        tini \ 
    && rm -rf /var/lib/apt/lists/*

# Create base directories
RUN mkdir -p ${KM_HOME}/var ${KM_BIN} ${KM_ETC} ${KM_HOME}/app

# Download and install Qdrant
RUN curl -fsSL -o /tmp/qdrant.tar.gz "https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/qdrant-${QDRANT_VERSION}-linux-x86_64-musl.tar.gz" \
    && tar -xzf /tmp/qdrant.tar.gz -C /opt/knowledge \
    && mv /opt/knowledge/qdrant-${QDRANT_VERSION} /opt/knowledge/qdrant \
    && ln -sf /opt/knowledge/qdrant/qdrant ${KM_BIN}/qdrant \
    && rm /tmp/qdrant.tar.gz

# Download and install Neo4j
RUN curl -fsSL -o /tmp/neo4j.tar.gz "https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz" \
    && tar -xzf /tmp/neo4j.tar.gz -C /opt/knowledge \
    && mv /opt/knowledge/neo4j-community-${NEO4J_VERSION} ${KM_BIN}/neo4j-distribution \
    && ln -sf ${KM_BIN}/neo4j-distribution/bin/neo4j ${KM_BIN}/neo4j \
    && rm /tmp/neo4j.tar.gz

# Set up Python environment
RUN python -m venv /opt/knowledge/.venv

WORKDIR ${KM_HOME}/app
COPY pyproject.toml README.md .
COPY gateway gateway

RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# Copy remaining project assets (docs, infra, etc.)
COPY docs docs
COPY tests tests
COPY infra ${KM_HOME}/infra

# Install supervisor configuration and entrypoint assets
RUN cp ${KM_HOME}/infra/supervisord.conf ${KM_ETC}/supervisord.conf \
    && cp ${KM_HOME}/infra/qdrant.yaml ${KM_ETC}/qdrant.yaml \
    && mkdir -p ${KM_ETC}/neo4j \
    && cp ${KM_HOME}/infra/neo4j.conf ${KM_ETC}/neo4j/neo4j.conf \
    && cp ${KM_HOME}/infra/docker-entrypoint.sh ${KM_HOME}/docker-entrypoint.sh \
    && chmod +x ${KM_HOME}/docker-entrypoint.sh

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
EXPOSE 8000 6333 6334 7474 7473 7687
VOLUME ["${KM_VAR}"]

ENTRYPOINT ["/opt/knowledge/docker-entrypoint.sh"]
