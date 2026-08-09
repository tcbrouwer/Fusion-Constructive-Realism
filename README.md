# Fusion Constructive Realism (FCR) System

Attractor-driven boundary fusion state engine, interactive master REPL (`fcr_repl.py`), offline Born-rule probability analyzer (`fcr_analyzer.py`), high-performance Rust algebraic compute engine (`fusion_constructive_realism`), and C-API bindings for **Fusion Constructive Realism (FCR)**.

FCR replaces naive $N \times N$ matrix graph-stepping simulations with discrete group representation theory, group word metrics, spectral transfer operators, dynamic capacity normalization, phase venting ($\mathcal{M}_{1/2}$), link severing, graph fission, auto-saved state histories, and path-aware repository analysis to calculate non-local quantum correlations, Born-rule display probability distributions, and analytic lepton mass hierarchies in $O(\text{poly}(\log N))$ memory.

---

## Technical Specifications & Papers

1. **`ANTIGRAVITY_MASTER_SPEC.md`**: Master system specification for attractor-driven boundary fusion, auto-saved repository state tracking, and offline Born-rule probability analyzer.
2. **`ANTIGRAVITY_REPL_SPEC.md`**: Specification for the interactive terminal REPL.
3. **`fcr_master_spec.md`**: Developer specification for the algebraic C++/Rust compute engine modules.
4. **`FCR_Fundamentals.pdf`**: Axiomatic physics foundation paper establishing primitive space $(P, \mu, C)$, topodynamical mutation laws, Virtual Lock $\mathcal{M}_{1/2}$, and mass scaling laws.
5. **`FCR_Compute_Paradigm.pdf`**: Algebraic compute paradigm paper leveraging discrete group coset representations, character-based DAG deduplication, and sparse transfer operators.

---

## 1. Interactive Master REPL (`fcr_repl.py`)

Launch the master REPL shell. State graphs initialize directly as **attractor wedge products** ($\mathcal{M}_3^4 \to \mathcal{M}_6$ octahedral frame default). Every intermediate topodynamical state mutation (`triangulate`, `decay`, `metric_evolve`) advances the poset clock by 1 ($\Delta T = 1$) and **automatically persists** its state record to `fcr_repository/M<n>/T_<k>/state_<HASH>.yaml`. Setup operations (`set` at $T=0$, `lock` sub-tick) operate at $\Delta T = 0$ without advancing the clock:

```bash
python fcr_repl.py --seed M6_M3^4
```

### REPL Commands

| Command | Description | Clock ($\Delta T$) | Example / Operation |
| --- | --- | --- | --- |
| `show` / `print` | Redraws the $n \times n$ state matrix grid and capacity audit bounds. | $\Delta T = 0$ | Displays aligned matrix of geodesic $(\mu_{ij}, z_{ij})$. |
| `init <seed_name>` | Initializes graph state via attractor template (`M6_M3^4`, `M3_triangle`, `M3^2`, `M6_octahedron`). | $T = 0$ | `init M6_M3^4` |
| `seed <type>` | Loads a boundary assembly seed template. | $T = 0$ | `seed M6_octahedron` |
| `wedge <a1> <a2> ...` | Synthesizes state space via wedge product of lower-order attractors. | $T = 0$ | `wedge M3 M3` |
| `set <i,j> <mu> <z>` | Sets edge $(i, j)$ metric and complex correlation value (allowed **only at $T=0$**). | $\Delta T = 0$ | `set 0,1 1.0 0.707+0.707j` |
| `triangulate <i> <x> <j>` | Executes Mutation 2 strictly on open 2-path $i \to x \to j$. | $\Delta T = 1$ | $C(i,j) \leftarrow C(i,x) \cdot C(x,j)$ (Auto-Saved) |
| `decay <i> <j> [gamma]` | Executes Mutation 3 strictly on edge $(i, j)$. | $\Delta T = 1$ | $C(i,j) \leftarrow C(i,j) \cdot e^{-\gamma \mu_{ij}}$ (Auto-Saved) |
| `metric_evolve <i> <j>` | Executes Mutation 4 strictly on edge $(i, j)$. | $\Delta T = 1$ | $\mu_{ij} \leftarrow \mu_{ij} - \alpha \|z_{ij}\|^2 + \beta(1 - \mu_{ij})$ (Auto-Saved) |
| `lock` | Audits capacity. Scales coherently ($C \leftarrow C/\sqrt{S}$), vents $\mathcal{M}_{1/2}$, severs links $<10^{-6}$, splits fission components. | $\Delta T = 0$ (Sub-Tick) | Phase venting & link severing (Auto-Saved) |
| `discover [max_depth]` | Executes Depth-First Search (DFS) over topodynamical mutation branches up to `max_depth` (default: 5) to discover stable attractors. | DFS tree | Registers discovered attractors to `fcr_repository/attractors/`. |
| `attractors` | Scans repository for registered attractors and states satisfying closed phase recirculation ($Q_{T+k} \cong Q_T$). | $\Delta T = 0$ | Searches topodynamical limit cycles. |
| `exit` / `quit` | Quits the REPL session. | - | Stops program. |

