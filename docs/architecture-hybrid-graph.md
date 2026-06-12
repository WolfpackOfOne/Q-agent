# Hybrid Property-Graph-First Knowledge Graph Architecture

This document describes the target architecture for the Q-agent workspace graph.
It is a design reference, not an implementation checklist — pieces will be added
incrementally alongside the existing `agent_graph_system`.

---

## Guiding principle

```
Property graph for operational truth.
Policy engine for enforcement.
Learned extraction for suggestions.
Embeddings for similarity and retrieval.
Semantic validation/export as an optional audit layer.
```

The property graph is the operational source of truth.
Learned and inferred facts are suggestions — they can be promoted, but they are
never silently authoritative.

---

## System overview

```
                 +----------------------+
                 |  Agent / CLI / API    |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |     GraphWriter       |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |  GraphPolicyEngine    |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 | Property Graph Backend|
                 | Neo4j / local backend |
                 +----------+-----------+
                            |
        +-------------------+-------------------+
        |                                       |
        v                                       v
+------------------+                  +-------------------+
| GraphRetriever   |                  | GraphValidator     |
| Context packs    |                  | CI / audit checks  |
| GraphRAG         |                  | Schema checks      |
+------------------+                  +-------------------+
        |
        v
+------------------+
| Embedding index  |
| Similarity edges |
+------------------+
```

**GraphWriter** is the single write path. All writes go through the policy
engine before reaching the backend.

**GraphPolicyEngine** enforces blocking rules, logs `PolicyDecision` nodes,
and rejects writes that violate enforced policies.

**GraphValidator** runs batch checks: schema conformance, provenance
completeness, circular-dependency detection, and broken lineage checks.
It runs in CI and on demand.

**GraphRetriever** assembles context packs and GraphRAG queries. It is
read-only and must never use `SIMILAR_TO` edges as dependency evidence.

**Embedding index** backs the `SIMILAR_TO` relationship type. It is refreshed
on content-hash changes, not on every write.

---

## Fact categories

Every fact in the graph carries a `fact_status` field via the shared provenance
block (`prov_assertion_type`). The categories are:

| Category | Meaning | Can enforce? |
|---|---|---|
| `authoritative` | Declared by a human or parsed from a deterministic source | Yes |
| `extracted` | Parsed from source code, notebooks, docs, or config by an extractor | After review |
| `inferred` | Derived by a deterministic rule from authoritative facts | Yes (if rule is enforced) |
| `learned` | Suggested by an LLM or statistical model | Never directly |
| `policy_decision` | Recorded by the policy engine (allowed or denied) | Read-only record |

A `learned` fact must be explicitly promoted to `extracted` or `authoritative`
before it can trigger enforcement logic.

---

## Canonical node labels

These are the preferred labels for new ingestion and extraction work.
The legacy labels (`Agent`, `Dataset`, `Notebook`, `Backtest`) remain valid
for backward compatibility.

> **Schema reconciliation note.** The merged MyProjects ingestion pipeline
> (`agent_graph_system/ingestion/quantconnect/`) already writes `Project`,
> `File`, `Module`, `ResearchNotebook`, `Signal`, `ConfigParam`, and
> `ObjectStoreKey` nodes with specific keys and properties. The schema files
> (`ontology/schema/*.yaml`) keep those shipped definitions as the base and
> mark this design's additions as *planned (issue #54)*. Two naming caveats:
> ingestion uses `Module` for **classes** (keyed `{project}.{class_name}`),
> so the "importable unit" concept from this design is represented by `File`,
> and the planned `IMPORTS` edge is `File → File`.

### Workspace structure nodes

| Label | Description |
|---|---|
| `Project` | QuantConnect / research project under `MyProjects/` |
| `Repository` | A git repository |
| `File` | A source file tracked in the workspace graph |
| `Module` | A class defined within a project file (current ingestion schema; key `{project}.{class_name}`) |
| `Function` | A Python function or method |
| `Class` | A Python class definition (planned; ingestion currently writes classes as `Module`) |
| `Doc` | A documentation file (markdown, RST, or inline docstring) |
| `ConfigParam` | A named configuration parameter within a project or pipeline |
| `ObjectStoreKey` | A key in the QuantConnect ObjectStore |

### Strategy and research nodes

