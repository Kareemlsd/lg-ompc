# Mathematical Definition of the Environment

This document defines the concept of an **environment** for the LG-OMPC project.

The goal of this definition is to provide a mathematical foundation for the first part of the project: representing an environment as a structured system of entities, actions, relations, observations, and purposes. This environment definition will later be used to inform objective-function synthesis for model predictive control.

---

## 1. Environment as the True Interactive System

We define an environment as the true interactive system in which actions are performed and consequences occur.

An environment is denoted by

\[
\mathcal{E}
=
\left(
\mathcal{V},
\mathcal{X},
\mathcal{U},
F_{\mathcal{E}},
\mathcal{R},
\mathcal{O},
\mathcal{P}
\right),
\]

where:

- \(\mathcal{V}\) is the set of entities in the environment;
- \(\mathcal{X}\) is the true state space;
- \(\mathcal{U}\) is the action space;
- \(F_{\mathcal{E}}\) is the true environment transition function;
- \(\mathcal{R}\) is the set of relations between entities;
- \(\mathcal{O}\) is the observation space;
- \(\mathcal{P}\) is the set of entity-associated purposes.

At discrete time \(k\), the environment has a true state

\[
x_k \in \mathcal{X}.
\]

An action

\[
u_k \in \mathcal{U}(x_k)
\]

is performed, where \(\mathcal{U}(x_k)\) denotes the set of admissible actions in state \(x_k\).

The environment evolves according to

\[
x_{k+1}
=
F_{\mathcal{E}}(x_k, u_k, \xi_k),
\]

where \(\xi_k\) represents disturbances, uncertainty, hidden influences, or unmodeled interactions.

The environment should be distinguished from the world model. The environment is the true system. A world model is only an approximation used for prediction and planning.

---

## 2. Entities

The environment contains a finite or countable set of entities

\[
\mathcal{V}
=
\{e_1, e_2, \ldots, e_n\}.
\]

Each entity \(e_i \in \mathcal{V}\) has an entity-specific state

\[
x_k^{(i)} \in \mathcal{X}^{(i)}.
\]

The full environment state may be written as

\[
x_k
=
\left(
x_k^{(1)},
x_k^{(2)},
\ldots,
x_k^{(n)},
r_k
\right),
\]

where \(r_k\) contains relational or global information that does not belong to a single entity.

Examples of such relational or global information include:

- distances between entities;
- contact relations;
- visibility relations;
- ownership or dependency relations;
- environmental constraints;
- shared resources;
- hidden contextual variables.

This distinction is important because many relevant objectives are not entity-local. For example, the statement "the human is hydrated" may depend on the human, the water bottle, the amount of water, the availability of a drinking action, and the current context.

---

## 3. Acting and Acted-On Entities

Entities may act on the environment, be acted upon by other entities, or both.

For each entity \(e_i\), we define two action-related sets:

\[
\mathcal{A}_i^{\mathrm{out}}
\]

and

\[
\mathcal{A}_i^{\mathrm{in}},
\]

where:

- \(\mathcal{A}_i^{\mathrm{out}}\) is the set of actions that entity \(e_i\) can perform;
- \(\mathcal{A}_i^{\mathrm{in}}\) is the set of actions that can be performed on entity \(e_i\).

An entity is called **active** if

\[
\mathcal{A}_i^{\mathrm{out}} \neq \emptyset.
\]

An entity is called **passive** if

\[
\mathcal{A}_i^{\mathrm{out}} = \emptyset
\quad \text{and} \quad
\mathcal{A}_i^{\mathrm{in}} \neq \emptyset.
\]

Passive entities are not irrelevant. They may still be essential to the system dynamics and to the construction of the objective function.

For example, a human may have outgoing actions such as

\[
\mathcal{A}_{\mathrm{human}}^{\mathrm{out}}
=
\{
\text{walk},
\text{pick up},
\text{drink},
\text{open}
\},
\]

whereas a water bottle may primarily have incoming actions such as

\[
\mathcal{A}_{\mathrm{bottle}}^{\mathrm{in}}
=
\{
\text{pick up},
\text{open},
\text{drink from},
\text{move}
\}.
\]

In this example, the water bottle may be acted upon in order to help satisfy a purpose associated with the human, such as hydration.

---

## 4. Multi-Purpose Entities

Each entity is assumed to be potentially multi-purpose.

For each entity \(e_i\), we define a set of possible purposes

\[
\mathcal{P}_i
=
\{
p_i^1,
p_i^2,
\ldots,
p_i^{m_i}
\}.
\]

The complete purpose set of the environment is

\[
\mathcal{P}
=
\bigcup_{i=1}^{n}
\mathcal{P}_i.
\]

A purpose should not be interpreted as a fixed objective. Instead, a purpose describes a possible role an entity may serve in the system.