---

## 2. Offline Born-Rule Probability Analyzer (`fcr_analyzer.py`)

Scans state transition records in `fcr_repository/M<n>/T_<k>/`, reconstructs convergent path trajectories $\gamma$, evaluates path phase products $Z(\gamma) = \prod_{e \in \gamma} z_e$, and computes the Born-rule display probability distribution:

$$P(Q) = \frac{\left| \sum_{\gamma \to Q} Z(\gamma) \right|^2}{\sum_{Q'} \left| \sum_{\gamma' \to Q'} Z(\gamma') \right|^2}$$

Run analyzer:
```bash
python fcr_analyzer.py --level 6 --step 1
```

Exports JSON summary report to `fcr_repository/probability_report_M<n>_T<k>.json`.

---

## 3. High-Performance Rust Compute Engine (`fusion_constructive_realism`)

1. **`fcr_groups` ([src/groups.rs](file:///c:/Users/timcb/Projects/Fusion-Constructive-Realism/src/groups.rs))**: Discrete symmetry groups $\mathbb{Z}_3$ (electron $e^-$), $O_h$ (muon $\mu^-$), $I_h$ (tau $\tau^-$), and $O(1)$ word metric lookup.
2. **`fcr_state` ([src/state.rs](file:///c:/Users/timcb/Projects/Fusion-Constructive-Realism/src/state.rs))**: State character profiles $\chi_Q(g)$, BLAKE3 canonical $O(1)$ state hashing, and Quotient DAG deduplication.
3. **`fcr_solver` ([src/solver.rs](file:///c:/Users/timcb/Projects/Fusion-Constructive-Realism/src/solver.rs))**: Sub-tick Virtual Lock character irrep decomposition and capacity audit ($N(p) \le 1.0$).
4. **`fcr_transfer` ([src/transfer.rs](file:///c:/Users/timcb/Projects/Fusion-Constructive-Realism/src/transfer.rs))**: Sparse Transfer Operator $\mathbf{T}$, Lanczos eigensolver, and Born-rule display probabilities $P(d_k)$.
5. **`fcr_benchmarks` ([src/benchmarks.rs](file:///c:/Users/timcb/Projects/Fusion-Constructive-Realism/src/benchmarks.rs))**: Effective resistance $\Omega(G)$, Kirchhoff tree counts $\tau(G)$, and analytic lepton mass ratios ($m_e=1.0$, $m_\mu/m_e \approx 208$, $m_\tau/m_e \approx 3478$).

---

## Build & Testing Instructions

### 1. Run Master Python Unit Tests
```bash
python -m unittest discover tests/
```

### 2. Run Rust Integration Tests
```bash
cargo test -- --nocapture
```

### 3. Build C-API Shared Library
```bash
cargo build --release
```

### 4. Run Python Verification
```bash
python verify_fcr.py
```
