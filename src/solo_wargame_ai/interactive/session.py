"""In-memory resolver-backed lifecycle for a local playable session."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import (
    apply_action,
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.state import (
    DEFAULT_INITIAL_RNG_SEED,
    GameState,
    create_initial_game_state,
)

from .action_view import (
    UIActionSelection,
    build_ui_action_selection,
    state_token_from_ui_action_id,
)
from .state_view import build_state_view


class PlaySessionError(ValueError):
    """Base class for clean interactive session errors."""

    code = "play_session_error"
    status_code = 400

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-friendly error payload."""

        return {
            "error": {
                "code": self.code,
                "message": str(self),
            },
        }


class InvalidUIActionIdError(PlaySessionError):
    """Raised when a UI action id does not name a current legal action."""

    code = "invalid_action_id"
    status_code = 400


class StaleUIActionIdError(PlaySessionError):
    """Raised when a UI action id belongs to an earlier state frontier."""

    code = "stale_action_id"
    status_code = 409


class TerminalSessionError(PlaySessionError):
    """Raised when a caller tries to continue a completed mission."""

    code = "terminal_state"
    status_code = 409


@dataclass(frozen=True, slots=True)
class PlaySessionSnapshot:
    """Current state plus lightweight session bookkeeping."""

    state: GameState
    seed: int
    decision_step_count: int


class PlaySession:
    """Own one deterministic local browser play session."""

    def __init__(
        self,
        mission: Mission,
        *,
        default_seed: int = DEFAULT_INITIAL_RNG_SEED,
    ) -> None:
        self._mission = mission
        self._default_seed = default_seed
        self._snapshot: PlaySessionSnapshot | None = None
        self.reset(seed=default_seed)

    @property
    def snapshot(self) -> PlaySessionSnapshot:
        """Return the current session snapshot."""

        if self._snapshot is None:
            raise RuntimeError("PlaySession has no active state; call reset() first")
        return self._snapshot

    def reset(self, *, seed: int | None = None) -> dict[str, object]:
        """Reset the session to the initial resolver-normalized decision state."""

        chosen_seed = self._default_seed if seed is None else seed
        state = resolve_automatic_progression(
            create_initial_game_state(self._mission, seed=chosen_seed),
        )
        self._snapshot = PlaySessionSnapshot(
            state=state,
            seed=chosen_seed,
            decision_step_count=0,
        )
        return self.current_view()

    def current_view(self) -> dict[str, object]:
        """Return the current JSON-friendly session view."""

        snapshot = self.snapshot
        legal_actions = get_legal_actions(snapshot.state)
        view = build_state_view(snapshot.state, legal_actions)
        view["session"] = {
            "seed": snapshot.seed,
            "decision_step_count": snapshot.decision_step_count,
            "closed": snapshot.state.terminal_outcome is not None,
        }
        return view

    def apply_ui_action(self, action_id: str) -> dict[str, object]:
        """Apply one currently legal UI action id and return the updated view."""

        snapshot = self.snapshot
        if snapshot.state.terminal_outcome is not None:
            raise TerminalSessionError("The mission is already complete; reset to play again")

        action_selection = self._current_action_selection(snapshot.state)
        action = action_selection.actions_by_id.get(action_id)
        if action is None:
            self._raise_action_id_error(
                action_id=action_id,
                current_state_token=action_selection.state_token,
            )

        self._snapshot = PlaySessionSnapshot(
            state=apply_action(snapshot.state, action),
            seed=snapshot.seed,
            decision_step_count=snapshot.decision_step_count + 1,
        )
        return self.current_view()

    def _current_action_selection(self, state: GameState) -> UIActionSelection:
        legal_actions = get_legal_actions(state)
        return build_ui_action_selection(state, legal_actions)

    def _raise_action_id_error(
        self,
        *,
        action_id: str,
        current_state_token: str,
    ) -> None:
        supplied_state_token = state_token_from_ui_action_id(action_id)
        if supplied_state_token is not None and supplied_state_token != current_state_token:
            raise StaleUIActionIdError(
                "The selected action belongs to an earlier game state; refresh the session",
            )

        raise InvalidUIActionIdError(
            "The selected action id is not legal for the current game state",
        )


__all__ = [
    "InvalidUIActionIdError",
    "PlaySession",
    "PlaySessionError",
    "PlaySessionSnapshot",
    "StaleUIActionIdError",
    "TerminalSessionError",
]
