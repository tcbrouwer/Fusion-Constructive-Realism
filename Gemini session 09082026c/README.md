# Fusion Constructive Realism (FCR v2.1)
## Foundational State-Space & Reduction Engine

[![Rust 1.80+](https://img.shields.io/badge/Rust-1.80%2B-orange.svg)](https://www.rust-lang.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FCR Spec](https://img.shields.io/badge/FCR-v2.1%20Specification-purple.svg)](AGENT.md)

An ultra-high performance, background-independent, discrete relational physics engine and quantum computer simulator for **Fusion Constructive Realism (FCR v2.1)**. 

The engine models physical reality not as a continuous coordinate spacetime manifold, but as an evolving network of $M_n$ discrete relational points governed by complex correlation fields $C(i,j)$, spatial metrics $\mu(i,j)$, non-uniform operational mutation kinetics $\Sigma$, instant virtual phase venting recoil, canonical Weisfeiler-Lehman graph reduction, and Born-rule observational display postulates.

---

## Table of Contents

- [1. Theoretical Foundations & Axioms](#1-theoretical-foundations--axioms)
- [2. System Architecture & Capabilities](#2-system-architecture--capabilities)
- [3. Operational Mutation Taxonomy ($\Sigma$)](#3-operational-mutation-taxonomy-\sigma)
- [4. Permutation-Invariant Canonical Reduction](#4-permutation-invariant-canonical-reduction)
- [5. Born-Rule Display Postulate Evaluator](#5-born-rule-display-postulate-evaluator)
- [6. Extensibility Modules](#6-extensibility-modules)
  - [Sub-Universe Boundary Fusion ($Q_A \oplus Q_B$)](#sub-universe-boundary-fusion-q_a-\oplus-q_b)
  - [Dedicated FCR Quantum Computer Simulator](#dedicated-fcr-quantum-computer-simulator)
- [7. Installation & Quickstart](#7-installation--quickstart)
- [8. CLI Command Reference](#8-cli-command-reference)
- [9. Visualizing & Inspecting States (`.fcrstate`)](#9-visualizing--inspecting-states-fcrstate)
- [10. Programmatic Library API (Rust & Python)](#10-programmatic-library-api-rust--python)
- [11. Testing & Verification](#11-testing--verification)

---

## 1. Theoretical Foundations & Axioms

Physical reality in FCR 2.1 is represented as a discrete world-state triad $Q = (P, \mu, C) \in M_n$:

1. **Base Relational Set ($P$)**: A finite set of $n$ discrete node identifiers $P = \{0, 1, \dots, n-1\}$.
2. **Complex Correlation Field ($C$)**: An $n \times n$ Hermitian-like matrix $C(i,j) \in \mathbb{C}$ encoding phase and correlation strength:
   $$\vert{}C(i,j)\vert{} \le 1.0, \quad C(i,i) = 1.0 + 0.0i, \quad C(i,j) = C(j,i)^*$$
3. **Primitive Metric Field ($\mu$)**: A spatial distance matrix $\mu(i,j) \in \mathbb{R}^+$ satisfying $\mu(i,i) = 0.0$.
4. **Node Correlation Capacity Sum Axiom**: Physical stability requires that no single node $p \in P$ can support unbounded external correlations:
   $$S(p) = \sum_{q \neq p} \vert{}C(p,q)\vert{}^2 \le 1.0$$

---

## 2. System Architecture & Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               FCR 2.1 ENGINE ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
        │
        ├── Core Computational Engine (Rust 1.97+ / fcr_core)
        │     ├── High-concurrency Rayon macro-trajectory state branching
        │     ├── Instant virtual phase venting (M_1/2) with phase recoil conservation
        │     ├── Gauge-fixing via 3-cycle loop trace phase arg(Tr(C^3))
        │     ├── Weisfeiler-Lehman (WL) canonical graph hashing & deduplication
        │     └── Fast binary .fcrstate disk serialization (bincode)
        │
        ├── Extensibility Modules
        │     ├── Sub-Universe Boundary Fusion (Q_A ⊕ Q_B)
        │     └── FCR Quantum Computer Simulator (H, X, CNOT gates & Bell states)
        │
        └── Interface & Analysis (Python 3.11+ / fcr_display.py)
              ├── Born-rule display probability distribution tables
              ├── Text-based matrix & edge capacity inspection
              └── 2D Relational Network Plotting (NetworkX + Matplotlib)
```

---

## 3. Operational Mutation Taxonomy ($\Sigma$)

Transitions between world states occur across causal poset steps $T \to T'$ via single operational mutations $m \in \Sigma_{\text{lawful}} \cup \Sigma_{\text{contingent}}$:

### 1. Triangulation ($t \in \Sigma_{\text{lawful}}$)
* **Mechanics**: Iterates over each unordered triplet of nodes $\{i, k, j\}$ and evaluates simple linear updates for active 2-paths, regardless of whether target $C(i, j)$ is $0$ or $>0$:
  $$C_{\text{new}}(i, j) = C_{\text{old}}(i, j) + C(i, k) C(k, j)$$
* **Physical Weight**: $W_t = \exp\left(-\left(\mu(i,j)\right)^2\right) \cdot \exp\left(-\text{excess}^2\right)$ where $\text{excess} = \max(0, S(i) - 1.0) + \max(0, S(j) - 1.0)$. Soft Gaussian action penalty for virtual over-capacity states.

### 2. Correlation Decay ($d \in \Sigma_{\text{lawful}}$)
* **Mechanics**: $C_{T'}(i,j) = C_T(i,j) \cdot e^{-\gamma \mu_T(i,j)}$. Edge is severed ($C \to 0$) if $|C| < 10^{-6}$.
* **Physical Weight**: $W_d = \exp(-\gamma \mu_T(i,j)) \cdot \exp\left(-\text{excess}^2\right)$ with default decay rate parameter $\gamma = \ln(2) \approx 0.6931$ and $\text{excess} = \max(0, S(i) - 1.0) + \max(0, S(j) - 1.0)$.

### 3. Asymptotic Metric Evolution ($\mu \in \Sigma_{\text{lawful}}$)
* **Mechanics**: Asymptotic non-linear update law resolving negative distance pathologies:
  $$\mu_{T'}(i,j) = \mu_T(i,j) \cdot e^{-\alpha (\vert{}C_T(i,j)\vert{} - 0.5)} + \beta(1.0 - \mu_T(i,j))$$
* **Physical Weight**: $W_m = \exp(-\text{strain}) \cdot \exp\left(-\text{excess}^2\right)$ where $\text{strain} = \frac{|\mu_{\text{new}} - \mu_{\text{old}}|}{\mu_{\text{old}}}$ (or $1.0$ if $\mu_{\text{old}} \le 0$) and $\text{excess} = \max(0, S(i) - 1.0) + \max(0, S(j) - 1.0)$.
* **Positivity Guarantee**: Strictly holds $\mu_{T'} > 0$ for all finite steps.

> [!NOTE]
> **Metric Geodesic Definition for Unlinked Pairs ($C(i,j) = 0$)**
> 
> Uncorrelated node pairs ($C(i,j) = 0$) do not undergo direct metric drift. Instead, the metric separation between any unlinked pair is strictly defined as the Shortest-Path Geodesic distance across active intermediate correlated edges ($|C(u,v)| > \epsilon_{\text{cancel}}$):
> 
> $$\mu(i,j) = \text{ShortestPath}_\mu(i \to j) = \min_{\gamma} \sum_{e \in \gamma} \mu(e)$$

---

## 4. Permutation-Invariant Canonical Reduction

To deduplicate multi-path macro-trajectories landing on isomorphic relational graphs, candidate states pass through a 3-step reduction algorithm:

1. **Global Loop Phase Gauge-Fixing**: Rotate edge phases relative to the global 3-cycle loop trace phase $\Phi_{\text{global}} = \arg(\text{Tr}(C^3))$ (active if $|\text{Tr}(C^3)| > \epsilon_{\text{cancel}} = 10^{-2}$):
   $$C_{\text{gauge}}(a,b) = C(a,b) \cdot e^{-i\Phi_{\text{global}}}$$
2. **Numerical Float Binning**: Round floating-point values for $|C|$, $\arg(C)$, and $\mu$ to fixed precision $\epsilon_{\text{bin}} = 10^{-2}$ (0.01) to eliminate floating-point drift.
3. **Weisfeiler-Lehman (WL) Canonical Graph Hashing**: 3-round WL color refinement algorithm outputting a unique, deterministic SHA-256 hash string for equivalence class $[Q]$.

> [!NOTE]
> **Computational Power vs. Reality Accuracy Settings (`EPSILON_BIN` & `EPSILON_CANCEL`)**
> 
> In `src/reduction.rs`, the numerical parameters are configured to `EPSILON_BIN = 1e-2` (0.01) and `EPSILON_CANCEL = 1e-2` (0.01).
> 
> - **Why this boosts Computational Power**: Float binning at $10^{-2}$ precision and higher cancellation thresholds ($10^{-2}$) cause micro-states with minor numerical floating-point fluctuations to collapse into identical Weisfeiler-Lehman canonical hash equivalence classes ($[Q]$). This suppresses combinatorial state-space explosion across poset time steps $T_k$, allowing complex multi-node systems (such as 6+ node cyclic networks) to evaluate rapidly with low memory overhead.
> - **Accuracy Trade-off**: High-precision continuum phase interference and ultra-fine distance variations ($< 0.01$) are discretized into 2-decimal bins. For ultra-exact physical continuum simulations, these constants can be adjusted back to finer tolerances ($10^{-3}$ and $10^{-6}$).

> [!IMPORTANT]
> **Top-N State Pruning (`--top-states 100`)**
> 
> During macro-trajectory tree generation, after completing operational mutation branching and canonical WL graph deduplication at step $T_k$, the engine evaluates the accumulated amplitude weight $A(\Gamma)$ of each state equivalence class $[Q]$.
> 
> - **Top 100 Default Pruning**: By default (`--top-states 100`), only the top 100 most probable world states in step $T_k$ are saved to disk and carried forward as parent states for step $T_{k+1}$; states below rank 100 are pruned.
> - **Computational Efficiency Gain**: Prevents exponential state-space tree explosion ($O(B^T)$). For instance, in a 6-node cyclic network evolved over 36 steps, top-100 pruning evaluates in under **1 second** while preserving all dominant quantum trajectory branches.
> - **Accuracy Trade-off**: Highly improbable sub-dominant quantum trajectory branches below rank $N$ are discarded. To execute exact, unpruned quantum trajectory calculations, set `--top-states 0`.

> [!TIP]
> **Commutative Canonical Edge Ordering & Combinatorial Symmetry Weighting ($\frac{k!}{\prod n_i!}$)**
> 
> When two local mutations $m_a, m_b \in \Sigma_{\text{lawful}}$ act on disjoint sets of nodes, they commute ($[m_a, m_b] = 0$). To eliminate redundant permutation trees without altering physical trajectory probabilities:
> 
> 1. **Canonical Edge & Triad Indexing**: Each edge $(i,j)$ and triad $\{p_1, p_2, p_3\}$ is assigned a unique, fixed canonical index $e_i$.
> 2. **Disjoint Commutative Ordering Constraint**: When two mutations $m_a, m_b$ act on completely disjoint sets of nodes ($N(m_a) \cap N(m_b) = \emptyset$), they commute ($m_a \circ m_b \equiv m_b \circ m_a$). The generator strictly requires applying disjoint commuting operations in increasing canonical index order ($e_a < e_b$), pruning non-canonical permutation branches.
> 3. **Combinatorial Symmetry Weighting**: The weight of the resulting canonical trajectory path $A(\Gamma)$ is scaled by the exact combinatorial symmetry factor $\frac{k!}{\prod n_i!}$, preserving exact physical Born-rule display probability distributions while accelerating trajectory evolution by orders of magnitude.

---

## 5. Born-Rule Display Postulate Evaluator

The evaluator computes observational display probabilities $P([Q])$ across time steps $T_k$:

$$P([Q]) = \frac{\left\vert{}\sum_{\Gamma \to [Q]} A(\Gamma)\right\vert{}^2}{\sum_{[Q'] \in \mathcal{V}_{\mathcal{M}}(T_k)} \left\vert{}\sum_{\Gamma' \to [Q']} A(\Gamma')\right\vert{}^2}$$

where $A(\Gamma) = \prod_{i=1}^k W(m_i)$ is the pure real product of physical mutation weights along macro-trajectory path $\Gamma$.

### Mutation Sequence Tracking & Path Analysis
Each path $\Gamma$ records its exact sequence of applied operational mutations using short codes:
* `t`: Triangulation
* `d`: Correlation Decay
* `m`: Asymptotic Metric Evolution

When multiple paths merge into the same canonical world state $[Q]$, all incoming mutation sequences are aggregated. The evaluator table extracts and displays the **most common mutation sequence** (`Top Seq`, e.g. `tdtdt` or `tmtd`) for each state.

---

## 6. Extensibility Modules

### Sub-Universe Boundary Fusion ($Q_A \oplus Q_B$)
Fuses two previously disconnected relational sub-universes $Q_A \in M_{n_A}$ and $Q_B \in M_{n_B}$ along boundary nodes subject to bridge metric equivalence:
$$\mu(i,j) = \min_{(a,b) \in E_{\text{bridge}}} (\mu_A(i, a) + \mu_{\text{bridge}}(a, b) + \mu_B(b, j))$$

### Dedicated FCR Quantum Computer Simulator
Simulates gate topologies ($\text{Hadamard } H$, $\text{Pauli-}X$, $\text{CNOT}$) acting on quantum register data subgraphs $Q_D \in \mathcal{M}_{\text{data}}$, evaluating Born-rule branch probabilities for entangled Bell states $|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$.

---

## 7. Installation & Quickstart

### Prerequisites
- **Rust toolchain** (Rust 1.80+ or 1.97+)
- **Python 3.11+** with `networkx` and `matplotlib` (for 2D graph plotting)

### Build the Project
```bash
# Clone the repository
git clone https://github.com/tcbrouwer/Fusion-Constructive-Realism.git
cd "Gemini session 09082026c"

# Build optimized release executable
cargo build --release
```

---

## 8. CLI Command Reference

The compiled binary `fcr_engine` provides high-speed CLI commands:

### 1. Macro-Trajectory Generation (`generate`)
Generate state-space branching trees across $T$ steps (starting from default $Q_0$ or a custom `.fcrstate` file):
```bash
# Default initial state
./target/release/fcr_engine.exe generate --nodes 6 --steps 3 --out-dir ./output --run-id demo_run

# From custom initial state created with fcr_repl.py
./target/release/fcr_engine.exe generate --initial-state ./custom_6node.fcrstate --steps 3 --out-dir ./output --run-id 6node_run
```

### 2. Interactive State Building REPL (`fcr_repl.py`)
Build custom initial state configurations ($M_n$) interactively:
```bash
python fcr_repl.py
```
**REPL Commands:**
- `init <n>`: Initialize $n$ nodes with default metric ($\mu=1.0$) and empty correlation graph.
- `set <a> <b> <m> <w>`: Set edge $a \leftrightarrow b$ metric distance $\mu=m$ and complex correlation weight $w$ (e.g. `set 0 1 1.0 0.8+0.2j` or `set 0 1 1.0 0.7@30`).
- `show`: Display matrix draft, capacities $S(p)$, and active edges.
- `plot`: View 2D NetworkX graph plot of draft state.
- `load <path/to/.fcrstate>`: Load an existing `.fcrstate` binary file directly into the REPL for modification or trajectory simulation.
- `run <run_id> <steps>`: Save state and immediately execute trajectory evolution & Born-rule evaluation!
- `eval <run_id> <step> [top]`: Evaluate and display top $N$ states for step $T$ (e.g. `eval qaq 36 25`, or `eval qaq 36 0` for all states).

### 3. Born-Rule Display Evaluation (`evaluate`)
Evaluate state probabilities at step $T$ (defaults to top 10 rows; use `--top <N>` or `--top 0` for all):
```bash
# Display top 25 states
./target/release/fcr_engine.exe evaluate --run-dir ./output/run_demo_run --step 3 --top 25

# Display all states (unlimited)
./target/release/fcr_engine.exe evaluate --run-dir ./output/run_demo_run --step 3 --top 0
```

### 3. State Inspection (`inspect`)
Inspect matrices, capacities $S(p)$, active edges, and parent hashes of a `.fcrstate` file:
```bash
./target/release/fcr_engine.exe inspect --file ./output/run_demo_run/T003/<HASH>.fcrstate
```

### 4. Quantum Computer Simulation (`qc-demo`)
Run Bell state $|\Phi^+\rangle$ circuit simulation:
```bash
./target/release/fcr_engine.exe qc-demo --out-dir ./output --run-id qc_bell_001
```

### 5. High-Performance Benchmark (`benchmark`)
Benchmark state-generation speed (states/sec):
```bash
./target/release/fcr_engine.exe benchmark --nodes 4 --steps 3
```

---

## 9. Visualizing & Inspecting States (`.fcrstate`)

### Python CLI Tool (`fcr_display.py`)

#### Display Probability Table:
```bash
python fcr_display.py --run-id demo_run --time-step 3
```
**Output View:**
```text
======================================================================================================================
FCR 2.1 State-Space Display Evaluator | Time Step T = 36
======================================================================================================================
Rank  Canonical WL Hash              Path Count  Edges   Avg |C|    Top Seq         Accumulated Weight   Display Prob P([Q])
----------------------------------------------------------------------------------------------------------------------
1     88fb7bb3c17edab1aa2414a...     21          15      0.4280     tdtdtd          2.1211e1             0.008146          
2     6cd2a1ba5cdd1fec048c938...     21          15      0.4266     tdtdtd          2.0164e1             0.007362          
3     46b68c2fb90a2241694a88e...     20          15      0.4283     ttddtd          1.9681e1             0.007013          
----------------------------------------------------------------------------------------------------------------------
Total Macro States: 1000 | Trajectory Path Count Sum: 6689
======================================================================================================================
```

#### Inspect Specific State File & Render 2D Graph Plot:
```bash
# Open interactive Matplotlib plot window
python fcr_display.py --file ./output/run_demo_run/T003/<WL_HASH>.fcrstate --plot

# Export high-resolution PNG diagram
python fcr_display.py --file ./output/run_demo_run/T003/<WL_HASH>.fcrstate --save-plot state_graph.png
```

---

## 10. Programmatic Library API (Rust & Python)

### Using `fcr_core` in Rust
```rust
use fcr_core::*;
use num_complex::Complex64;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Initialize State Q in M_3
    let mut q0 = StateQ::new(3);
    q0.set_c(0, 1, Complex64::new(0.8, 0.2));
    q0.set_mu(0, 1, 1.0);

    // 2. Compute Weisfeiler-Lehman Canonical Graph Hash
    let wl_hash = compute_wl_hash(&q0);
    println!("Canonical Hash: {}", wl_hash);

    // 3. Run Poset Trajectory Generator
    let params = PhysicalParameters::default();
    let generator = StateSpaceGenerator::new("./output", params);
    let meta = generator.generate_trajectories("api_run", q0, 3)?;
    println!("Generated {} states.", meta.total_states_generated);

    Ok(())
}
```

---

## 11. Testing & Verification

Run the full automated Rust unit and integration test suite:

```bash
cargo test
```

### Verified Test Cases:
- `test_state_q_axioms`: Validates metric symmetries and correlation bounds.
- `test_capacity_exceeded_and_phase_venting`: Verifies instant virtual phase venting recoil and capacity projection $S(p) \le 1.0$.
- `test_global_loop_phase_and_wl_hashing`: Tests gauge fixing $\text{Tr}(C^3)$ and permutation-invariant WL hashing.
- `test_asymptotic_metric_evolution_positivity`: Confirms metric distance positivity $\mu > 0$.
- `test_sub_universe_fusion`: Verifies multi-node boundary geodesic fusion $Q_A \oplus Q_B$.
- `test_quantum_computer_bell_state`: Simulates 2-qubit Hadamard + CNOT entangling circuit.
- `test_trajectory_generator_and_evaluator`: Validates trajectory generation, binary serialization, and display probability sum $\sum P([Q]) = 1.0$.

---

## License

Distributed under the MIT License. See `LICENSE` for details.
