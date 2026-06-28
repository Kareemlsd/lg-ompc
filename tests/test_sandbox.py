"""Tests for the sandbox: read-only enforcement and failure isolation."""

from __future__ import annotations

import pytest

from conftest import HANDWRITTEN_OBJECTIVE, make_world
from lg_ompc import ObjectiveError, compile_objective, evaluate


def test_valid_objective_returns_float():
    env = make_world()
    objective = compile_objective(HANDWRITTEN_OBJECTIVE)
    score = evaluate(objective, env, [])
    assert isinstance(score, float)


def test_missing_function_raises():
    with pytest.raises(ObjectiveError):
        compile_objective("x = 1")


def test_syntax_error_raises():
    with pytest.raises(ObjectiveError):
        compile_objective("def evaluate_objective(world, history) return 1")


def test_crashing_objective_scores_negative_infinity():
    env = make_world()
    # References an attribute that does not exist -> AttributeError at runtime.
    bad = compile_objective(
        "def evaluate_objective(world, history):\n"
        "    return world.entity('human').state['nonexistent_key']\n"
    )
    assert evaluate(bad, env, []) == float("-inf")


def test_mutation_attempt_is_blocked():
    env = make_world()
    mutating = compile_objective(
        "def evaluate_objective(world, history):\n"
        "    world.entity('human').state['hydration'] = 'high'\n"
        "    return 1.0\n"
    )
    # The mutation raises inside the read-only proxy, so the branch is discarded
    # and, crucially, the real environment is untouched.
    assert evaluate(mutating, env, []) == float("-inf")
    assert env.entity("human").state["hydration"] == "low"
