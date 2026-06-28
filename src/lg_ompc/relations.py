"""Relations: global or pairwise information that is not entity-local.

Many objectives depend on facts *between* entities (distance, containment,
ordering) rather than on a single entity's state. Relations capture that
``r_k`` term from the environment definition and are surfaced to the LLM as
part of the serialized description.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RelationKind(str, Enum):
    """The category of a relation.

    ``SPATIAL`` relations are instantaneous (distance, contact, visibility);
    ``TEMPORAL`` relations encode ordering or sequence state (A before B);
    ``DEPENDENCY`` captures ownership or requires-relationships.
    """

    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    DEPENDENCY = "dependency"


@dataclass(frozen=True)
class Relation:
    """A directed, typed edge between two entities.

    Attributes:
        kind: The category of relation.
        type: A free-form subtype label (e.g. ``"distance"``, ``"holding"``).
        source: Name of the source entity.
        target: Name of the target entity.
        value: Optional numeric or symbolic payload (e.g. a distance).
    """

    kind: RelationKind
    type: str
    source: str
    target: str
    value: float | str | None = None