For example, a water bottle may have purposes such as

\[
\mathcal{P}_{\mathrm{bottle}}
=
\{
\text{hydrate agent},
\text{store water},
\text{transport liquid},
\text{serve as physical object}
\}.
\]

A human may have purposes or needs such as

\[
\mathcal{P}_{\mathrm{human}}
=
\{
\text{remain safe},
\text{be hydrated},
\text{complete task},
\text{minimize effort}
\}.
\]

The relevant purpose of an entity depends on the current state, the available actions, the relations between entities, and the desired goal.

---

## 5. Purpose Relevance

Let \(\mathcal{G}\) denote the space of possible goals or desired final conditions.

For each entity \(e_i\), we define a purpose relevance function

\[
\rho_i :
\mathcal{P}_i
\times
\mathcal{X}
\times
\mathcal{G}
\rightarrow
\mathbb{R}_{\geq 0}.
\]

The value

\[
\rho_i(p_i^j, x_k, g)
\]

measures the relevance of purpose \(p_i^j\) for entity \(e_i\), given the current environment state \(x_k\) and goal \(g \in \mathcal{G}\).

A high value of \(\rho_i\) means that the corresponding purpose is relevant for objective construction.

For example, if the goal is to make a human hydrated, then

\[
\rho_{\mathrm{bottle}}
(
\text{hydrate agent},
x_k,
g
)
\]

should be high when a water bottle is present, contains water, and can be used by the human.

This formulation avoids assigning a single fixed purpose to an entity. Instead, each entity has multiple possible purposes whose relevance depends on context.

---

## 6. Purposes as Information for Objective Construction

The purpose structure of the environment provides semantic information from which objective terms may be assembled.

Each purpose \(p_i^j\) may be associated with candidate objective terms

\[
\Phi(p_i^j)
=
\{
\ell_1,
\ell_2,
\ldots,
\ell_q
\},
\]

where each \(\ell_q\) is a possible running cost, terminal cost, penalty, or constraint-related term.

For example, the purpose

\[
p = \text{hydrate human}
\]

may imply objective terms such as:

\[
\ell_{\mathrm{hydration}}(x_k),
\]

\[
\ell_{\mathrm{water\_availability}}(x_k),
\]

\[
\ell_{\mathrm{effort}}(u_k),
\]

and

\[
\ell_{\mathrm{safety}}(x_k, u_k).
\]

The environment therefore does not directly define the MPC objective. Instead, it contains the structured semantic information needed to construct one.

In the LG-OMPC framework, the language model receives a description of the environment, including entities, purposes, relations, actions, and goals. It then proposes or assembles an objective specification that can be used by an MPC planner.

Conceptually,

\[
\mathrm{LLM}
:
(
\mathcal{E},
x_k,
g
)
\mapsto
J,
\]

where \(J\) is an MPC-compatible objective function or objective specification.

---

## 7. Fully Observed Environments

The first environment class is the fully observed case.

In this case, the full state is available:

\[
y_k = x_k.
\]

The dynamics can be represented as

\[
x_{k+1}
=
F_{\mathcal{E}}(x_k, u_k, \xi_k).
\]

A world model may approximate these dynamics as

\[
\hat{x}_{k+1}
=
f_\theta(x_k, u_k).
\]

In this case, MPC can operate directly on the state space \(\mathcal{X}\).

A generic MPC problem can be written as

\[
\min_{u_{k:k+N-1}}
\sum_{j=0}^{N-1}
\ell(x_{k+j}, u_{k+j})
+
\ell_f(x_{k+N}),
\]

subject to

\[
x_{k+j+1}
=
f_\theta(x_{k+j}, u_{k+j}),
\]

\[
u_{k+j}
\in
\mathcal{U}(x_{k+j}),
\]

and

\[
x_{k+j}
\in
\mathcal{X}_{\mathrm{safe}}.
\]

The role of objective generation is to define or assemble

\[
\ell,
\quad
\ell_f,
\quad
\mathcal{X}_{\mathrm{safe}},
\]

from the environment description and goal.

---

## 8. Partially Observed Environments

The second environment class is the partially observed case.

The true state exists,

\[
x_k \in \mathcal{X},
\]

but it is not directly available. Instead, measurements are observed:

\[
y_k
=
H_{\mathcal{E}}(x_k, \nu_k),
\]

where:

- \(y_k \in \mathcal{O}\) is the observation;
- \(H_{\mathcal{E}}\) is the observation function;
- \(\nu_k\) represents measurement noise.

The true dynamics remain

\[
x_{k+1}
=
F_{\mathcal{E}}(x_k, u_k, \xi_k),
\]

but the controller does not have direct access to \(x_k\).

Therefore, planning must be performed using an estimated, latent, or lifted state

