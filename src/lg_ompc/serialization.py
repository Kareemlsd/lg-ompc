"""Serialization: turn a live environment into an LLM-facing description.

This module is the single source of truth for *what the LLM sees*. Besides the
human-readable structure (entities, actions, relations, goal) it emits an
``attribute_map`` listing the exact, dotted attribute paths the generated
objective may read — e.g. ``human.hydration``. Advertising the real names up
front removes a whole class of attribute-hallucination bugs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from lg_ompc.environment import Environment


class EntityDescription(BaseModel):
    """Serialized view of a single entity."""

    name: str
    kind: str
    role: str = Field(description="'active', 'passive', or 'inert'.")
    state: dict[str, object]
    outgoing_actions: list[str]
    incoming_actions: list[str]
    purposes: list[str]


class RelationDescription(BaseModel):
    """Serialized view of a relation between two entities."""

    kind: str
    type: str
    source: str
    target: str
    value: float | str | None = None


class EnvironmentDescription(BaseModel):
    """The complete structured input handed to the synthesis agent.

    ``attribute_map`` maps each readable dotted path to its current value's type
    name, so the LLM knows precisely which attributes exist before it writes any
    code against them.
    """

    goal: str
    entities: list[EntityDescription]
    relations: list[RelationDescription]
    attribute_map: dict[str, str]

    def to_prompt_json(self) -> str:
        """Render as indented JSON suitable for embedding in a prompt."""
        return self.model_dump_json(indent=2)


def _role(entity) -> str:
    if entity.is_active:
        return "active"
    if entity.is_passive:
        return "passive"
    return "inert"


def describe(env: Environment) -> EnvironmentDescription:
    """Build an :class:`EnvironmentDescription` from a live environment."""
    entities: list[EntityDescription] = []
    attribute_map: dict[str, str] = {}

    for entity in env.entities.values():
        for key, value in entity.state.values.items():
            attribute_map[f"{entity.name}.{key}"] = type(value).__name__
        entities.append(
            EntityDescription(
                name=entity.name,
                kind=entity.kind,
                role=_role(entity),
                state=dict(entity.state.values),
                outgoing_actions=[s.name for s in entity.outgoing_actions()],
                incoming_actions=[s.name for s in entity.incoming_actions()],
                purposes=list(entity.purposes),
            )
        )

    relations = [
        RelationDescription(
            kind=r.kind.value,
            type=r.type,
            source=r.source,
            target=r.target,
            value=r.value,
        )
        for r in env.compute_relations()
    ]

    return EnvironmentDescription(
        goal=env.goal,
        entities=entities,
        relations=relations,
        attribute_map=attribute_map,
    )
