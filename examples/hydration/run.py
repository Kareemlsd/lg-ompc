"""Run the hydration example end to end with a live language model.

Usage::

    # Put your key in a .env (see .env.example) or export it, then:
    python examples/hydration/run.py

The script synthesizes an objective from the language model, runs the
receding-horizon controller, and prints the action trace it discovered.
"""

from __future__ import annotations

import os
from pathlib import Path

from lg_ompc import Controller
from world import HUMAN, build_world


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from a repo-root .env into the environment.

    Kept dependency-free and deliberately simple: existing environment
    variables win, so an explicit export always overrides the file.
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    _load_dotenv()
    env = build_world()

    print("Goal:", env.goal)
    print("Initial state:")
    for name, entity in env.entities.items():
        print(f"  {name}: {entity.state.values}")

    controller = Controller(horizon=6, max_steps=20)
    result = controller.run(env)

    if result.spec is not None:
        print("\nSynthesized objective rationale:")
        print(" ", result.spec.rationale or "(none provided)")
        if result.spec.terms:
            print("Objective terms:")
            for term in result.spec.terms:
                print(f"  - {term.name} (w={term.weight}): {term.rationale}")
        print("\nGenerated objective code:\n")
        print(result.spec.code)

    print("\nExecuted action trace:")
    for i, action in enumerate(result.history, start=1):
        print(f"  {i}. {action}")

    print(
        f"\nReached goal: {result.reached_goal} "
        f"(hydration={env.entity(HUMAN).state.get('hydration')}) "
        f"in {len(result.history)} actions."
    )


if __name__ == "__main__":
    main()
