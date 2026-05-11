"""Local browser entrypoint for an interactive resolver-backed play session."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.domain.state import DEFAULT_INITIAL_RNG_SEED
from solo_wargame_ai.interactive import PlaySession
from solo_wargame_ai.interactive.server import create_play_session_server, server_url
from solo_wargame_ai.io.mission_loader import load_mission

DEFAULT_MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the local play-session CLI parser."""

    parser = argparse.ArgumentParser(
        description="Start a local browser play session for a resolver-backed mission.",
    )
    parser.add_argument(
        "--mission",
        type=Path,
        default=DEFAULT_MISSION_PATH,
        help=f"Mission TOML path. Defaults to {DEFAULT_MISSION_PATH}.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_INITIAL_RNG_SEED,
        help="Initial RNG seed. Defaults to 0.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the local server. Defaults to 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the local server. Defaults to 8765.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Start the local browser play-session server."""

    args = build_parser().parse_args(argv)
    mission = load_mission(args.mission)
    session = PlaySession(mission, default_seed=args.seed)
    server = create_play_session_server(session, host=args.host, port=args.port)

    print(f"Interactive play session: {server_url(server)}", flush=True)
    print(f"Mission: {mission.name}", flush=True)
    print(f"Seed: {args.seed}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped interactive play session.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
