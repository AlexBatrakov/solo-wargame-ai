"""Thin JSON CLI for the orchestration-facing episode-batch runner."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.episode_batch_runner import (
    EPISODE_BATCH_OPERATION,
    FAILURE_STATUS,
    RUNNER_SCHEMA_VERSION,
    EpisodeBatchError,
    EpisodeBatchFailureResult,
    run_episode_batch_from_payload,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the episode-batch runner CLI parser."""

    parser = argparse.ArgumentParser(
        description="Run a versioned episode-batch request from stdin JSON or a request file.",
    )
    parser.add_argument(
        "--request-file",
        type=Path,
        help="Optional JSON request file. If omitted, read the request from stdin.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestration-facing episode-batch CLI."""

    args = build_parser().parse_args(argv)

    try:
        payload = _read_request_payload(args.request_file)
    except OSError as exc:
        result = _transport_failure_result(
            kind="request_validation_error",
            message=f"failed to read request input: {exc}",
        )
    except json.JSONDecodeError as exc:
        result = _transport_failure_result(
            kind="request_validation_error",
            message=f"request payload is not valid JSON: {exc}",
        )
    else:
        try:
            result = run_episode_batch_from_payload(payload)
        except Exception as exc:
            result = _transport_failure_result(
                kind="internal_error",
                message=str(exc),
            )

    print(json.dumps(result.to_payload(), indent=2, sort_keys=True))
    return 0 if result.status != FAILURE_STATUS else 1


def _read_request_payload(request_file: Path | None) -> object:
    if request_file is None:
        return json.loads(sys.stdin.read())
    return json.loads(request_file.read_text(encoding="utf-8"))


def _transport_failure_result(
    *,
    kind: str,
    message: str,
) -> EpisodeBatchFailureResult:
    return EpisodeBatchFailureResult(
        schema_version=RUNNER_SCHEMA_VERSION,
        status=FAILURE_STATUS,
        operation=EPISODE_BATCH_OPERATION,
        artifacts=(),
        warnings=(),
        error=EpisodeBatchError(kind=kind, message=message),
    )


if __name__ == "__main__":
    raise SystemExit(main())
