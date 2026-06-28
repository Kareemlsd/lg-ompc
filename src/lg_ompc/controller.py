"""Controller: the receding-horizon loop tying everything together.

The controller synthesizes an objective once (the LLM step), then repeatedly
plans on the *true* environment, executes the single best first action, and
replans from the resulting state until the goal is reached or a step budget is
exhausted. This is the discrete analogue of receding-horizon MPC: plan over a
horizon, commit one step, repeat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lg_ompc.actions import Action
from lg_ompc.environment import Environment
from lg_ompc.planner import ForwardSearchPlanner
from lg_ompc.sandbox import ObjectiveCallable
from lg_ompc.synthesis import ObjectiveSpec, synthesize_objective

if TYPE_CHECKING:
    from pydantic_ai.models import Model


@dataclass
class ControlResult:
    """The outcome of running the control loop.

    Attributes:
        history: Actions actually executed on the true environment, in order.
        reached_goal: Whether the environment reported a terminal (goal) state.
        spec: The synthesized objective spec used, if synthesis was performed.
    """

    history: list[Action] = field(default_factory=list)
    reached_goal: bool = False
    spec: ObjectiveSpec | None = None


class Controller:
    """Run language-guided objective synthesis plus receding-horizon planning."""

    def __init__(self, horizon: int = 3, max_steps: int = 20) -> None:
        self.horizon = horizon
        self.max_steps = max_steps

    def run(
        self,
        env: Environment,
        *,
        objective: ObjectiveCallable | None = None,
        spec: ObjectiveSpec | None = None,
        model: str | "Model" | None = None,
        agent=None,
    ) -> ControlResult:
        """Drive ``env`` toward its goal.

        Provide a ready ``objective`` callable to skip the LLM entirely (handy
        for tests and baselines). Otherwise an objective is synthesized: from a
        provided ``spec`` if given, else via :func:`synthesize_objective` using
        ``model`` / ``agent``.
        """
        if objective is None:
            if spec is None:
                spec = synthesize_objective(env, model=model, agent=agent)
            objective = spec.compile()

        planner = ForwardSearchPlanner(objective, horizon=self.horizon)
        result = ControlResult(spec=spec)

        for _ in range(self.max_steps):
            if env.is_terminal():
                result.reached_goal = True
                break
            plan = planner.plan(env, history=result.history)
            if plan.action is None:
                break
            env.apply(plan.action)
            result.history.append(plan.action)

        if env.is_terminal():
            result.reached_goal = True
        return result