| Label | Description |
|---|---|
| `Strategy` | A trading strategy |
| `ResearchNotebook` | A marimo or Jupyter research notebook |
| `LeanBacktest` | A completed QuantConnect cloud or local backtest run |
| `Signal` | A named trading or research signal |
| `Dataset` | A data source or derived dataset |
| `Pipeline` | A data ingestion or processing pipeline |

### Agent and task nodes

| Label | Description |
|---|---|
| `Agent` | An AI agent in the system |
| `AgentTask` | A task issued to or completed by an AI agent |

### Observation and enforcement nodes

| Label | Description |
|---|---|
| `ExtractionRun` | A single run of an extractor pipeline over a source |
| `Observation` | A single fact extracted by an `ExtractionRun`, with confidence |
| `RiskFlag` | A risk or data-quality flag raised during validation |
| `PolicyDecision` | A recorded result from the policy engine |

---

## Canonical relationship types

### Structural / code-graph (hard edges — operational truth)

| Type | From → To | Meaning |
|---|---|---|
| `CONTAINS` | Repository, Project → files/notebooks/strategies | Workspace hierarchy |
| `DEFINES` | File, Module → Module, Function, Class, Signal, ConfigParam | Code structure |
| `IMPORTS` | File → File | Direct Python import |
| `DEPENDS_ON` | Notebook, Strategy, Pipeline → Dataset, Pipeline, API | Hard data dependency |
| `HAS_DOC` | Project, Strategy, Signal, … → File, Doc | Documentation link |
| `READS` | Strategy, ResearchNotebook, Pipeline → ObjectStoreKey, Dataset, File | Runtime data read |
| `WRITES` | Strategy, ResearchNotebook, Pipeline, LeanBacktest → ObjectStoreKey, Dataset, File | Runtime data write |
| `BELONGS_TO_PROJECT` | Notebook, Signal, LeanBacktest, … → Project | Project membership |

### Lineage / provenance (operational, directional)

| Type | From → To | Meaning |
|---|---|---|
| `DERIVED_FROM` | Dataset, Signal → Dataset, Pipeline | Data lineage |
| `GENERATES` | Notebook, Strategy, Pipeline → Backtest, Dataset | Output production |
| `HAS_BACKTEST` | Strategy → LeanBacktest | Strategy backtest record |
| `OBSERVED_BY` | Observation, File, Function → ExtractionRun | Extraction provenance |

### Policy / enforcement

| Type | From → To | Meaning |
|---|---|---|
| `VIOLATES` | Strategy, LeanBacktest → PolicyDecision | Policy violation record |
| `ALLOWED_BY` | Strategy, LeanBacktest → PolicyDecision | Explicit allow record |
| `DENIED_BY` | Strategy, LeanBacktest → PolicyDecision | Explicit deny record |
| `RAISES` | ExtractionRun, Pipeline → RiskFlag | Validation flag |

### Suggestion / inference (non-authoritative)

| Type | From → To | Meaning |
|---|---|---|
| `SUGGESTS` | ExtractionRun, Agent, Observation → any node | Low-trust suggestion from LLM or extractor |

### Similarity (retrieval evidence only — never dependency truth)

| Type | From → To | Meaning |
|---|---|---|
| `SIMILAR_TO` | Doc, File, ResearchNotebook, AgentTask, Signal → same | Embedding-backed semantic similarity |

!!! warning "SIMILAR_TO is not a dependency"
    `SIMILAR_TO` is retrieval evidence for GraphRAG queries, not a dependency
    or lineage edge.  Agents and query layers that need hard dependencies must
    exclude `SIMILAR_TO` edges.  The schema enforces this with a constraint
    annotation on the relationship type.

---

## Embedding and similarity design

Objects that can receive embeddings:

- `Doc`
- `File` (text-based)
- `ResearchNotebook`
- `AgentTask`
- `Signal`

Each embedding record stores: model name, dimension, `computed_at`, and
`source_hash`. When `source_hash` changes, the embedding is stale and should
be refreshed.

`SIMILAR_TO` edges are created when `similarity_score >= threshold` (default
0.80). Edges are stored with both source hashes so staleness can be detected
without re-embedding.

---

## Extraction pipelines

Each extractor produces `ExtractionRun` and `Observation` nodes.

Planned extractors:

