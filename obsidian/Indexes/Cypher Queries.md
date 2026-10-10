---
tags:
  - "cypher"
  - "index"
---
# Cypher Queries

25 Neo4j Cypher statements in [[Hubs/Areas/Agent Graph System|Agent Graph System]].

## monitoring_agent.py → MonitoringAgent.run

**`MonitoringAgent.run()`** — line [51](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/monitoring_agent.py#L51) in [[Code/agent_graph_system/agents/monitoring_agent.py|agent_graph_system/agents/monitoring_agent.py]] · assigned to `datasets`

```cypher
MATCH (d:Dataset) RETURN d.name AS name, d.source AS source, d.last_updated AS last_updated
```

## monitoring_agent.py → MonitoringAgent._check_walkforward_coverage

**`MonitoringAgent._check_walkforward_coverage()`** — line [91](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/monitoring_agent.py#L91) in [[Code/agent_graph_system/agents/monitoring_agent.py|agent_graph_system/agents/monitoring_agent.py]] · assigned to `strategies`

```cypher
MATCH (s:Strategy) RETURN s.name AS name
```

## monitoring_agent.py → MonitoringAgent._strategy_type

**`MonitoringAgent._strategy_type()`** — line [116](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/monitoring_agent.py#L116) in [[Code/agent_graph_system/agents/monitoring_agent.py|agent_graph_system/agents/monitoring_agent.py]] · assigned to `rows`

```cypher
MATCH (s:Strategy) RETURN s.name AS name, s.strategy_type AS strategy_type
```

## orchestration_agent.py → OrchestrationAgent.run

**`OrchestrationAgent.run()`** — line [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L30) in [[Code/agent_graph_system/agents/orchestration_agent.py|agent_graph_system/agents/orchestration_agent.py]] · assigned to `stale`

```cypher
MATCH (d:Dataset) WHERE d.status = 'stale' RETURN d.name AS name, d.source AS source
```

## orchestration_agent.py → OrchestrationAgent.run

**`OrchestrationAgent.run()`** — line [37](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L37) in [[Code/agent_graph_system/agents/orchestration_agent.py|agent_graph_system/agents/orchestration_agent.py]] · assigned to `failed_pipelines`

```cypher
MATCH (p:Pipeline) WHERE p.status = 'failed' RETURN p.name AS name
```

## orchestration_agent.py → OrchestrationAgent.run

**`OrchestrationAgent.run()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L47) in [[Code/agent_graph_system/agents/orchestration_agent.py|agent_graph_system/agents/orchestration_agent.py]] · assigned to `strategies`

```cypher
MATCH (s:Strategy) RETURN s.name AS name, s.status AS status
```

## walkforward_agent.py → WalkforwardAgent._flagged_strategies

**`WalkforwardAgent._flagged_strategies()`** — line [125](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/walkforward_agent.py#L125) in [[Code/agent_graph_system/agents/walkforward_agent.py|agent_graph_system/agents/walkforward_agent.py]] · assigned to `rows`

```cypher
MATCH (s:Strategy) RETURN s.name AS name, s.status AS status
```

## walkforward_agent.py → WalkforwardAgent._strategy_type

**`WalkforwardAgent._strategy_type()`** — line [196](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/walkforward_agent.py#L196) in [[Code/agent_graph_system/agents/walkforward_agent.py|agent_graph_system/agents/walkforward_agent.py]] · assigned to `rows`

```cypher
MATCH (s:Strategy) RETURN s.name AS name, s.strategy_type AS strategy_type
```

## backend.py → graph_stats

**`graph_stats()`** — line [33](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/backend.py#L33) in [[Code/agent_graph_system/graph/backend.py|agent_graph_system/graph/backend.py]] · assigned to `nodes`

```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC
```

## backend.py → graph_stats

**`graph_stats()`** — line [34](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/backend.py#L34) in [[Code/agent_graph_system/graph/backend.py|agent_graph_system/graph/backend.py]] · assigned to `rels`

```cypher
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS count ORDER BY count DESC
```

## queries.py → notebooks_using_wrds

**`notebooks_using_wrds()`** — line [8](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L8) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (n:Notebook)-[:USES]->(d:Dataset)
WHERE d.source = 'WRDS'
RETURN n.name AS notebook, n.path AS path, d.name AS dataset, d.status AS data_status
ORDER BY n.name
```

## queries.py → stale_strategy_dependencies

**`stale_strategy_dependencies()`** — line [19](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L19) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (s:Strategy)-[:USES|DEPENDS_ON]->(d:Dataset)
WHERE d.status = 'stale'
RETURN s.name AS strategy, s.status AS strategy_status, d.name AS stale_dataset, d.last_updated AS last_updated
ORDER BY d.last_updated
```

## queries.py → backtest_lineage

**`backtest_lineage()`** — line [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L30) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (s:Strategy {name: $name})<-[:USED_BY]-(d:Dataset)
OPTIONAL MATCH (s)<-[:GENERATES]-(n:Notebook)-[:GENERATES]->(b:Backtest)
RETURN s.name AS strategy, d.name AS dataset, n.name AS notebook, b.run_id AS backtest_id,
       b.sharpe AS sharpe, b.cagr AS cagr
```

## queries.py → active_deployments

**`active_deployments()`** — line [42](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L42) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (s:Strategy)-[r:DEPLOYS_TO]->(a:API)
WHERE r.environment IN ['live', 'paper']
RETURN s.name AS strategy, a.name AS broker, r.environment AS env, r.deployed_at AS deployed_at
ORDER BY r.deployed_at DESC
```

## queries.py → pipeline_health

**`pipeline_health()`** — line [53](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L53) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (p:Pipeline)
OPTIONAL MATCH (p)-[:PRODUCES]->(d:Dataset)
RETURN p.name AS pipeline, p.status AS status, p.last_run AS last_run,
       collect(d.name) AS output_datasets
ORDER BY p.last_run
```

## queries.py → dataset_dependency_graph

**`dataset_dependency_graph()`** — line [66](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L66) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (e)-[:USES|DEPENDS_ON]->(d:Dataset {name: $name})
RETURN labels(e)[0] AS entity_type, e.name AS entity, e.status AS status
ORDER BY entity_type, e.name
```

## queries.py → full_strategy_context

**`full_strategy_context()`** — line [78](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L78) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH path = (s:Strategy {name: $name})-[*1..2]-(connected)
RETURN DISTINCT
    labels(connected)[0] AS node_type,
    connected.name AS name,
    type(relationships(path)[-1]) AS via_relationship
ORDER BY node_type, name
```

## queries.py → agent_task_graph

**`agent_task_graph()`** — line [93](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L93) in [[Code/agent_graph_system/graph/cypher/queries.py|agent_graph_system/graph/cypher/queries.py]]

```cypher
MATCH (a:Agent)-[r:MONITORS]->(target)
RETURN a.name AS agent, a.role AS role, labels(target)[0] AS watching_type,
       target.name AS watching, target.status AS target_status
ORDER BY a.name
```

## graph_models.py → latest_backtest_for_strategy

**`latest_backtest_for_strategy()`** — line [159](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L159) in [[Code/agent_graph_system/graph/neo4j/graph_models.py|agent_graph_system/graph/neo4j/graph_models.py]] · assigned to `cypher`

```cypher
MATCH (b:Backtest)
WHERE (
    EXISTS { MATCH (:Strategy {name: $name})-[:HAS_BACKTEST]->(b) }
    OR b.strategy = $name
)
AND coalesce(b.status, 'completed') NOT IN ['failed', 'running']
RETURN b AS bt
ORDER BY coalesce(b.completed_at, b.run_date, b.created_at, b.updated_at, '') DESC
LIMIT 1
```

## graph_models.py → latest_walkforward_for_strategy

**`latest_walkforward_for_strategy()`** — line [183](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L183) in [[Code/agent_graph_system/graph/neo4j/graph_models.py|agent_graph_system/graph/neo4j/graph_models.py]] · assigned to `cypher`

```cypher
MATCH (w:WalkforwardRun)
WHERE (
    EXISTS { MATCH (:Strategy {name: $name})-[:HAS_WALKFORWARD]->(w) }
    OR w.strategy = $name
)
AND coalesce(w.status, 'completed') = 'completed'
RETURN w AS wf
ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
LIMIT 1
```

## graph_models.py → latest_walkforward_for_backtest

**`latest_walkforward_for_backtest()`** — line [208](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L208) in [[Code/agent_graph_system/graph/neo4j/graph_models.py|agent_graph_system/graph/neo4j/graph_models.py]] · assigned to `cypher`

```cypher
MATCH (w:WalkforwardRun)-[:VALIDATES]->(b:Backtest {run_id: $bt})
WHERE coalesce(w.status, 'completed') = 'completed'
RETURN w AS wf
ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
LIMIT 1
```

## retriever.py → graphrag_query

**`graphrag_query()`** — line [35](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L35) in [[Code/agent_graph_system/rag/retriever.py|agent_graph_system/rag/retriever.py]] · assigned to `rows`

f-string placeholders: `{graph_hops}`, `{name_key}`, `{node_type}`

```cypher
MATCH path = (seed:{node_type} {{{name_key}: $name}})-[*1..{graph_hops}]-(neighbour)
RETURN DISTINCT
    labels(seed)[0]     AS seed_type,
    seed.name           AS seed_name,
    type(relationships(path)[-1]) AS rel,
    labels(neighbour)[0] AS neighbour_type,
    neighbour.name      AS neighbour_name,
    neighbour.status    AS neighbour_status
LIMIT 50
```

## retriever.py → stale_impact_report

**`stale_impact_report()`** — line [59](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L59) in [[Code/agent_graph_system/rag/retriever.py|agent_graph_system/rag/retriever.py]] · assigned to `stale`

```cypher
MATCH (d:Dataset) WHERE d.status = 'stale' RETURN d.name AS name, d.source AS source
```

## retriever.py → stale_impact_report

**`stale_impact_report()`** — line [64](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L64) in [[Code/agent_graph_system/rag/retriever.py|agent_graph_system/rag/retriever.py]] · assigned to `rows`

```cypher
MATCH (e)-[:USES|DEPENDS_ON|FEEDS]->(d:Dataset {name: $name})
RETURN labels(e)[0] AS type, e.name AS name, e.status AS status
```

## retriever.py → strategy_readiness

**`strategy_readiness()`** — line [77](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L77) in [[Code/agent_graph_system/rag/retriever.py|agent_graph_system/rag/retriever.py]] · assigned to `deps`

```cypher
MATCH (s:Strategy {name: $name})-[:USES|DEPENDS_ON]->(d)
RETURN labels(d)[0] AS dep_type, d.name AS dep_name, d.status AS status
```
