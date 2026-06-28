"""Synthesis: use an LLM to write the objective function.

This is the language-guided heart of the framework. A Pydantic-AI agent
receives the serialized environment and goal and returns an
:class:`ObjectiveSpec` — straight Python source for an ``evaluate_objective``
function, plus a rationale and the cost terms it combined. The source is then
compiled by :mod:`lg_ompc.sandbox` into a callable the planner can score with.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from lg_ompc.environment import Environment
from lg_ompc.sandbox import (
    OBJECTIVE_FUNCTION_NAME,
    ObjectiveCallable,
    compile_objective,
)
from lg_ompc.serialization import EnvironmentDescription, describe

#: Default OpenAI model. Override with the ``LLM_MODEL`` environment variable.
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gpt-5.2")


class ObjectiveTerm(BaseModel):
    """One named component of the assembled objective."""

    name: str = Field(description="Short label, e.g. 'hydration' or 'effort'.")
    weight: float = Field(description="Relative weight (lambda) of this term.")
    rationale: str = Field(description="Why this term matters for the goal.")


class ObjectiveSpec(BaseModel):
    """The agent's structured proposal for an objective function.

    ``code`` must define a top-level ``evaluate_objective(world, history)``
    returning a float, where higher is better. ``world`` is a read-only snapshot
    of the environment and ``history`` is the list of actions taken to reach it.
    """

    code: str = Field(
        description=(
            f"Python source defining `def {OBJECTIVE_FUNCTION_NAME}(world, history) "
            "-> float`. Higher return values are better. Read entity state via "
            "world.entity('name').state.get('attr'); never mutate `world`."
        )
    )
    terms: list[ObjectiveTerm] = Field(default_factory=list)
    rationale: str = Field(
        default="", description="Overall explanation of the objective design."
    )

    def compile(self) -> ObjectiveCallable:
        """Compile :attr:`code` into a callable objective."""
        return compile_objective(self.code)


SYSTEM_PROMPT = f"""\
You are an objective-function synthesizer for a discrete-event Model Predictive
Controller. Given a structured description of an environment and a goal, you
write a Python scoring function that the planner maximizes over a short horizon.

How the planner uses your function (read carefully — this shapes your design):
- The planner looks only a FEW steps ahead (a short horizon), scores the state
  at the end of each candidate line of play, and commits just the FIRST action
  of the best line, then replans. It is greedy and myopic.
- Critically, it will only act if some action STRICTLY INCREASES your score
  within that short horizon. If standing still already scores as high as
  anything reachable in a few steps, the planner does nothing and the mission
  stalls. Your job is to make sure genuine progress always looks better, now.

Rules:
- Define exactly one top-level function:
  `def {OBJECTIVE_FUNCTION_NAME}(world, history) -> float`.
- `world` is a READ-ONLY snapshot. Read entity state with
  world.entity('name').state.get('attribute'). NEVER assign to anything on
  `world` — assignments raise an error.
- `history` is the list of actions taken to reach this state; each has
  `.name`, `.actor`, and `.target`. Use it to penalize effort (e.g. number of
  actions) when relevant.
- Return a single float where HIGHER IS BETTER. Combine weighted cost/reward
  terms; reward progress toward the goal and gently penalize effort.
- Only reference attributes that appear in the provided `attribute_map`.
- Use only basic Python and the builtins available (abs, min, max, sum, len,
  round, sorted, etc.). Do not import anything.

Designing for the short horizon (this is the most common failure mode):
- SHAPE DENSELY. Provide a smooth gradient toward the goal so that every single
  step of real progress strictly raises the score — typically a distance-based
  potential like `-w * distance_to_next_subgoal`. Do not rely only on large
  rewards that fire at a far-away milestone (pickup, delivery, terminal); the
  planner cannot see that far, so without shaping it will never start moving.
- NO STATUS-QUO TRAPS. Make sure "do nothing" / "stay where I am" is never a
  local optimum while work remains. In particular, do not let a safety,
  effort, or stay-near-home term outweigh the per-step progress reward — if
  leaving the start lowers the score more than one step of progress raises it,
  the rover freezes. Keep effort/safety penalties small relative to the
  progress gradient.
- KEEP MILESTONES MONOTONE. A milestone (reaching, picking up, depositing,
  becoming terminal) should always score higher than the best non-milestone
  state that precedes it, so the gradient leads smoothly into it.
"""


def build_agent(model: str | Model | None = None) -> Agent[None, ObjectiveSpec]:
    """Construct the synthesis agent.

    Args:
        model: An OpenAI model name (e.g. ``"gpt-5.2"``), a pre-built
            :class:`~pydantic_ai.models.Model` (such as a ``TestModel`` for
            tests), or ``None`` to use the ``LLM_MODEL`` environment variable.
            When a name is given, the OpenAI provider is configured with the
            ``LLM_API_KEY`` environment variable.
    """
    resolved: str | Model
    if model is None or isinstance(model, str):
        resolved = _openai_model(model or DEFAULT_MODEL)
    else:
        resolved = model
    return Agent(
        resolved,
        output_type=ObjectiveSpec,
        instructions=SYSTEM_PROMPT,
    )


def _openai_model(model_name: str) -> OpenAIChatModel:
    api_key = os.environ.get("LLM_API_KEY")
    provider = OpenAIProvider(api_key=api_key) if api_key else OpenAIProvider()
    return OpenAIChatModel(model_name, provider=provider)


def _render_request(description: EnvironmentDescription) -> str:
    return (
        "Synthesize an objective for the following environment.\n\n"
        f"GOAL: {description.goal}\n\n"
        "ENVIRONMENT (JSON):\n"
        f"{description.to_prompt_json()}\n\n"
        "Return an ObjectiveSpec whose `code` defines "
        f"`{OBJECTIVE_FUNCTION_NAME}(world, history)`."
    )


def synthesize_objective(
    env: Environment,
    *,
    model: str | Model | None = None,
    agent: Agent[None, ObjectiveSpec] | None = None,
) -> ObjectiveSpec:
    """Synthesize an objective for ``env`` using the LLM (synchronous).

    Args:
        env: The environment to describe and synthesize an objective for.
        model: Optional model name or :class:`Model` override.
        agent: Optional pre-built agent (e.g. with a ``TestModel`` for tests).
            When given, ``model`` is ignored.

    Note:
        This uses a blocking event loop and cannot run inside an already-running
        loop (e.g. a Jupyter kernel). In that case use
        :func:`synthesize_objective_async` with ``await`` instead.
    """
    agent = agent or build_agent(model)
    description = describe(env)
    result = agent.run_sync(_render_request(description))
    return result.output


async def synthesize_objective_async(
    env: Environment,
    *,
    model: str | Model | None = None,
    agent: Agent[None, ObjectiveSpec] | None = None,
) -> ObjectiveSpec:
    """Synthesize an objective for ``env`` using the LLM (asynchronous).

    The async counterpart of :func:`synthesize_objective`; use this inside an
    existing event loop, such as a Jupyter notebook (``await ...``).
    """
    agent = agent or build_agent(model)
    description = describe(env)
    result = await agent.run(_render_request(description))
    return result.output
