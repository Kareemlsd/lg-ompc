"""Actions: the verbs an entity can perform or have performed on it.

An action is the discrete, named transition primitive of the environment. It
carries a *precondition* (Design by Contract: the action's guard) and an
*effect* (how it mutates state). Affordance — whether an action *can* run — is
decided here, in code. Desirability — whether it *should* run — is decided
later by the synthesized objective. Keeping those two concerns apart is the
central separation of the framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    from lg_ompc.environment import Environment


class ActionDirection(str, Enum):
    """Whether an action originates from an entity or is applied to it.

    Mirrors the ``A_out`` / ``A_in`` split from the environment definition.
    """

    OUTGOING = "outgoing"
    INCOMING = "incoming"


class InvalidAction(Exception):
    """Raised when an action is applied in a state that violates its precondition.

    Crashing early on a contract violation is deliberate: the planner treats a
    raised ``InvalidAction`` as "this branch is not reachable" rather than
    silently producing a corrupt state.
    """


@dataclass(frozen=True)
class Action:
    """A concrete, ready-to-apply action instance.

    An ``Action`` binds an :class:`ActionSpec` to the specific entities it
    targets. It is the unit the planner enumerates, records in the action
    history, and applies to the environment.
    """

    spec: "ActionSpec"
    actor: str
    target: str | None = None
    params: dict[str, object] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def direction(self) -> ActionDirection:
        return self.spec.direction

    def is_applicable(self, env: "Environment") -> bool:
        """Return whether this action's precondition currently holds."""
        return self.spec.precondition(env, self)

    def apply(self, env: "Environment") -> None:
        """Apply the effect, enforcing the precondition first.

        Raises:
            InvalidAction: if the precondition does not hold.
        """
        if not self.spec.precondition(env, self):
            raise InvalidAction(
                f"Action {self.name!r} by {self.actor!r} "
                f"on {self.target!r} is not applicable in the current state."
            )
        self.spec.effect(env, self)

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        if self.target is not None:
            return f"{self.actor}.{self.name}({self.target})"
        return f"{self.actor}.{self.name}()"


# A precondition answers "can this run?"; an effect performs the mutation.
Precondition = Callable[["Environment", Action], bool]
Effect = Callable[["Environment", Action], None]


def _always(_env: "Environment", _action: Action) -> bool:
    return True


@dataclass(frozen=True)
class ActionSpec:
    """A reusable template describing one kind of action.

    Bind a spec to concrete entities with :meth:`bind` to produce an
    :class:`Action`. Specs are declared once per entity type and shared across
    every instance — a single source of truth for the verb's contract.
    """

    name: str
    direction: ActionDirection
    effect: Effect
    precondition: Precondition = _always
    enumerate_targets: Callable[["Environment", str], list[str]] | None = None

    def bind(
        self,
        actor: str,
        target: str | None = None,
        **params: object,
    ) -> Action:
        """Create a concrete :class:`Action` from this spec."""
        return Action(spec=self, actor=actor, target=target, params=params)


@runtime_checkable
class SupportsActions(Protocol):
    """Structural type for objects that expose action specs.

    Any object — typically an :class:`~lg_ompc.entities.Entity` — that can list
    the actions it offers satisfies this protocol.
    """

    def outgoing_actions(self) -> list[ActionSpec]: ...

    def incoming_actions(self) -> list[ActionSpec]: ...
