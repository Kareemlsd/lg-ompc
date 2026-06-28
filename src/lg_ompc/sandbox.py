"""Sandbox: compile and run an LLM-generated objective safely.

The synthesized objective is straight Python — maximally expressive, but
untrusted. This module compiles it into a restricted namespace and invokes it
over a *read-only snapshot* of the world so an objective that tries to mutate
state (instead of merely scoring it) cannot corrupt the simulation.

The isolation here is deliberately lightweight (a frozen view plus a trimmed
builtins namespace), which is appropriate for a research MVP running
first-party-prompted code locally. It is **not** a security boundary against
hostile code; that would require process- or interpreter-level sandboxing.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

from lg_ompc.actions import Action

#: The signature every generated objective must define.
OBJECTIVE_FUNCTION_NAME = "evaluate_objective"

#: Builtins exposed to generated code. Trimmed to read-only, numeric-friendly
#: helpers; notably excludes ``open``, ``__import__``, ``eval``, and ``exec``.
_SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "round": round,
    "sorted": sorted,
    "any": any,
    "all": all,
    "map": map,
    "filter": filter,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "float": float,
    "int": int,
    "bool": bool,
    "str": str,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "isinstance": isinstance,
    "getattr": getattr,
    "hasattr": hasattr,
}


class ObjectiveError(Exception):
    """Raised when generated objective code cannot be compiled."""


class _ReadOnly:
    """A recursive, read-only proxy around a mapping or object.

    Attribute and item access pass through; any attempt to assign raises. This
    enforces the contract that an objective *reads* the world and *returns* a
    score, never mutating it.
    """

    __slots__ = ("_target",)

    def __init__(self, target: Any) -> None:
        object.__setattr__(self, "_target", target)

    def __getattr__(self, name: str) -> Any:
        return _wrap(getattr(object.__getattribute__(self, "_target"), name))

    def __setattr__(self, name: str, value: Any) -> None:
        raise ObjectiveError("Objective code may not mutate the world snapshot.")

    def __getitem__(self, key: Any) -> Any:
        return _wrap(object.__getattribute__(self, "_target")[key])

    def __setitem__(self, key: Any, value: Any) -> None:
        raise ObjectiveError("Objective code may not mutate the world snapshot.")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        target = object.__getattribute__(self, "_target")
        return _wrap(target(*args, **kwargs))

    def __iter__(self):
        return iter(object.__getattribute__(self, "_target"))

    def __len__(self) -> int:
        return len(object.__getattribute__(self, "_target"))

    def __contains__(self, item: Any) -> bool:
        return item in object.__getattribute__(self, "_target")

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"ReadOnly({object.__getattribute__(self, '_target')!r})"


def _wrap(value: Any) -> Any:
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return value
    if isinstance(value, _ReadOnly):
        return value
    return _ReadOnly(value)


# The compiled objective receives a read-only world snapshot and the list of
# actions taken to reach it, and returns a scalar score.
ObjectiveCallable = Callable[[Any, list[Action]], float]


def compile_objective(code: str) -> ObjectiveCallable:
    """Compile generated source into a callable objective.

    The source must define a top-level function named ``evaluate_objective``.

    Raises:
        ObjectiveError: if the code does not compile or the function is missing.
    """
    namespace: dict[str, Any] = {"__builtins__": _SAFE_BUILTINS}
    try:
        compiled = compile(code, "<objective>", "exec")
        exec(compiled, namespace)  # noqa: S102 - intentional, sandboxed exec
    except SyntaxError as exc:  # crash early on un-runnable code
        raise ObjectiveError(f"Objective code failed to compile: {exc}") from exc

    func = namespace.get(OBJECTIVE_FUNCTION_NAME)
    if not callable(func):
        raise ObjectiveError(
            f"Objective code must define a callable {OBJECTIVE_FUNCTION_NAME!r}."
        )
    return func


def evaluate(
    objective: ObjectiveCallable,
    snapshot: Any,
    history: list[Action],
) -> float:
    """Score a world snapshot with an objective, isolating any failure.

    The snapshot is deep-copied and wrapped read-only before being passed in:
    the proxy rejects direct assignment with a clear error, and the copy is a
    belt-and-braces guarantee that nothing the objective does can touch the real
    world. If the objective raises (e.g. it referenced a non-existent
    attribute), this returns negative infinity so the planner discards that
    branch instead of crashing.
    """
    try:
        result = objective(_ReadOnly(copy.deepcopy(snapshot)), list(history))
        return float(result)
    except Exception:  # noqa: BLE001 - any failure means "unusable branch"
        return float("-inf")
