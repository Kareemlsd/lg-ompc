"""A 2-D sample-return world that stretches LG-OMPC past the toy case.

A single ``Rover`` roams a small grid. Scattered across it are several rock
``Sample`` s, each with a different *scientific value*, and a ``Lander`` the
rover must return them to. Every move drains a finite ``battery``. There is no
single "correct" plan baked into the world: with enough charge the rover can
fetch everything, but when the battery is tight it must decide *which* samples
are worth the trip — a value-vs-effort trade-off that nobody hard-codes.

That decision is exactly what the language-guided objective supplies. The world
only defines what *can* happen (affordances, preconditions, effects); the
synthesized objective decides what *should* happen (which samples, in what
order, and when to head home).

Coordinates are small integers on a grid so the search tree stays inspectable
and the whole episode plots cleanly.
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

ROVER = "rover"
LANDER = "lander"


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def _pos(entity) -> tuple[int, int]:
    return entity.state["x"], entity.state["y"]


def _manhattan(a, b) -> int:
    return abs(a.state["x"] - b.state["x"]) + abs(a.state["y"] - b.state["y"])


# -- action effects and preconditions -------------------------------------


def _move_targets(env: Environment, actor: str) -> list[str]:
    """Landmarks worth heading toward: the lander, plus any sample still out there.

    A sample already on the rover or already deposited is not a movement target;
    you either carry it home or it is already home.
    """
    targets = [LANDER]
    for name, entity in env.entities.items():
        if getattr(entity, "kind", "") != "sample":
            continue
        if entity.state.get("collected") or entity.state.get("deposited"):
            continue
        targets.append(name)
    return targets


def _can_move(env: Environment, action) -> bool:
    rover = env.entity(action.actor)
    target = env.entity(action.target)
    return rover.state["battery"] > 0 and _pos(rover) != _pos(target)


def _move(env: Environment, action) -> None:
    """Take one grid step toward the target, closing the larger axis gap first."""
    rover = env.entity(action.actor)
    target = env.entity(action.target)
    dx = target.state["x"] - rover.state["x"]
    dy = target.state["y"] - rover.state["y"]
    if abs(dx) >= abs(dy) and dx != 0:
        rover.state["x"] += _sign(dx)
    else:
        rover.state["y"] += _sign(dy)
    rover.state["battery"] -= 1


def _can_collect(env: Environment, action) -> bool:
    rover = env.entity(action.actor)
    sample = env.entity(action.target)
    return (
        rover.state.get("carrying") is None
        and not sample.state.get("collected")
        and not sample.state.get("deposited")
        and _pos(rover) == _pos(sample)
    )


def _collect(env: Environment, action) -> None:
    env.entity(action.actor).state["carrying"] = action.target
    env.entity(action.target).state["collected"] = True


def _can_deposit(env: Environment, action) -> bool:
    rover = env.entity(action.actor)
    sample = env.entity(action.target)
    lander = env.entity(LANDER)
    return rover.state.get("carrying") == action.target and _pos(rover) == _pos(lander)


def _deposit(env: Environment, action) -> None:
    rover = env.entity(action.actor)
    sample = env.entity(action.target)
    sample.state["deposited"] = True
    sample.state["collected"] = False
    rover.state["carrying"] = None


MOVE = ActionSpec(
    name="move",
    direction=ActionDirection.OUTGOING,
    effect=_move,
    precondition=_can_move,
    enumerate_targets=_move_targets,
)
COLLECT = ActionSpec(
    name="collect",
    direction=ActionDirection.INCOMING,
    effect=_collect,
    precondition=_can_collect,
)
DEPOSIT = ActionSpec(
    name="deposit",
    direction=ActionDirection.INCOMING,
    effect=_deposit,
    precondition=_can_deposit,
)


# -- entities --------------------------------------------------------------


class Rover(Entity):
    """The active agent: drives the grid, collects samples, returns them home."""

    kind = "active_agent"

    def outgoing_actions(self) -> list[ActionSpec]:
        return [MOVE]

    def incoming_actions(self) -> list[ActionSpec]:
        return []


class Sample(Entity):
    """A passive rock with a scientific ``value`` that can be collected and deposited."""

    kind = "sample"

    def outgoing_actions(self) -> list[ActionSpec]:
        return []

    def incoming_actions(self) -> list[ActionSpec]:
        return [COLLECT, DEPOSIT]


class Lander(Entity):
    """An inert landmark: the drop-off point. It offers and accepts no actions."""

    kind = "landmark"

    def outgoing_actions(self) -> list[ActionSpec]:
        return []

    def incoming_actions(self) -> list[ActionSpec]:
        return []


# -- environment -----------------------------------------------------------


class RoverWorld(Environment):
    """A grid world where samples must be returned to the lander on a battery budget."""

    def update(self) -> None:
        """A carried sample rides along with the rover."""
        rover = self.entity(ROVER)
        carried = rover.state.get("carrying")
        if carried is not None:
            sample = self.entity(carried)
            sample.state["x"] = rover.state["x"]
            sample.state["y"] = rover.state["y"]

    def samples(self) -> list[Entity]:
        return [e for e in self.entities.values() if getattr(e, "kind", "") == "sample"]

    def compute_relations(self) -> list[Relation]:
        rover = self.entity(ROVER)
        relations = [
            Relation(
                kind=RelationKind.SPATIAL,
                type="distance",
                source=ROVER,
                target=LANDER,
                value=float(_manhattan(rover, self.entity(LANDER))),
            )
        ]
        for sample in self.samples():
            if sample.state.get("deposited"):
                continue
            relations.append(
                Relation(
                    kind=RelationKind.SPATIAL,
                    type="distance",
                    source=ROVER,
                    target=sample.name,
                    value=float(_manhattan(rover, sample)),
                )
            )
        return relations

    def is_terminal(self) -> bool:
        return all(s.state.get("deposited") for s in self.samples())


def build_world(battery: int = 30) -> RoverWorld:
    """Construct a fresh sample-return mission.

    Args:
        battery: Movement budget. ~24 steps are needed to fetch all three
            samples and return; lower it to force a value-vs-effort decision.
    """
    rover = Rover(
        name=ROVER,
        state={"x": 0, "y": 0, "battery": battery, "carrying": None},
        purposes=["return_samples", "conserve_battery", "survive"],
    )
    lander = Lander(name=LANDER, state={"x": 0, "y": 0})
    basalt = Sample(
        name="basalt_sample",
        state={"x": 4, "y": 1, "value": 3, "collected": False, "deposited": False},
        purposes=["be_returned"],
    )
    ice_core = Sample(
        name="ice_core",
        state={"x": 2, "y": 4, "value": 5, "collected": False, "deposited": False},
        purposes=["be_returned"],
    )
    meteorite = Sample(
        name="meteorite",
        state={"x": 5, "y": 5, "value": 8, "collected": False, "deposited": False},
        purposes=["be_returned"],
    )
    return RoverWorld(
        entities=[rover, lander, basalt, ice_core, meteorite],
        goal=(
            "Collect the rock samples and return each one to the lander. Samples "
            "differ in scientific value (higher is better) — prefer the most "
            "valuable ones. Every move costs battery, so spend it wisely; if the "
            "battery is too low to fetch everything, secure the best samples you "
            "can and return them rather than stranding the rover."
        ),
    )
