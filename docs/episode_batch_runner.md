# Episode Batch Runner

`solo_wargame_ai.cli.episode_batch_runner` is the orchestration-facing v1 JSON
runner for deterministic episode batches. It accepts one request object for one
`episode_batch` execution and prints one machine-readable JSON result.

Stable sample fixtures live under `docs/episode_batch_runner_samples/`:

- `request.json`
- `success_result.json`
- `failure_result.json`

The sample request uses repo-relative input paths for portability. Resolved
execution metadata and artifact paths in runtime results are absolute after
normalization.

## Supported v1 request shape

```json
{
  "schema_version": "solo_wargame_runner_v1",
  "operation": "episode_batch",
  "mission_path": "configs/missions/mission_01_secure_the_woods_1.toml",
  "policy": {
    "kind": "builtin",
    "name": "heuristic"
  },
  "seed_spec": {
    "kind": "range",
    "start": 0,
    "stop": 4
  },
  "artifact_dir": "outputs/evalynx/episode_batch_run_001",
  "write_episode_rows": true
}
```

Notes:

- `schema_version` must currently be `solo_wargame_runner_v1`.
- `operation` must currently be `episode_batch`.
- `write_episode_rows` is optional and requires `artifact_dir`.

Builtin policy names for v1:

- `random`
- `heuristic`
- `exact_guided_heuristic`

## Success result shape

```json
{
  "schema_version": "solo_wargame_runner_v1",
  "status": "succeeded",
  "operation": "episode_batch",
  "metrics": {
    "agent_name": "HeuristicAgent",
    "episode_count": 4,
    "victory_count": 3,
    "defeat_count": 1,
    "win_rate": 0.75,
    "defeat_rate": 0.25,
    "mean_terminal_turn": 5.75,
    "mean_resolved_marker_count": 4.25,
    "mean_removed_german_count": 1.5,
    "mean_player_decision_count": 10.0
  },
  "execution": {
    "mission_id": "mission_01_secure_the_woods_1",
    "mission_path": "/path/to/workdir/configs/missions/mission_01_secure_the_woods_1.toml",
    "policy": {
      "kind": "builtin",
      "name": "heuristic",
      "resolved_agent_name": "HeuristicAgent"
    },
    "seed_spec": {
      "kind": "range",
      "start": 0,
      "stop": 4
    },
    "resolved_seed_count": 4,
    "git_commit": "abcdef0",
    "git_dirty": false,
    "python_version": "3.12.0",
    "duration_sec": 0.123456
  },
  "artifacts": [
    {
      "kind": "request",
      "path": "/path/to/workdir/outputs/evalynx/episode_batch_run_001/request.json",
      "format": "json"
    },
    {
      "kind": "episode_rows",
      "path": "/path/to/workdir/outputs/evalynx/episode_batch_run_001/episodes.jsonl",
      "format": "jsonl",
      "episode_count": 4
    },
    {
      "kind": "result",
      "path": "/path/to/workdir/outputs/evalynx/episode_batch_run_001/result.json",
      "format": "json"
    }
  ],
  "warnings": []
}
```

## Failure result shape

```json
{
  "schema_version": "solo_wargame_runner_v1",
  "status": "failed",
  "operation": "episode_batch",
  "execution": {
    "mission_id": "mission_03_secure_the_building",
    "mission_path": "/path/to/workdir/configs/missions/mission_03_secure_the_building.toml",
    "policy": {
      "kind": "builtin",
      "name": "exact_guided_heuristic"
    },
    "seed_spec": {
      "kind": "range",
      "start": 0,
      "stop": 2
    },
    "git_commit": "abcdef0",
    "git_dirty": false,
    "python_version": "3.12.0",
    "duration_sec": 0.012345
  },
  "artifacts": [
    {
      "kind": "request",
      "path": "/path/to/workdir/outputs/evalynx/episode_batch_run_002/request.json",
      "format": "json"
    },
    {
      "kind": "result",
      "path": "/path/to/workdir/outputs/evalynx/episode_batch_run_002/result.json",
      "format": "json"
    }
  ],
  "warnings": [],
  "error": {
    "kind": "policy_resolution_error",
    "message": "builtin policy 'exact_guided_heuristic' does not support mission 'mission_03_secure_the_building'; supported missions: 'mission_01_secure_the_woods_1', 'mission_02_secure_the_woods_2'"
  }
}
```

## Artifact manifest entry shape

```json
{
  "kind": "result",
  "path": "/path/to/workdir/outputs/evalynx/episode_batch_run_001/result.json",
  "format": "json",
  "size_bytes": 1234,
  "description": "machine-readable episode-batch result payload",
  "episode_count": 4
}
```

Per-episode rows are never inlined by default. When requested, they are written
as `episodes.jsonl` and referenced through the artifact manifest.
