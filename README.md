# Duskmantle Knowledge Management Appliance

This repository packages a turnkey knowledge management stack that bundles the Knowledge Gateway, Qdrant, and Neo4j into a single container. It targets Esper-Lite engineers and power users who need deterministic retrieval-augmented answers and graph-backed reasoning over their own repositories without standing up infrastructure.

## Highlights
- **Single container delivery:** Supervisor launches the gateway, Qdrant, and Neo4j together with baked-in defaults.
- **Deterministic ingestion:** Periodic jobs index docs, source, tests, and protobufs with provenance and coverage reporting.
- **Graph-aware retrieval:** Combined vector search and Neo4j context power downstream LLM agents and humans alike.
- **Offline ready:** Embedding models and dependencies are vendored so the appliance runs in air-gapped environments.

## Quick Start
1. Clone this repository alongside the project you want to index.
2. Build the development image (requires Docker; Python 3.12 is only needed for local library development):
   ```bash
   docker build -t duskmantle/km:dev .
   ```
3. Run the appliance, mounting your target repository and a persistent data directory:
   ```bash
   docker run --rm \
     -p 8000:8000 \
     -v $(pwd)/data:/opt/knowledge/var \
     -v /path/to/your/repo:/workspace/repo \
     duskmantle/km:dev
   ```
4. Trigger a manual ingest (optional) in another terminal:
   ```bash
   docker exec $(docker ps -qf ancestor=duskmantle/km:dev) \
     python -m gateway.ingest.cli rebuild --profile local
   ```
5. Query the API at `http://localhost:8000/search` and explore graph endpoints under `/graph/...`.

## Repository Layout
- `docs/` — Specifications, architecture design, implementation plan, and risk mitigation playbook.
- `gateway/` — Python 3.12 application modules (API, ingestion, config, plugins).
- `infra/` — (Planned) Supervisor configs, resource profiles, helper scripts.
- `tests/` — Pytest suites and smoke tests for the turnkey appliance.
- `AGENTS.md` — Contributor guide tailored for coding agents and maintainers.

## Local Development
1. Ensure Python 3.12 is available on your workstation.
2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies (runtime + development extras):
   ```bash
   pip install -e .[dev]
   ```
4. (Optional) Install the slimmer runtime set used by the container build:
   ```bash
   pip install -r gateway/requirements.txt
   ```
5. Run the smoke tests:
   ```bash
   pytest
   ```

## Getting Involved
- Review the core specification in `docs/KNOWLEDGE_MANAGEMENT.md` and the companion design and implementation plan documents.
- Follow the practices in `AGENTS.md` for coding style, testing, and workflow expectations.
- Open issues for questions or enhancements—target users are experienced operators, so include environment details and reproduction steps.

## Roadmap References
- Architecture decisions: `docs/KNOWLEDGE_MANAGEMENT_DESIGN.md`
- Implementation phases & milestones: `docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md`
- Risk tracking and mitigations: `docs/RISK_MITIGATION_PLAN.md`

A CHANGELOG and release notes will ship once the first containerized milestone lands.
