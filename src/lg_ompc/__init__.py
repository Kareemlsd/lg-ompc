"""LG-OMPC: Language-Guided Objective Model Predictive Control.

LG-OMPC separates *task understanding* from *action optimization*: a language
model reads a structured description of an environment and synthesizes an
objective function, while a discrete Model Predictive Controller uses that
objective to plan and act over a receding horizon.

Public building blocks for your own scenarios:

- :class:`Entity`, :class:`EntityState` — subclass to define your domain objects.
- :class:`ActionSpec`, :class:`Action`, :class:`ActionDirection`,
  :class:`InvalidAction` — declare the verbs and their contracts.
- :class:`Relation`, :class:`RelationKind` — express between-entity facts.
- :class:`Environment` — subclass to host entities and define termination.
- :func:`describe` / :class:`EnvironmentDescription` — the LLM-facing view.
- :func:`synthesize_objective` / :class:`ObjectiveSpec` — the LLM step.
- :class:`ForwardSearchPlanner` — discrete MPC by forward search.
- :class:`Controller` — the end-to-end receding-horizon loop.
"""

from __future__ import annotations

from lg_ompc.actions import (
    Action,
    ActionDirection,
    ActionSpec,
    InvalidAction,
)
from lg_ompc.controller import ControlResult, Controller
from lg_ompc.entities import Entity, EntityState
from lg_ompc.environment import Environment
from lg_ompc.planner import ForwardSearchPlanner, PlanResult
from lg_ompc.relations import Relation, RelationKind
from lg_ompc.sandbox import (
    ObjectiveError,
    compile_objective,
    evaluate,
)
from lg_ompc.serialization import (
    EntityDescription,
    EnvironmentDescription,
    RelationDescription,
    describe,
)
from lg_ompc.synthesis import (
    ObjectiveSpec,
    ObjectiveTerm,
    build_agent,
    synthesize_objective,
    synthesize_objective_async,
)

__all__ = [
    "Action",
    "ActionDirection",
    "ActionSpec",
    "InvalidAction",
    "Entity",
    "EntityState",
    "Environment",
    "Relation",
    "RelationKind",
    "describe",
    "EntityDescription",
    "EnvironmentDescription",
    "RelationDescription",
    "ObjectiveSpec",
    "ObjectiveTerm",
    "build_agent",
    "synthesize_objective",
    "synthesize_objective_async",
    "compile_objective",
    "evaluate",
    "ObjectiveError",
    "ForwardSearchPlanner",
    "PlanResult",
    "Controller",
    "ControlResult",
]
