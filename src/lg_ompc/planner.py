"""Planner: discrete Model Predictive Control by forward search.

In a discrete action space, MPC reduces to finite-horizon look-ahead: from the
current state, exhaustively expand every applicable action up to ``horizon``
steps, score each resulting leaf with the synthesized objective, and return the
first action of the best-scoring trajectory. The controller then executes that
single action and replans — the receding horizon.

Exhaustive expansion is intentional for the MVP: it is simple, complete for
small problems, and easy to reason about. Swap in beam search or MCTS behind the
same :meth:`ForwardSearchPlanner.plan` interface when branching grows.
"""

from __future__ import annotations

from dataclasses import dataclass

from lg_ompc.actions import Action
from lg_ompc.environment import Environment
from lg_ompc.sandbox import ObjectiveCallable, evaluate


@dataclass
class PlanResult:
    """The outcome of a planning call.

    Attributes:
        action: The best first action to execute, or ``None`` if no action is
            applicable.
        score: The objective value of the best trajectory found.
        trajectory: The full sequence of actions in that best trajectory.
    """

    action: Action | None
    score: float
    trajectory: list[Action]


class ForwardSearchPlanner:
    """Finite-horizon exhaustive forward-search planner."""

    def __init__(self, objective: ObjectiveCallable, horizon: int = 3) -> None:
        if horizon < 1:
            raise ValueError("horizon must be at least 1")
        self.objective = objective
        self.horizon = horizon

    def plan(
        self, env: Environment, history: list[Action] | None = None
    ) -> PlanResult:
        """Return the best first action from ``env`` without mutating it.

        Args:
            env: Current true state (left untouched; the planner explores clones).
            history: Actions already executed before this state, so the objective
                can account for cumulative effort. Defaults to empty.
        """
        score, trajectory = self._search(
            env, depth=self.horizon, path=list(history or [])
        )
        action = trajectory[0] if trajectory else None
        return PlanResult(action=action, score=score, trajectory=trajectory)

    def _search(
        self, env: Environment, depth: int, path: list[Action]
    ) -> tuple[float, list[Action]]:
        best_score = evaluate(self.objective, env, path)
        best_trajectory: list[Action] = []

        if depth == 0 or env.is_terminal():
            return best_score, best_trajectory

        for action in env.available_actions():
            branch = env.clone()
            cloned_action = action.spec.bind(
                actor=action.actor, target=action.target, **action.params
            )
            branch.apply(cloned_action)
            score, tail = self._search(branch, depth - 1, [*path, cloned_action])
            if score > best_score:
                best_score = score
                best_trajectory = [cloned_action, *tail]

        return best_score, best_trajectory
