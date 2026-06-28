"""A minimal hydration world that proves the LG-OMPC concept end to end.

A ``Human`` starts thirsty and distant from a ``WaterBottle``. The only verbs in
the world are ``walk`` (close the distance), ``pick_up`` (grab the bottle once
adjacent), and ``drink_from`` (become hydrated, emptying the bottle). No reward
shaping is hard-coded here — the controller must obtain its objective from the
language model and discover the walk → pick up → drink plan itself.

Positions are 1-D integers to keep the search tree tiny and the example
inspectable.
"""

from __future__ import annotations

from lg_ompc import (
    ActionDirection,
    ActionSpec,
    Entity,
    Environment,
    Relation,
    RelationKind,
)

BOTTLE = "water_bottle"
HUMAN = "human"


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


# -- action effects and preconditions -------------------------------------


def _can_walk(env: Environment, action) -> bool:
    actor = env.entity(action.actor)
    target = env.entity(action.target)
    return actor.state["position"] != target.state["position"]


def _walk(env: Environment, action) -> None:
    actor = env.entity(action.actor)
    target = env.entity(action.target)
    delta = _sign(target.state["position"] - actor.state["position"])
    actor.state["position"] = actor.state["position"] + delta


def _can_pick_up(env: Environment, action) -> bool:
    actor = env.entity(action.actor)
    bottle = env.entity(action.target)
    return (
        actor.state["position"] == bottle.state["position"]
        and actor.state.get("holding") is None
    )


def _pick_up(env: Environment, action) -> None:
    env.entity(action.actor).state["holding"] = action.target


def _can_drink(env: Environment, action) -> bool:
    actor = env.entity(action.actor)
    bottle = env.entity(action.target)
    return actor.state.get("holding") == action.target and bool(
        bottle.state.get("contains_water")
    )


def _drink(env: Environment, action) -> None:
    env.entity(action.actor).state["hydration"] = "high"
    env.entity(action.target).state["contains_water"] = False


WALK = ActionSpec(
    name="walk",
    direction=ActionDirection.OUTGOING,
    effect=_walk,
    precondition=_can_walk,
)
PICK_UP = ActionSpec(
    name="pick_up",
    direction=ActionDirection.INCOMING,
    effect=_pick_up,
    precondition=_can_pick_up,
)
DRINK_FROM = ActionSpec(
    name="drink_from",
    direction=ActionDirection.INCOMING,
    effect=_drink,
    precondition=_can_drink,
)


# -- entities --------------------------------------------------------------


class Human(Entity):
    """An active agent that can move and interact with objects."""

    kind = "active_agent"

    def outgoing_actions(self) -> list[ActionSpec]:
        return [WALK]

    def incoming_actions(self) -> list[ActionSpec]:
        return []


class WaterBottle(Entity):
    """A passive object that can be picked up and drunk from."""

    kind = "passive_object"

    def outgoing_actions(self) -> list[ActionSpec]:
        return []

    def incoming_actions(self) -> list[ActionSpec]:
        return [PICK_UP, DRINK_FROM]


# -- environment -----------------------------------------------------------


class HydrationWorld(Environment):
    """The toy world: hydrate the human while spending as little effort as possible."""

    def compute_relations(self) -> list[Relation]:
        human = self.entity(HUMAN)
        bottle = self.entity(BOTTLE)
        distance = abs(human.state["position"] - bottle.state["position"])
        return [
            Relation(
                kind=RelationKind.SPATIAL,
                type="distance",
                source=HUMAN,
                target=BOTTLE,
                value=float(distance),
            )
        ]

    def is_terminal(self) -> bool:
        return self.entity(HUMAN).state.get("hydration") == "high"


def build_world() -> HydrationWorld:
    """Construct a fresh, thirsty hydration world."""
    human = Human(
        name=HUMAN,
        state={"position": 0, "hydration": "low", "holding": None},
        purposes=["remain_safe", "be_hydrated", "complete_task"],
    )
    bottle = WaterBottle(
        name=BOTTLE,
        state={"position": 3, "contains_water": True},
        purposes=["hydrate_agent", "store_water", "transport_liquid"],
    )
    return HydrationWorld(
        entities=[human, bottle],
        goal="The human should become hydrated while spending as little effort as possible.",
    )
