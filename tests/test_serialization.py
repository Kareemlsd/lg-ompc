"""Tests for serialization: shape and the attribute map."""

from __future__ import annotations

from lg_ompc import describe


def test_describe_includes_entities_and_goal(world):
    desc = describe(world)
    names = {e.name for e in desc.entities}
    assert names == {"human", "water_bottle"}
    assert desc.goal


def test_attribute_map_lists_real_dotted_paths(world):
    desc = describe(world)
    assert "human.hydration" in desc.attribute_map
    assert "water_bottle.contains_water" in desc.attribute_map


def test_roles_and_actions_are_serialized(world):
    desc = describe(world)
    by_name = {e.name: e for e in desc.entities}
    assert by_name["human"].role == "active"
    assert by_name["water_bottle"].role == "passive"
    assert "walk" in by_name["human"].outgoing_actions
    assert "drink_from" in by_name["water_bottle"].incoming_actions


def test_relations_are_serialized(world):
    desc = describe(world)
    assert any(r.type == "distance" for r in desc.relations)


def test_prompt_json_is_valid(world):
    payload = describe(world).to_prompt_json()
    assert "human" in payload and "goal" in payload