\[
z_k \in \mathcal{Z}.
\]

This state may be obtained from measurement histories and action histories:

\[
z_k
=
\psi_\theta
(
y_{k-h:k},
u_{k-h:k-1}
),
\]

where \(h\) is a history length and \(\psi_\theta\) is a learned encoder or lifting map.

A general learned world model may then be written as

\[
z_{k+1}
=
f_\theta(z_k, u_k).
\]

A Koopman-inspired formulation seeks a lifted representation in which the dynamics are approximately linear:

\[
z_{k+1}
=
A z_k + B u_k,
\]

with a reconstruction or output map

\[
\hat{y}_k
=
C z_k.
\]

In partially observed environments, MPC operates over \(z_k\), \(y_k\), or reconstructed estimates of meaningful state quantities.

The objective may therefore be expressed as

\[
J
=
\sum_{j=0}^{N-1}
\ell(z_{k+j}, u_{k+j}, \hat{y}_{k+j})
+
\ell_f(z_{k+N}, \hat{y}_{k+N}).
\]

---

## 9. Environment Description for Objective Generation

For objective generation, the mathematical environment must be expressible in a structured representation.

A useful environment description should include:

- entities \(\mathcal{V}\);
- entity states \(x_k^{(i)}\), if available;
- available actions \(\mathcal{A}_i^{\mathrm{out}}\) and \(\mathcal{A}_i^{\mathrm{in}}\);
- relations \(\mathcal{R}\);
- purposes \(\mathcal{P}_i\);
- purpose relevance information \(\rho_i\), if available;
- observations \(y_k\), if the environment is partially observed;
- the goal \(g\);
- safety constraints and admissible state/action sets.

A possible structured representation is

```json
{
  "environment": {
    "entities": [
      {
        "name": "human",
        "type": "active_agent",
        "state": {
          "hydration": "low",
          "position": [0, 0]
        },
        "outgoing_actions": ["walk", "pick_up", "drink"],
        "incoming_actions": [],
        "purposes": ["remain_safe", "be_hydrated", "complete_task"]
      },
      {
        "name": "water_bottle",
        "type": "passive_object",
        "state": {
          "contains_water": true,
          "position": [2, 1]
        },
        "outgoing_actions": [],
        "incoming_actions": ["pick_up", "open", "drink_from"],
        "purposes": ["hydrate_agent", "store_water", "transport_liquid"]
      }
    ],
    "relations": [
      {
        "type": "distance",
        "source": "human",
        "target": "water_bottle",
        "value": 2.24
      }
    ],
    "goal": "human should become hydrated while remaining safe"
  }
}
```

This representation is not the objective itself. It is the semantic and structural input from which an objective can be constructed.

---

## 10. Key Distinction: Environment vs. World Model

The environment and the world model must remain conceptually separate.

The environment is the true system:

\[
x_{k+1}
=
F_{\mathcal{E}}(x_k, u_k, \xi_k).
\]

The world model is an approximation used for prediction:

\[
\hat{x}_{k+1}
=
f_\theta(x_k, u_k),
\]

or, in the partially observed case,

\[
z_{k+1}
=
f_\theta(z_k, u_k).
\]

MPC does not act on the world model. MPC uses the world model to select an action, and that action is then applied to the true environment.

Thus,

\[
\mathcal{E} \neq f_\theta.
\]

This distinction is central to the project.

---

## 11. Working Definition

For this project, the environment is defined as follows:

> An environment is the true interactive system consisting of entities, states, actions, relations, observations, and purposes. It evolves according to its true dynamics under performed actions. Entities may act, be acted upon, or both. Each entity may serve multiple purposes, and the relevance of these purposes depends on the current state and desired goal. The structured description of the environment provides the semantic information needed for language-guided objective construction, while the world model provides a predictive approximation used by MPC.

---

## 12. Implementation Implications

This definition suggests that the first environment module should support the following concepts:

1. **Entity**
   - name;
   - type;
   - state;
   - outgoing actions;
   - incoming actions;
   - purposes.

2. **Relation**
   - source entity;
   - target entity;
   - relation type;
   - relation value or metadata.

3. **Environment**
   - entity collection;
   - state representation;
   - available actions;
   - transition interface;
   - observation interface;
   - relation structure;
   - goal description.

4. **Purpose**
   - purpose name;
   - associated entity;
   - optional relevance score;
   - possible mapping to objective terms.

5. **Observation**
   - full-state observation for fully observed environments;
   - measurement-based observation for partially observed environments.

6. **Environment Description**
   - a structured representation, such as JSON, that can be passed to an objective-generation component.

The implementation should preserve the distinction between:

- the true environment;
- the observed state or measurement;
- the learned or specified world model;
- the objective specification generated from the environment description.