| Extractor | Sources |
|---|---|
| `python_ast_extractor` | Python source files — modules, functions, classes, imports |
| `notebook_metadata_extractor` | Marimo / Jupyter notebooks — cells, imports, data reads |
| `markdown_doc_extractor` | Markdown docs — titles, section headings, links |
| `quantconnect_project_extractor` | `MyProjects/*/main.py`, `domain/config.py` — strategy metadata |
| `github_issue_extractor` | GitHub issue titles, labels, bodies |
| `github_pr_extractor` | Pull request metadata, review state, linked issues |
| `objectstore_usage_extractor` | `ObjectStore.Save`/`Read` calls in strategy files |

Extracted-fact metadata shape:

```yaml
source_file: MyProjects/Example/main.py
line: 42
extractor: python_ast_extractor
confidence: 0.98
observed_at: 2026-05-28T00:00:00Z
last_seen: 2026-05-28T00:00:00Z
source_hash: abc123
fact_status: extracted
```

---

## Policy engine design

The `GraphPolicyEngine` is the write-time gatekeeper.
It evaluates `enforced: true` + `severity: blocking` rules before any write
reaches the backend.

```
GraphWriter -> GraphPolicyEngine -> GraphBackend
GraphValidator -> schema/rules/provenance checks -> ValidationReport
GraphRetriever -> context-pack / GraphRAG queries
```

Policy result shape:

```json
{
  "allowed": false,
  "code": "DEPLOYMENT_GATE_FAILED",
  "message": "Latest completed backtest Sharpe is below threshold",
  "evidence": [
    {"node": "LeanBacktest:bt_2026_05_27", "metric": "sharpe", "value": 0.42}
  ]
}
```

Every decision is recorded as a `PolicyDecision` node and linked to the
affected node via `VIOLATES`, `ALLOWED_BY`, or `DENIED_BY`.

---

## Migration path from current YAML ontology

| Current file | Target in hybrid model |
|---|---|
| `schema/entities.yaml` | Node labels and node schemas (both files coexist; new labels added below legacy labels) |
| `schema/relationships.yaml` | Relationship types and property schemas (same file, new types appended) |
| `ontology/rules.yaml` | Policy rules (`status: enforced`) and validation checks (`status: documented`) |
| `graph/cypher/queries.py` | Named query layer and context-pack query layer |
| `ingestion/*` | Extraction pipelines; output `ExtractionRun` and `Observation` nodes |

Current entity labels (`Agent`, `Dataset`, `Notebook`, `Backtest`, `Repository`,
`Pipeline`, `API`, `FactorModel`, `Filing`, `Security`, `Workflow`) are preserved
as-is. The hybrid architecture adds new labels alongside them.

The recommended migration sequence:

1. New ingestion work uses the hybrid labels (`Project`, `File`, `Module`, etc.).
2. Existing nodes are optionally re-labelled in a migration script — never
   destructively in-place.
3. Rules in `rules.yaml` are audited and each is confirmed as either
   `enforced`, `documented`, or `disabled`.
4. Semantic export (RDF/JSON-LD) is added as a read-only audit layer after
   the operational graph is stable.

---

## Test and fixture plans

### Schema validation tests

- Each entity in `entities.yaml` deserialises without error.
- Each relationship in `relationships.yaml` references known entity labels.
- Required provenance fields are present on extracted/inferred nodes.
- `fact_status: learned` nodes cannot appear as the source of `DEPENDS_ON`,
  `IMPORTS`, or `READS` edges.

### Policy enforcement tests

- `deployment_gate` rule blocks a `Strategy → LeanBacktest` write when
  `sharpe < 0.5`.
- `deployment_gate` rule allows the write when `sharpe >= 0.5`.
- Every blocked write produces a `PolicyDecision` node with `allowed: false`.
- `VIOLATES` edge is created for each blocked write.

### Extraction confidence tests

- `python_ast_extractor` golden fixture: given a known Python file, the
  extracted `Function` and `Class` nodes match expected names and line numbers.
- Confidence scores for deterministic AST extraction are >= 0.95.
- Re-running an extractor on the same file updates `last_seen` without
  creating duplicate `Observation` nodes.

### Similarity edge tests

- `SIMILAR_TO` edges are never created between identical nodes (`a == b`).
- `similarity_score` is always in [0.0, 1.0].
- A query for `DEPENDS_ON` transitive closure must return zero `SIMILAR_TO`
  edges.
- Stale similarity edges (source hash changed) are detected and flagged.

### Migration tests

- All legacy entity labels load without error after schema expansion.
- A sample `entities.yaml` with both legacy and hybrid labels passes
  the schema validator.
