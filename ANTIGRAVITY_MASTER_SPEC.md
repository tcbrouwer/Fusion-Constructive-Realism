# `ANTIGRAVITY_MASTER_SPEC.md`

## System Goal

Build a Python 3.10+ interactive Command Line / REPL application (`fcr_repl.py`) and an offline graph analysis engine (`fcr_analyzer.py`) implementing **Fusion Constructive Realism (FCR)**.

The software builds state spaces ($\mathcal{M}_0$ through $\mathcal{M}_6$) level-by-level via **Attractor-Driven Boundary Fusion**, models targeted local graph mutations, executes capacity normalization and fission, and exports state transitions into a path-aware repository (`fcr_repository/`) to compute state transition probabilities $P(d_k)$.

---

## 1. Core Mathematical Definitions & State Representation

A state $Q = (P, \mu, C)$ at discrete poset tick $T$ is defined as:

* **Base Set ($P$):** A set of $n$ discrete node IDs $\{0, 1, \dots, n-1\}$.
* **Primitive Metric ($\mu$):**
* **Direct Edges ($C(i,j) \neq 0$):** Initialized at baseline Planck rest distance $\mu(i,j) = 1.0 \in \mathbb{Q}^+$. Evaluated as exact floats/rationals.
* **Uncorrelated Pairs ($C(i,j) = 0$):** Defined dynamically as the shortest-path geodesic metric through the graph network ($\mu(i,j) = \text{ShortestPath}_{\mu}(i \rightsquigarrow j)$). If disconnected, $\mu(i,j) = \infty$.


* **Correlation Field ($C$):** Complex values $z = a + bi \in \mathbb{D}_{\mathbb{Q}(i)}$ where $\vert{}z\vert{} \le 1.0$. Diagonal self-identity is fixed: $C(i,i) = 1.0 + 0.0i, \, \mu(i,i) = 0.0$.
* **Capacity Constraint:** For every node $p \in P$, the external correlation capacity sum must satisfy:

$$S(p) = \sum_{q \neq p} \vert{}C(p,q)\vert{}^2 \le 1.0$$



---

## 2. Dynamic Capacity Normalization, Virtual Lock, and Fission Engine

When a mutation pushes a node $p$ past capacity ($S(p) > 1.0$):

1. **Phase Venting ($\mathcal{M}_{1/2}$ Virtual Half-Edge):**
* The emitted virtual half-edge carries an un-fused phase magnitude $\Delta S = S(p) - 1.0$.
* The phase angle $\phi_{\text{vent}}$ of $\mathcal{M}_{1/2}$ is the net phase angle of all active incoming links at $p$:

$$\phi_{\text{vent}} = \arg \left( \sum_{q \neq p} C(p,q) \right)$$




2. **Coherent Amplitude Scaling:**
* Every active edge $C(p,q)$ connected to overloaded node $p$ is scaled down by factor $1/\sqrt{S(p)}$:

$$C(p,q) \leftarrow \frac{C(p,q)}{\sqrt{S(p)}}$$


* This guarantees $\sum_{q \neq p} \vert{}C(p,q)\vert{}^2 = 1.0$ without distorting relative phase angles.


3. **Link Severing & Fission Split:**
* If scaling causes any edge magnitude to fall below noise threshold $\vert{}C(p,q)\vert{} < \epsilon$ ($\epsilon = 10^{-6}$), the link is severed ($C(p,q) \to 0$).
* Execute connected-component analysis on $P$. If the graph splits into disjoint subgraphs $Q_1, Q_2, \dots$:
* The primary surviving component $Q_1$ remains at the target timestep.
* Severed subgraphs $Q_2, \dots$ are logged as ejected radiation remnants ($\mathcal{M}_2$ chains) in the transition history.





---

## 3. Boundary Assembly & Canonical Seeding Schema

To generate valid initial states for $\mathcal{M}_n$ without combinatorial explosion:

1. All initial seeds at $T=0$ must be constructed by gluing proven lower-order attractors ($n' < n$) along specified boundary maps $B$.
2. Every boundary fusion follows an explicit vertex identification mapping:

```yaml
# Example Seed: M3^4 -> M6 Octahedral Frame
seed_type: "multi_wedge"
target_nodes: 6
components:
  - { id: T_A, type: "M3_triangle", local_nodes: [0, 1, 2] }
  - { id: T_B, type: "M3_triangle", local_nodes: [0, 1, 2] }
  - { id: T_C, type: "M3_triangle", local_nodes: [0, 1, 2] }
  - { id: T_D, type: "M3_triangle", local_nodes: [0, 1, 2] }

boundary_gluing_map:
  0: [[T_A, 0], [T_B, 0]]
  1: [[T_A, 1], [T_C, 0]]
  2: [[T_A, 2], [T_D, 0]]
  3: [[T_B, 1], [T_C, 1]]
  4: [[T_B, 2], [T_D, 1]]
  5: [[T_C, 2], [T_D, 2]]

```

3. **Canonical Labeling:** Pass the resulting graph through NetworkX / NautyVF2 graph canonicalization over node degrees and correlation capacity sums to assign a unique, deterministic Canonical Hash ID.

---

## 4. Repository Directory & File Schema

States and transitions are stored on disk in the path-aware directory hierarchy:
`fcr_repository/M<n>/T_<k>/state_<CANONICAL_HASH>.yaml`

### File Schema Example (`fcr_repository/M6/T_1/state_a8f3c912.yaml`):

```yaml
metadata:
  level: 6
  poset_step_T: 1
  canonical_hash: "a8f3c912"
  visit_count: 5

incoming_paths:
  - parent_hash: "b7e12d40"
    mutation_used: "triangulate(0, 1, 3)"
    transition_phase: { real: 0.7071, imag: 0.7071 }

state_matrices:
  nodes: [0, 1, 2, 3, 4, 5]
  metric_distances:
    "[0,1]": 1.0
    "[1,3]": 1.0
    "[0,3]": 0.5
  correlations:
    "[0,1]": { real: 0.7071, imag: 0.7071 }
    "[1,3]": { real: 0.5000, imag: 0.0000 }
    "[0,3]": { real: 0.3535, imag: 0.3535 }

capacity_audit:
  max_node_sum: 0.875
  is_capacity_compliant: true

```

---

## 5. Interactive REPL Application Specs (`fcr_repl.py`)

The REPL application must provide an interactive shell supporting target-specific local operations:

### Terminal Display Matrix

When `show` or `print` is invoked, display the $n \times n$ state grid:

```text
=== FCR State: M6 | Step T = 1 | Hash: a8f3c912 ===

     |        0       |        1       |        2       |       ...
-----+----------------+----------------+----------------+---
   0 |  (0.0, 1.0)    | (1.0, 0.71+0i) | (0.5, 0.35+0i) |  ...
   1 | (1.0, 0.71+0i) |  (0.0, 1.0)    | (1.0, 0.50+0i) |  ...
 ... |   ...          |   ...          |   ...          |  ...

```

### REPL Commands

* `init <n>`: Initializes a blank $n$-node graph.
* `seed <type>`: Loads a boundary assembly template (e.g., `seed M6_M3^4`, `seed M3_triangle`).
* `set <i,j> <mu> <z_re+z_im>`: Manually sets edge $(i, j)$ metric and complex correlation.
* `triangulate <i> <x> <j>`: Executes Mutation 2 strictly on open 2-path $i \to x \to j$:

$$C(i,j) \leftarrow C(i,x) \cdot C(x,j)$$


* `decay <i> <j> [gamma]`: Executes Mutation 3 strictly on edge $(i,j)$:

$$C(i,j) \leftarrow C(i,j) \cdot e^{-\gamma \mu(i,j)}$$


* `metric_evolve <i> <j>`: Executes Mutation 4 strictly on edge $(i,j)$:

$$\mu(i,j) \leftarrow \mu(i,j) - \alpha \vert{}C(i,j)\vert{}^2 + \beta(1 - \mu(i,j))$$


* `lock`: Audits node capacity. If $S(p) > 1.0$, performs coherent scaling and vents $\mathcal{M}_{1/2}$.
* `step`: Advances poset clock $T \to T + 1$, saves state to `fcr_repository/M<n>/T_<T>/`, and logs incoming path.
* `attractors`: Lists all states in `fcr_repository/attractors/` that satisfy closed phase recirculation ($Q_{T+k} \cong Q_T$).

---

## 6. Offline Probability Analyzer Specs (`fcr_analyzer.py`)

Build a standalone analysis utility that:

1. Scans `fcr_repository/M<n>/T_<k>/` for all states at timestep $T_k$.
2. Reconstructs convergent path trajectories from `incoming_paths`.
3. Evaluates total phase product $Z(\gamma) = \prod_{e \in \gamma} z_e$ across all paths leading to state $Q$.
4. Computes and outputs the Born-rule display probability distribution:

$$P(Q) = \frac{\left\vert{} \sum_{\gamma \to Q} Z(\gamma) \right\vert{}^2}{\sum_{Q' \in T_k} \left\vert{} \sum_{\gamma' \to Q'} Z(\gamma') \right\vert{}^2}$$