"""Shared test fixtures: a tiny deterministic world and a hand-written objective.

Keeping a self-contained world here (rather than importing the example) lets the
unit tests stay independent of the ``examples/`` directory layout.
"""

from __future__ import annotations

import pytest

from lg_ompc import (
    ActionDirection,
    ActionSpec,
    Entity,
    Environment,
    Relation,
    RelationKind,
)


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def _can_walk(env, action) -> bool:
    return env.entity(action.actor).state["position"] != env.entity(
        action.target
    ).state["position"]


def _walk(env, action) -> None:
    actor = env.entity(action.actor)
    target = env.entity(action.target)
    delta = _sign(target.state["position"] - actor.state["position"])
    actor.state["position"] = actor.state["position"] + delta


def _can_pick_up(env, action) -> bool:
    actor = env.entity(action.actor)
    bottle = env.entity(action.target)
    return (
        actor.state["position"] == bottle.state["position"]
        and actor.state.get("holding") is None
    )


def _pick_up(env, action) -> None:
    env.entity(action.actor).state["holding"] = action.target


def _can_drink(env, action) -> bool:
    actor = env.entity(action.actor)
    bottle = env.entity(action.target)
    return actor.state.get("holding") == action.target and bool(
        bottle.state.get("contains_water")
    )


def _drink(env, action) -> None:
    env.entity(action.actor).state["hydration"] = "high"
    env.entity(action.target).state["contains_water"] = False


WALK = ActionSpec("walk", ActionDirection.OUTGOING, _walk, _can_walk)
PICK_UP = ActionSpec("pick_up", ActionDirection.INCOMING, _pick_up, _can_pick_up)
DRINK_FROM = ActionSpec("drink_from", ActionDirection.INCOMING, _drink, _can_drink)


class Human(Entity):
    kind = "active_agent"

    def outgoing_actions(self):
        return [WALK]

    def incoming_actions(self):
        return []


class WaterBottle(Entity):
    kind = "passive_object"

    def outgoing_actions(self):
        return []

    def incoming_actions(self):
        return [PICK_UP, DRINK_FROM]


class HydrationWorld(Environment):
    def compute_relations(self):
        d = abs(
            self.entity("human").state["position"]
            - self.entity("water_bottle").state["position"]
        )
        return [
            Relation(RelationKind.SPATIAL, "distance", "human", "water_bottle", float(d))
        ]

    def is_terminal(self) -> bool:
        return self.entity("human").state.get("hydration") == "high"


def make_world(distance: int = 2) -> HydrationWorld:
    human = Human(
        "human",
        {"position": 0, "hydration": "low", "holding": None},
        purposes=["be_hydrated"],
    )
    bottle = WaterBottle(
        "water_bottle",
        {"position": distance, "contains_water": True},
        purposes=["hydrate_agent"],
    )
    return HydrationWorld([human, bottle], goal="hydrate the human cheaply")


# A correct, hand-written objective used to test the planner deterministically:
# reward hydration, shape with negative distance, and penalize effort.
HANDWRITTEN_OBJECTIVE = '''
def evaluate_objective(world, history):
    human = world.entity("human")
    bottle = world.entity("water_bottle")
    score = 0.0
    if human.state.get("hydration") == "high":
        score += 100.0
    dist = abs(human.state.get("position") - bottle.state.get("position"))
    score -= dist
    if human.state.get("holding") is not None:
        score += 5.0
    score -= 0.1 * len(history)
    return score
'''


@pytest.fixture
def world():
    return make_world()
