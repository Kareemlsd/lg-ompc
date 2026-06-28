"""Tests for the environment engine: enumeration, application, clone isolation."""

from __future__ import annotations

from conftest import make_world


def test_available_actions_only_returns_applicable(world):
    names = {a.name for a in world.available_actions()}
    # From the start the human can walk; it cannot yet pick up or drink.
    assert "walk" in names
    assert "pick_up" not in names
    assert "drink_from" not in names


def test_clone_is_isolated(world):
    clone = world.clone()
    clone.entity("human").state["position"] = 99
    assert world.entity("human").state["position"] == 0


def test_apply_runs_action_and_update(world):
    walk = world.available_actions()[0]
    world.apply(walk)
    assert world.entity("human").state["position"] == 1


def test_terminal_detection():
    env = make_world()
    assert not env.is_terminal()
    env.entity("human").state["hydration"] = "high"
    assert env.is_terminal()
