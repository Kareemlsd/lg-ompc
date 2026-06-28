"""Tests for the controller loop and LLM synthesis (with a stub model)."""

from __future__ import annotations

from pydantic_ai.models.test import TestModel

from conftest import HANDWRITTEN_OBJECTIVE, make_world
from lg_ompc import Controller, build_agent, compile_objective, synthesize_objective


def test_controller_reaches_goal_with_handwritten_objective():
    env = make_world(distance=2)
    objective = compile_objective(HANDWRITTEN_OBJECTIVE)

    result = Controller(horizon=3, max_steps=20).run(env, objective=objective)

    assert result.reached_goal
    assert env.entity("human").state["hydration"] == "high"
    # walk, walk, pick_up, drink_from
    names = [a.name for a in result.history]
    assert names[-1] == "drink_from"
    assert "pick_up" in names


def test_synthesis_returns_compilable_spec_with_stub_model():
    env = make_world()
    stub = TestModel(
        custom_output_args={
            "code": HANDWRITTEN_OBJECTIVE,
            "terms": [],
            "rationale": "stub",
        }
    )
    agent = build_agent(model=stub)
    spec = synthesize_objective(env, agent=agent)

    assert spec.rationale == "stub"
    # The synthesized code compiles and runs.
    objective = spec.compile()
    assert isinstance(__import__("lg_ompc").evaluate(objective, env, []), float)


def test_controller_synthesizes_when_no_objective_given():
    env = make_world(distance=1)
    stub = TestModel(
        custom_output_args={"code": HANDWRITTEN_OBJECTIVE, "terms": [], "rationale": ""}
    )
    agent = build_agent(model=stub)
    result = Controller(horizon=3).run(env, agent=agent)

    assert result.reached_goal
