"""The Environment: the true interactive system and Discrete-Event engine.

The environment owns the authoritative entity registry and relation set, knows
which actions are currently applicable, applies them, and can :meth:`clone`
itself so the planner can explore hypothetical futures without disturbing the
real state. This is the world the controller acts upon — distinct from any
world model used for prediction.
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod

from lg_ompc.actions import Action, ActionDirection
from lg_ompc.entities import Entity
from lg_ompc.relations import Relation


class Environment(ABC):
    """Base class for a discrete-event environment.

    Subclasses populate ``entities`` and override :meth:`compute_relations`,
    :meth:`is_terminal`, and optionally :meth:`update`. The base class provides
    the registry, action enumeration, application, and branch-isolated cloning
    that the planner relies on.
    """

    def __init__(
        self,
        entities: list[Entity] | None = None,
        goal: str = "",
    ) -> None:
        self._entities: dict[str, Entity] = {}
        for entity in entities or []:
            self.add_entity(entity)
        self.goal = goal

    # -- registry ---------------------------------------------------------

    def add_entity(self, entity: Entity) -> None:
        if entity.name in self._entities:
            raise ValueError(f"Duplicate entity name: {entity.name!r}")
        self._entities[entity.name] = entity

    @property
    def entities(self) -> dict[str, Entity]:
        """The live entity registry keyed by name."""
        return self._entities

    def entity(self, name: str) -> Entity:
        """Look up an entity by name.

        Raises:
            KeyError: if no entity with that name exists.
        """
        return self._entities[name]

    # -- relations --------------------------------------------------------

    def compute_relations(self) -> list[Relation]:
        """Return the current relations between entities.

        Default is no relations; override to expose distances, containment, or
        ordering that objectives may depend on.
        """
        return []

    # -- dynamics ---------------------------------------------------------

    def available_actions(self) -> list[Action]:
        """Enumerate every currently-applicable action across all entities.

        Outgoing actions are bound to their owning entity as actor; incoming
        actions are bound with every active entity as a candidate actor. Targets
        come from each spec's ``enumerate_targets`` (defaulting to all other
        entities). Only actions whose preconditions hold are returned.
        """
        actions: list[Action] = []

        for entity in self._entities.values():
            for spec in entity.outgoing_actions():
                for action in self._bind_with_targets(spec, actor=entity.name):
                    if action.is_applicable(self):
                        actions.append(action)

        for target_entity in self._entities.values():
            for spec in target_entity.incoming_actions():
                for actor in self._active_actor_names():
                    if actor == target_entity.name:
                        continue
                    action = spec.bind(actor=actor, target=target_entity.name)
                    if action.is_applicable(self):
                        actions.append(action)

        return actions

    def _bind_with_targets(self, spec, actor: str) -> list[Action]:
        if spec.enumerate_targets is not None:
            targets = spec.enumerate_targets(self, actor)
            return [spec.bind(actor=actor, target=t) for t in targets]
        if spec.direction is ActionDirection.OUTGOING:
            others = [n for n in self._entities if n != actor]
            if others:
                return [spec.bind(actor=actor, target=t) for t in others]
        return [spec.bind(actor=actor)]

    def _active_actor_names(self) -> list[str]:
        return [name for name, e in self._entities.items() if e.is_active]

    def apply(self, action: Action) -> None:
        """Apply an action to this environment, then run :meth:`update`.

        Raises:
            InvalidAction: if the action's precondition does not hold.
        """
        action.apply(self)
        self.update()

    def update(self) -> None:
        """Hook for global, post-action dynamics. Override as needed."""

    @abstractmethod
    def is_terminal(self) -> bool:
        """Return whether the goal is reached or no further action helps."""

    # -- branching --------------------------------------------------------

    def clone(self) -> "Environment":
        """Return a deep, independent copy for hypothetical exploration.

        Mutating the clone must never affect the original; the planner depends
        on this isolation to explore the search tree safely.
        """
        return copy.deepcopy(self)
