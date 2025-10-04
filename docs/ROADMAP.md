## 1) Symbol‑aware code indexing (tree‑sitter + ctags fallback)

**Why:** File‑level chunks are fine; symbol‑level results are magic for “jump to the thing I mean”.

**How to ship quickly**

* Add a **symbol extractor** pass during ingest:

  * Primary: `tree-sitter` per language (Python, TypeScript/JS, Go to start).
  * Fallback: `universal-ctags` when a language has no parser.
* Emit **symbol chunks** alongside normal chunks.
* In Neo4j: `(:Symbol {id, name, kind, lang, file, start, end})` with `(:File)-[:DECLARES]->(:Symbol)` and optional `(:Symbol)-[:CALLS]->(:Symbol)` edges (you can grow CALLS later).

**Qdrant payload (add to existing):**

```json
{
  "kind": "function",
  "symbol": "serialize_payload",
  "lang": "python",
  "file": "gateway/api/utils.py",
  "line_start": 42,
  "line_end": 87,
  "repo": "km-core",
  "subsystem": "api"
}
```

**Query operators**

* `sym:serialize_payload`, `kind:function`, `lang:python`, `file:*/utils.py`
* CLI sugar: `km-search --symbol serialize_payload`

**UI nudge**

* Chips for `kind`, `lang`, `repo`.
* “Open in editor” button per hit (see #2).

**Complexity:** Medium (tree‑sitter wiring) / Big payoff.

> Minimal Python extractor sketch (per‑file):

```python
from tree_sitter import Language, Parser
# Build once: Language.build_library('build/langs.so', ['vendor/tree-sitter-python', ...])
PY_LANG = Language('build/langs.so', 'python')
parser = Parser(); parser.set_language(PY_LANG)

def extract_symbols(code: bytes):
    tree = parser.parse(code)
    # walk the tree to collect (function|class) nodes; return name, kind, start_line, end_line
    # keep it pragmatic: only top-level + class members for v1
    return symbols
```

---

## 2) IDE deep links (one click → open at line)

**Why:** Shortens the loop from “found it” to “fix it”.

**How to ship quickly**

* Add `KM_EDITOR_URI_TEMPLATE` env (e.g., `vscode://file/{abs_path}:{line_start}`).
* On the UI hit card, render a deep‑link built from Qdrant payload `file` + `line_start`.

**API/UI nudge**

* Include `metadata.editor_uri` in `/search` responses if template is set.

**Complexity:** Low.

---

## 3) Diff‑aware ingest (“index only what changed”)

**Why:** Keeps ingest snappy and avoids re‑embedding the world.

**How to ship quickly**

* New CLI: `gateway-ingest changed --since <git-ref>` that:

  * Runs `git diff --name-only <ref>...HEAD`.
  * Re‑chunks/embeds only changed files (and deletes stale chunks).
* For non‑Git content, support a **mtime cache** under `.duskmantle/.ingest-cache.json`.

**API/UI nudge**

* `/api/v1/coverage` shows “files scanned / files changed”.
* Button: “Reindex changed since last run”.

**Complexity:** Low.

---

## 4) Lightweight re‑ranking (ONNX cross‑encoder)

**Why:** Big precision bump for top‑K with tiny code changes; ideal when your corpus is yours alone.

**How to ship quickly**

* Add an optional **re‑rank stage**:

  * Env: `KM_RERANK_MODE=cross`, `KM_RERANK_TOPK=50`, `KM_RERANK_MODEL_PATH=/models/cross-encoder.onnx`.
  * Use `onnxruntime` CPU; batch the top‑K.
* Return `scoring.rerank_score` alongside your current scores.

**API/UI nudge**

* Toggle in UI: “Improve top‑K (CPU)”.
* Display deltas: “Re‑rank moved this from #7 → #2”.

**Complexity:** Low‑Medium.

---

## 5) Time‑travel search (`as_of`) + corpus stamp

**Why:** You will regret not being able to reproduce yesterday’s answer.

**How to ship quickly**

* Stamp each ingest with `KM_CORPUS_ID = <git_sha>.<chunker_hash>.<embedder_hash>`.
* Add `?as_of=YYYY-MM-DDTHH:mm:ssZ` to `/search` to filter chunks and graph edges by valid‑time (store `since`/`until` on them).

**API/UI nudge**

* UI date‑picker: “Search as of…”.
* Every answer footer: `Corpus: <stamp>` with a copy button.

**Complexity:** Low‑Medium.

---

## 6) Query macros & operators (tiny DSL)

**Why:** Saves keystrokes and encodes your habits (“I always boost tests for bug hunts”).

**How to ship quickly**

* Load `~/.duskmantle/query_macros.yml` (or `.duskmantle/config/query_macros.yml`) with entries:

```yaml
bughunt: "error OR exception OR panic OR stacktrace -vendor -node_modules kind:file"
symfind: "sym:{0} OR file:*{0}*.py"
design:  "subsystem:{0} kind:doc doc:design OR adr"
```

* CLI: `km-search @bughunt serialization failure`

**API/UI nudge**

* UI drop‑down of macros, with preview of expanded query.

**Complexity:** Low.

---

## 7) “Answer as patch” for code results

**Why:** When the result is a function, you often want a starting patch, not prose.

**How to ship quickly**

* If a top hit is `kind:function` and you pass a short instruction, generate a **unified diff** for that file range (no LLM magic required for v1—simple text transform or templated TODO).
* Expose as `PATCH` download (`.diff`) and copy‑to‑clipboard.

**API/UI nudge**

* `POST /tools/patch-skeleton` with `{file, line_start, line_end, note}` returns a basic diff header you can hand‑edit.

**Complexity:** Low.

---

## 8) Tests ↔ symbols linking

**Why:** Gold for debugging—“show me tests that hit this function”.

**How to ship quickly**

* During ingest, simple heuristics:

  * For Python/pytest: parse `test_*` files; search for symbol names/imports; emit `(:Test)-[:EXERCISES]->(:Symbol)`.
  * Capture markers/ids so you can run `pytest -k`.
* CLI: `km-graph tests-of serialize_payload`.

**API/UI nudge**

* On a symbol hit card, list “Related tests (run)”.
* Button emits `pytest -k 'serialize_payload'`.

**Complexity:** Low‑Medium (heuristics first, refine later).

---

## 9) Local “file QA” (single‑file ephemeral index)

**Why:** Sometimes you just want to interrogate a single doc or file without polluting the main index.

**How to ship quickly**

* `km-file-qa path/to/file`:

  * Chunks + embeds to a **temp collection**.
  * Runs the same hybrid search against only that collection.
  * Auto‑expires after N minutes or on process exit.

**API/UI nudge**

* `/ui/` “Quick QA” pane with drag‑and‑drop.

**Complexity:** Low.

---

## 10) “Focus mode” filters (current repo/subsystem)

**Why:** Cuts noise when you’re buried in one area.

**How to ship quickly**

* Read current repo from a `.km-focus` file or infer from CWD in CLI.
* Default all searches to `repo:<current>` (override with `--all`).

**API/UI nudge**

* Toggle chip: “Only my current repo”.

**Complexity:** Low.

---

## 11) Snippet‑first result view (compact, copyable, line‑numbered)

**Why:** Faster skim, fewer clicks.

**How to ship quickly**

* Add line‑number rendering with **context controls** (+/‑ lines) and a **copy snippet** button.
* Provide a “token‑aware” trimming heuristic so snippets fit nicely in terminal/LLM prompts.

**API/UI nudge**

* Include `metadata.snippet_range` and `metadata.snippet_text` in `/search`.

**Complexity:** Low.

---

## 12) One‑file “workbench” logs (portable search runs)

**Why:** Keep a trail of what you asked and what you found—handy for write‑ups and handover.

**How to ship quickly**

* `--workbench my_session.jsonl` on CLI:

  * Append `{ts, query, filters, corpus_id, top_hits[..]}` for every run.
* UI toggle: “Record session”.

**API/UI nudge**

* Button: “Export session”.

**Complexity:** Low.

---

# Minimal schema & CLI tweaks (copy/paste‑able)

**Neo4j (new types/edges)**

```cypher
CREATE CONSTRAINT sym_id IF NOT EXISTS
FOR (s:Symbol) REQUIRE s.id IS UNIQUE;

CREATE INDEX sym_name IF NOT EXISTS
FOR (s:Symbol) ON (s.name);

CREATE INDEX sym_lang_kind IF NOT EXISTS
FOR (s:Symbol) ON (s.lang, s.kind);
```

**Search filter grammar (augment yours)**

```
sym:<name>         # exact or wildcard
kind:<function|class|method|test|file|doc>
lang:<python|go|ts|...>
repo:<name>        # focus mode default
file:<glob>        # supports **/*.py
as_of:<ISO8601>    # time travel
```

**ENV switches (keep it togglable)**

```
KM_SYMBOLS_ENABLED=true
KM_EDITOR_URI_TEMPLATE=vscode://file/{abs_path}:{line_start}
KM_RERANK_MODE=cross
KM_RERANK_TOPK=50
KM_WORKBENCH_PATH=.duskmantle/workbench.jsonl
```

---

## Suggested “ship order” (utility‑first)

1. **IDE deep links** → 2) **Snippet‑first view** → 3) **Focus mode** →
2. **Diff‑aware ingest** → 5) **Symbol indexing (one language first)** →
3. **Tests↔symbols** → 7) **Re‑ranking (optional)** → 8) **Time‑travel** → 9) **Macros** → 10) **File‑QA** → 11) **Workbench** → 12) **Answer‑as‑patch**.
