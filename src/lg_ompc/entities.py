"""Entities: the things that populate an environment.

An entity owns a mutable :class:`EntityState` and declares the actions it can
perform (``outgoing``) and that can be performed on it (``incoming``), plus a
set of *purposes* — the possible roles it may serve. Subclass :class:`Entity`
for your own domain; the base class is intentionally thin so it is Easy To
Change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from lg_ompc.actions import ActionSpec


@dataclass
class EntityState:
    """A flat, named bag of an entity's mutable attributes.

    Using explicit named keys (rather than an anonymous numeric vector) lets the
    serialized description advertise the exact attribute names to the LLM,
    eliminating a whole class of attribute-hallucination errors.
    """

    values: dict[str, object] = field(default_factory=dict)

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)

    def set(self, key: str, value: object) -> None:
        self.values[key] = value

    def __getitem__(self, key: str) -> object:
        return self.values[key]

    def __setitem__(self, key: str, value: object) -> None:
        self.values[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.values


class Entity(ABC):
    """Base class for every actor or object in an environment.

    Subclasses declare their behaviour by overriding :meth:`outgoing_actions`
    and :meth:`incoming_actions`. ``state`` holds the entity's mutable
    attributes and ``purposes`` lists the roles it may serve, which inform
    objective synthesis but never constrain it.
    """

    #: Free-form type label surfaced in the serialized description.
    kind: str = "entity"

    def __init__(
        self,
        name: str,
        state: EntityState | dict[str, object] | None = None,
        purposes: list[str] | None = None,
    ) -> None:
        self.name = name
        if isinstance(state, EntityState):
            self.state = state
        else:
            self.state = EntityState(dict(state or {}))
        self.purposes: list[str] = list(purposes or [])

    @abstractmethod
    def outgoing_actions(self) -> list[ActionSpec]:
        """Return the specs for actions this entity can perform."""

    @abstractmethod
    def incoming_actions(self) -> list[ActionSpec]:
        """Return the specs for actions that can be performed on this entity."""

    @property
    def is_active(self) -> bool:
        """True if the entity can act on the environment (``A_out`` non-empty)."""
        return bool(self.outgoing_actions())

    @property
    def is_passive(self) -> bool:
        """True if the entity only receives actions (``A_out`` empty, ``A_in`` not)."""
        return not self.outgoing_actions() and bool(self.incoming_actions())

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{type(self).__name__}(name={self.name!r}, state={self.state.values!r})"
