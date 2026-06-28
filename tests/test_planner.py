"""Tests for the planner: it picks a sensible first action toward the goal."""

from __future__ import annotations

from conftest import HANDWRITTEN_OBJECTIVE, make_world
from lg_ompc import ForwardSearchPlanner, compile_objective


def test_planner_walks_toward_bottle_first():
    env = make_world(distance=2)
    objective = compile_objective(HANDWRITTEN_OBJECTIVE)
    planner = ForwardSearchPlanner(objective, horizon=3)

    result = planner.plan(env)

    assert result.action is not None
    assert result.action.name == "walk"
    # Planning must not mutate the true environment.
    assert env.entity("human").state["position"] == 0


def test_planner_prefers_drinking_when_adjacent_and_holding():
    env = make_world(distance=0)
    env.entity("human").state["holding"] = "water_bottle"
    objective = compile_objective(HANDWRITTEN_OBJECTIVE)
    planner = ForwardSearchPlanner(objective, horizon=1)

    result = planner.plan(env)

    assert result.action is not None
    assert result.action.name == "drink_from"
