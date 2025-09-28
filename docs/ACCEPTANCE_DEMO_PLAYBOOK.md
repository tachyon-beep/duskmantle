# Acceptance Demo Playbook

This playbook captures the end-to-end validation used to sign off a release. It covers building the container, launching the stack, ingesting content, verifying search/graph responses, exercising backups/restores, and recording results for release notes.

## 1. Prerequisites

- Docker 24+ with BuildKit enabled (default).
- Python 3.12 (optional; required only for local CLI usage).
- Terminal with `curl`, `jq`, and `tar`.
- Clean working tree (`git status` shows no pending changes).
- Ensure the target repository you want to index is available locally.

### Optional: Configure Codex CLI MCP Support

If you use Codex CLI to run the demo, configure an MCP server so the CLI can call project-aware tools:

```toml
# ~/.codex/config.toml
[mcp_servers.km-server]
command = "npx"
args = ["-y", "mcp-server"]
# env entries are optional; add API keys or other secrets as needed
# env = { "API_KEY" = "value" }
```

Restart the Codex CLI after editing the config.

## 2. Build the Container Image

```bash
scripts/build-image.sh duskmantle/km:<demo-tag>
```

The script enables BuildKit and prints image metadata (ID, size, creation timestamp). Capture these details for release notes.

## 3. Launch the Stack

```bash
KM_IMAGE=duskmantle/km:<demo-tag> bin/km-run --detach
```

Defaults:

- Ports: API `8000`, Qdrant `6333`, Neo4j `7687`.
- State directory: `.duskmantle/config` mounted at `/opt/knowledge/var`.
- Repository content: `.duskmantle/data` mounted at `/workspace/repo`.
- Repo mount: current directory to `/workspace/repo`.

Wait for readiness:

```bash
for i in {1..30}; do \
  if curl -fsS http://localhost:8000/readyz >/dev/null; then echo "ready"; break; fi; \
  sleep 2; \
done
```

## 4. Run an Ingest

Run a full ingest (real embeddings) to populate Qdrant/Neo4j:

```bash
docker exec duskmantle gateway-ingest rebuild --profile demo
```

Expect logs indicating ~40 artifacts and ~314 chunks (values vary based on repo content). If you only need a smoke pass, you may add `--dummy-embeddings`, but remember to rebuild with real embeddings before running search demos (dummy embeddings produce 8-D vectors).

## 5. Verify APIs

### 5.1 Search

```bash
curl -s http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"ingestion pipeline"}' | jq '.results[0]'
```

Confirm a result returns with `chunk.artifact_path` referencing a repository file and `scoring.signals` present.

### 5.2 Graph APIs

Pre-auto-migration, Neo4j generated warnings when constraints were applied inside a transaction. Ensure migrations run successfully (no `Transaction.ForbiddenDueToTransactionType` errors). Validate the graph endpoints:

```bash
curl -s "http://localhost:8000/graph/subsystems/Kasmina?include_artifacts=true"
curl -s "http://localhost:8000/graph/nodes/DesignDoc%3Adocs%2FWORK_PACKAGES.md"
```

Expect 200 responses with node payloads. If nodes are missing, confirm ingestion populated Neo4j by running:

```bash
docker exec duskmantle /opt/knowledge/bin/neo4j-distribution/bin/cypher-shell \
  -a bolt://localhost:7687 -u neo4j -p neo4jadmin \
  "MATCH (d:DesignDoc) RETURN d.path LIMIT 5"
```

Capture any discrepancies for debugging.

## 6. Coverage Report

Confirm `/coverage` is available:

```bash
curl -s http://localhost:8000/coverage | jq '.summary'
```

Record total artifacts and chunk counts.

## 7. Backup & Restore

1. Create a backup:

   ```bash
   bin/km-backup
   ls backups
   ```

   Note the archive name.
2. Stop the container:

   ```bash
   docker rm -f duskmantle
   ```

3. Clear the data directory and restore from backup:

   ```bash
   docker run --rm -v $(pwd)/.duskmantle/config:/data alpine:3.20 sh -c "rm -rf /data/*"
   tar -xzf backups/<archive>.tgz -C .duskmantle/config
   ```

4. Relaunch the container and rerun health checks (`/readyz`, `/healthz`, `/coverage`).

## 8. Smoke Test (Automated)

```bash
./infra/smoke-test.sh duskmantle/km:<demo-tag>
```

This script builds the image, runs a container, triggers a smoke ingest (dummy embeddings), validates `/coverage`, and tears down.

## 9. Capture Results for Release Notes

Record the following in release notes or a demo log:

- Image ID, size, build timestamp.
- Ingestion run ID, artifact/chunk counts.
- Sample `/search` response.
- Graph query outputs (or troubleshooting notes if a label/property is missing).
- Coverage summary (`chunk_count`, `artifact_total`).
- Backup archive name and restore confirmation.
- Smoke test outcome.

## 10. Verify MCP Adapter

1. Install project dependencies with dev extras if not already done (`pip install -e .[dev]`).
2. In a new terminal, start the adapter against the running demo gateway:

   ```bash
   KM_GATEWAY_URL=http://localhost:8000 \
   KM_ADMIN_TOKEN=${KM_ADMIN_TOKEN:-maintainer-token} \
   gateway-mcp --transport stdio
   ```

   - Provide `KM_READER_TOKEN` if auth is enabled and you want to restrict scope. The demo typically reuses the maintainer token for both.
3. From the original terminal, run the MCP smoke marker:

   ```bash
   pytest -m mcp_smoke --maxfail=1 --disable-warnings
   ```

   This exercises `km-search`, `km-coverage-summary`, and `km-backup-trigger` over MCP. Confirm the Prometheus metrics `km_mcp_requests_total` and `km_mcp_request_seconds` increment by querying `http://localhost:8000/metrics`.
4. Stop the adapter (Ctrl+C) once verification completes.

## 11. Cleanup

```bash
docker rm -f duskmantle
rm -rf data backups
```

The environment is now back to a clean state.
