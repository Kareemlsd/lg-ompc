"""Tests for entities, actions, and Design-by-Contract preconditions."""

from __future__ import annotations

import pytest

from conftest import PICK_UP, WALK, make_world
from lg_ompc import InvalidAction


def test_active_and_passive_roles(world):
    assert world.entity("human").is_active
    assert world.entity("water_bottle").is_passive
    assert not world.entity("water_bottle").is_active


def test_valid_action_mutates_state(world):
    walk = WALK.bind(actor="human", target="water_bottle")
    assert walk.is_applicable(world)
    walk.apply(world)
    assert world.entity("human").state["position"] == 1


def test_precondition_violation_raises():
    env = make_world(distance=2)
    # Picking up before being adjacent violates the precondition.
    pick = PICK_UP.bind(actor="human", target="water_bottle")
    assert not pick.is_applicable(env)
    with pytest.raises(InvalidAction):
        pick.apply(env)


def test_action_str_renders_actor_and_target():
    walk = WALK.bind(actor="human", target="water_bottle")
    assert str(walk) == "human.walk(water_bottle)"
