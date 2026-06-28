# LG-OMPC: Language-Guided Objective Model Predictive Control

LG-OMPC is an early-stage research project exploring how large language models can dynamically synthesize objective functions for world-model-based planning.

The core idea is to separate **task understanding** from **action optimization**:

* the LLM interprets the environment, agents, available actions, and desired final state;
* the LLM generates a structured objective function and relevant constraints;
* a world model predicts future states under candidate actions;
* an MPC planner optimizes over a receding horizon and executes the first action.

In short:

> The LLM defines what matters.
> The world model predicts what happens.
> MPC decides what to do next.

## Motivation

World models are useful because they can predict how an environment evolves. However, they do not automatically know what should be optimized in different situations.

In many tasks, the challenge is not only modeling the dynamics, but also defining the right objective. A fixed reward or cost function may work in one environment but fail in another. LG-OMPC investigates whether language models can generate task-specific objectives from high-level descriptions, avoiding the need to manually redesign reward functions for every new setting.

## Goals

* Build a simple world-model environment.
* Define a formal objective-function grammar.
* Use an LLM to generate structured MPC objectives.
* Validate the generated objectives before optimization.
* Compare against fixed hand-designed objectives.
* Study how well the method generalizes across different environments and tasks.

## Status

This project is currently in the idea and prototype stage.

## Repository Structure

```text
lg-ompc/
    ├── LICENSE
    ├── README.md
    ├── pyproject.toml
    ├── docs/
    ├── examples/
    ├── src/
    │   └── lg_ompc/
    │       └── __init__.py
    └── tests/
```

## License

To be decided.
