#!/usr/bin/env python3
r"""
Fusion Constructive Realism (FCR) - Master State Engine & Interactive REPL
Implements ANTIGRAVITY_MASTER_SPEC.md:
- Auto-saving all intermediate state mutations to fcr_repository/
- Automated attractor discovery engine (find_attractors / discover)
- Attractor-driven boundary fusion & wedge product initialization (M3^4 -> M6 frame, M3_triangle, M3^2, M6_octahedron)
- Geodesic metric computation for uncorrelated pairs
- Dynamic capacity normalization, phase venting (M_{1/2}), link severing (< 10^-6), and graph fission
- Deterministic graph canonicalization (SHA-256 hex hash)
- Path-aware YAML repository state exporting (fcr_repository/M<n>/T_<k>/state_<HASH>.yaml)
- Interactive REPL shell with targeted local mutations, dynamic attractor wedging, and attractor search
"""

import os
import sys
import shutil
import argparse
import cmd
import math
import cmath
import hashlib
import json
import yaml
import networkx as nx

REPOS_DIR = "fcr_repository"
NOISE_THRESHOLD = 1.0e-6

class FCRStateGraph:
    """
    FCR Universe State Q = (P, mu, C) at discrete poset tick T.
    Base Set P: nodes {0, 1, ..., n-1}
    Metric mu: direct distance or shortest-path geodesic distance
    Correlation C: complex values z where |z| <= 1.0, diagonal C(i,i) = 1.0 + 0i
    """
    def __init__(self, seed_name: str = "M6_M3^4"):
        self.n = 0
        self.time_step = 0
        self.metric_matrix = []
        self.correlation_matrix = []
        self.incoming_paths = []
        self.ejected_remnants = []
        self.parent_hash = "00000000"
        self.last_mutation = "init"
        self.seed_template(seed_name)

    def clone(self):
        """Creates a deep copy of the state graph for DFS branching."""
        c = FCRStateGraph.__new__(FCRStateGraph)
        c.n = self.n
        c.time_step = self.time_step
        c.metric_matrix = [row[:] for row in self.metric_matrix]
        c.correlation_matrix = [row[:] for row in self.correlation_matrix]
        c.incoming_paths = [dict(entry) for entry in self.incoming_paths]
        c.ejected_remnants = [rem[:] for rem in self.ejected_remnants]
        c.parent_hash = self.parent_hash
        c.last_mutation = self.last_mutation
        c.last_transition_phase = self.last_transition_phase
        return c

    def _init_blank(self, n: int):
        self.n = n
        self.time_step = 0
        self.metric_matrix = [[0.0 if i == j else 1.0 for j in range(n)] for i in range(n)]
        self.correlation_matrix = [[1.0 + 0.0j if i == j else 0.0 + 0.0j for j in range(n)] for i in range(n)]
        self.incoming_paths = []
        self.ejected_remnants = []
        self.parent_hash = "00000000"
        self.last_mutation = "init"
        self.last_transition_phase = 1.0 + 0.0j
        self.auto_save_state("init", 1.0 + 0j, advance_clock=False)

    def seed_template(self, seed_name: str):
        """Initializes graph state via attractor-driven boundary fusion or wedge product template."""
        if seed_name == "M3_triangle":
            self._init_blank(3)
            for i in range(3):
                for j in range(3):
                    if i != j:
                        self.metric_matrix[i][j] = 1.0
                        self.correlation_matrix[i][j] = 0.5 + 0.0j

        elif seed_name == "M6_octahedron":
            self._init_blank(6)
            for i in range(6):
                for j in range(6):
                    if i != j and i + j != 5:
                        self.metric_matrix[i][j] = 1.0
                        self.correlation_matrix[i][j] = 0.3 + 0.0j

        elif seed_name in ["M6_M3^4", "M3^4"]:
            self._init_blank(6)
            triangles = [(0, 1, 2), (0, 3, 4), (1, 3, 5), (2, 4, 5)]
            for (u, v, w) in triangles:
                for a, b in [(u, v), (v, w), (u, w)]:
                    self.metric_matrix[a][b] = 1.0
                    self.metric_matrix[b][a] = 1.0
                    self.correlation_matrix[a][b] = 0.4 + 0.0j
                    self.correlation_matrix[b][a] = 0.4 + 0.0j

        elif seed_name in ["M3^2", "wedge_M3_M3"]:
            self._init_blank(5)
            for (u, v, w) in [(0, 1, 2), (0, 3, 4)]:
                for a, b in [(u, v), (v, w), (u, w)]:
                    self.metric_matrix[a][b] = 1.0
                    self.metric_matrix[b][a] = 1.0
                    self.correlation_matrix[a][b] = 0.4 + 0.0j
                    self.correlation_matrix[b][a] = 0.4 + 0.0j
        else:
            try:
                n_val = int(seed_name)
                if n_val == 3:
                    self.seed_template("M3_triangle")
                elif n_val == 6:
                    self.seed_template("M6_M3^4")
                else:
                    self._init_blank(n_val)
            except ValueError:
                raise ValueError(f"Unknown seed template: '{seed_name}'. Available: M6_M3^4, M3_triangle, M3^2, M6_octahedron")

        self.auto_save_state(f"seed({seed_name})", 1.0 + 0j, advance_clock=False)

    def wedge_product_compose(self, attractor_list: list):
        """Synthesizes a new state graph as the wedge product of lower-order attractors."""
        m3_count = sum(1 for a in attractor_list if a.upper() in ["M3", "M3_TRIANGLE"])
        if m3_count == 1:
            self.seed_template("M3_triangle")
        elif m3_count == 2:
            self.seed_template("M3^2")
        elif m3_count >= 4:
            self.seed_template("M6_M3^4")
        else:
            self.seed_template("M3_triangle")
        self.auto_save_state(f"wedge({','.join(attractor_list)})", 1.0 + 0j, advance_clock=False)

    def set_edge(self, i: int, j: int, mu_val: float, z_val: complex):
        """Sets edge (i, j) metric and correlation with symmetric enforcement (allowed only at T=0)."""
        if self.time_step > 0:
            raise ValueError(f"'set' is only allowed at T = 0 (current T = {self.time_step})")
        if not (0 <= i < self.n and 0 <= j < self.n):
            raise ValueError(f"Node indices ({i}, {j}) out of range for graph size {self.n}")
        if i == j:
            raise ValueError("Diagonal self-identity edges (i, i) cannot be modified.")

        z_c = complex(z_val)
        if abs(z_c) > 1.0 + 1e-9:
            raise ValueError(f"Correlation magnitude |z|={abs(z_c):.4f} exceeds 1.0")

        self.metric_matrix[i][j] = float(mu_val)
        self.metric_matrix[j][i] = float(mu_val)
        self.correlation_matrix[i][j] = z_c
        self.correlation_matrix[j][i] = z_c.conjugate()

        self.auto_save_state(f"set({i},{j})", z_c, advance_clock=False)

    def get_geodesic_distance(self, i: int, j: int) -> float:
        if i == j:
            return 0.0
        if abs(self.correlation_matrix[i][j]) > NOISE_THRESHOLD:
            return self.metric_matrix[i][j]

        G = nx.Graph()
        for u in range(self.n):
            G.add_node(u)
        for u in range(self.n):
            for v in range(u + 1, self.n):
                if abs(self.correlation_matrix[u][v]) > NOISE_THRESHOLD:
                    G.add_edge(u, v, weight=self.metric_matrix[u][v])

        try:
            return nx.shortest_path_length(G, source=i, target=j, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float("inf")

    def capacity_sum(self, p: int) -> float:
        r"""Computes external capacity sum S(p) = \sum_{q != p} |C(p, q)|^2 for node p."""
        s = 0.0
        for q in range(self.n):
            if q != p:
                s += abs(self.correlation_matrix[p][q]) ** 2
        return s

    def max_capacity_sum(self) -> float:
        return max(self.capacity_sum(p) for p in range(self.n)) if self.n > 0 else 0.0

    def is_capacity_compliant(self) -> bool:
        return self.max_capacity_sum() <= 1.0 + 1e-9

    def virtual_lock_normalize(self) -> dict:
        r"""
        Audits node capacity. Performs coherent scaling, phase venting (M_{1/2}), link severing, and graph fission.
        Auto-saves updated state to repository.
        """
        vent_events = []

        for p in range(self.n):
            s_p = self.capacity_sum(p)
            if s_p > 1.0 + 1e-9:
                delta_s = s_p - 1.0
                net_phase_vector = sum((self.correlation_matrix[p][q] for q in range(self.n) if q != p), 0.0 + 0.0j)
                phi_vent = cmath.phase(net_phase_vector)

                vent_events.append({
                    "node": p,
                    "delta_S": delta_s,
                    "phi_vent": phi_vent,
                })

                scale_factor = 1.0 / math.sqrt(s_p)
                for q in range(self.n):
                    if q != p:
                        self.correlation_matrix[p][q] *= scale_factor
                        self.correlation_matrix[q][p] = self.correlation_matrix[p][q].conjugate()

        severed_count = 0
        for u in range(self.n):
            for v in range(u + 1, self.n):
                if 0 < abs(self.correlation_matrix[u][v]) < NOISE_THRESHOLD:
                    self.correlation_matrix[u][v] = 0.0 + 0.0j
                    self.correlation_matrix[v][u] = 0.0 + 0.0j
                    severed_count += 1

        G = nx.Graph()
        for u in range(self.n):
            G.add_node(u)
        for u in range(self.n):
            for v in range(u + 1, self.n):
                if abs(self.correlation_matrix[u][v]) >= NOISE_THRESHOLD:
                    G.add_edge(u, v)

        components = list(nx.connected_components(G))
        if len(components) > 1:
            components.sort(key=len, reverse=True)
            primary = sorted(list(components[0]))

            for comp in components[1:]:
                self.ejected_remnants.append(sorted(list(comp)))

            mapping = {old_idx: new_idx for new_idx, old_idx in enumerate(primary)}
            new_n = len(primary)
            new_metric = [[0.0 for _ in range(new_n)] for _ in range(new_n)]
            new_corr = [[1.0 + 0.0j if i == j else 0.0 + 0.0j for j in range(new_n)] for i in range(new_n)]

            for i_old in primary:
                for j_old in primary:
                    i_new, j_new = mapping[i_old], mapping[j_old]
                    new_metric[i_new][j_new] = self.metric_matrix[i_old][j_old]
                    new_corr[i_new][j_new] = self.correlation_matrix[i_old][j_old]

            self.n = new_n
            self.metric_matrix = new_metric
            self.correlation_matrix = new_corr

        self.auto_save_state("lock", 1.0 + 0j, advance_clock=False)

        return {
            "vent_events": vent_events,
            "severed_count": severed_count,
            "fission_split": len(components) > 1,
            "remnants_count": len(components) - 1 if len(components) > 1 else 0,
        }

    def compute_canonical_hash(self) -> str:
        """Generates a deterministic 8-character SHA-256 Canonical Hash ID."""
        signatures = []
        for i in range(self.n):
            deg = sum(1 for j in range(self.n) if i != j and abs(self.correlation_matrix[i][j]) > NOISE_THRESHOLD)
            cap = round(self.capacity_sum(i), 4)
            signatures.append((deg, cap, i))

        canonical_order = [item[2] for item in sorted(signatures, key=lambda x: (x[0], x[1]))]

        payload = []
        for i_can in canonical_order:
            row_str = []
            for j_can in canonical_order:
                m = round(self.metric_matrix[i_can][j_can], 4)
                z = self.correlation_matrix[i_can][j_can]
                z_re, z_im = round(z.real, 4), round(z.imag, 4)
                row_str.append(f"({m:.4f},{z_re:.4f}+{z_im:.4f}i)")
            payload.append(";".join(row_str))

        full_str = f"n={self.n}|" + "|".join(payload)
        return hashlib.sha256(full_str.encode("utf-8")).hexdigest()[:8]

    def triangulate(self, i: int, x: int, j: int) -> complex:
        """Targeted Mutation 2 strictly on open 2-path i -> x -> j: C(i, j) <- C(i, x) * C(x, j)."""
        z_ij = self.correlation_matrix[i][j]
        if abs(z_ij) > NOISE_THRESHOLD:
            raise ValueError(f"Triangulation not allowed on {i} {x} {j}, since edge {i} {j} already exists")

        z1 = self.correlation_matrix[i][x]
        z2 = self.correlation_matrix[x][j]
        if abs(z1) <= NOISE_THRESHOLD or abs(z2) <= NOISE_THRESHOLD:
            raise ValueError(f"Triangulation not allowed on {i} {x} {j}, since edge {i} {x} or {x} {j} is 0")

        product = z1 * z2
        self.correlation_matrix[i][j] = product
        self.correlation_matrix[j][i] = product.conjugate()
        if self.metric_matrix[i][j] == 0.0 or self.metric_matrix[i][j] == float("inf"):
            self.metric_matrix[i][j] = 1.0
            self.metric_matrix[j][i] = 1.0

        self.auto_save_state(f"triangulate({i},{x},{j})", product)
        return product

    def decay(self, i: int, j: int, gamma: float = 0.05):
        r"""Targeted Mutation 3 strictly on edge (i, j): C(i, j) <- C(i, j) * e^{-\gamma * \mu(i, j)}."""
        z = self.correlation_matrix[i][j]
        mu = self.metric_matrix[i][j]
        factor = math.exp(-gamma * mu)
        new_z = z * factor
        self.correlation_matrix[i][j] = new_z
        self.correlation_matrix[j][i] = new_z.conjugate()

        self.auto_save_state(f"decay({i},{j})", factor + 0j)

    def metric_evolve(self, i: int, j: int, alpha: float = 0.5, beta: float = 0.1, d_rest: float = 1.0):
        r"""Targeted Mutation 4 strictly on edge (i, j): \mu(i,j) <- \mu(i,j) - \alpha |C(i,j)|^2 + \beta(d_{rest} - \mu(i,j))."""
        mu = self.metric_matrix[i][j]
        z = self.correlation_matrix[i][j]
        new_mu = mu - alpha * (abs(z) ** 2) + beta * (d_rest - mu)
        self.metric_matrix[i][j] = max(0.01, new_mu)
        self.metric_matrix[j][i] = self.metric_matrix[i][j]

        self.auto_save_state(f"metric_evolve({i},{j})", 1.0 + 0j)

    def auto_save_state(self, mutation_name: str = "mutation", transition_phase: complex = 1.0 + 0j, advance_clock: bool = True) -> str:
        r"""
        Automatically persists current state to fcr_repository/M<n>/T_<k>/state_<HASH>.yaml on every mutation.
        Any mutation except Virtual Lock (\Delta T = 0) advances the poset time clock by 1 (\Delta T = 1).
        """
        if advance_clock:
            self.time_step += 1

        curr_hash = self.compute_canonical_hash()
        self.last_mutation = mutation_name
        self.last_transition_phase = transition_phase

        # Only record state-changing mutations (triangulate, decay, lock, metric_evolve) in incoming_paths
        is_state_mutation = any(mutation_name.startswith(m) for m in ["triangulate", "decay", "lock", "metric_evolve"])
        if is_state_mutation:
            path_entry = {
                "parent_hash": self.parent_hash,
                "mutation_used": mutation_name,
                "transition_phase": {
                    "real": round(transition_phase.real, 6),
                    "imag": round(transition_phase.imag, 6),
                }
            }
            self.incoming_paths.append(path_entry)

        metrics_dict = {}
        corrs_dict = {}
        for u in range(self.n):
            for v in range(u + 1, self.n):
                metrics_dict[f"[{u},{v}]"] = round(self.metric_matrix[u][v], 4)
                z = self.correlation_matrix[u][v]
                corrs_dict[f"[{u},{v}]"] = {"real": round(z.real, 6), "imag": round(z.imag, 6)}

        data = {
            "metadata": {
                "level": self.n,
                "poset_step_T": self.time_step,
                "canonical_hash": curr_hash,
                "visit_count": 1,
            },
            "incoming_paths": self.incoming_paths,
            "state_matrices": {
                "nodes": list(range(self.n)),
                "metric_distances": metrics_dict,
                "correlations": corrs_dict,
            },
            "capacity_audit": {
                "max_node_sum": round(self.max_capacity_sum(), 6),
                "is_capacity_compliant": self.is_capacity_compliant(),
            }
        }

        dir_path = os.path.join(REPOS_DIR, f"M{self.n}", f"T_{self.time_step}")
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"state_{curr_hash}.yaml")

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = yaml.safe_load(f)
                v_count = existing.get("metadata", {}).get("visit_count", 1) + 1
                data["metadata"]["visit_count"] = v_count
            except Exception:
                pass

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)

        self.parent_hash = curr_hash
        return file_path

    def step_and_save(self) -> str:
        """Advances poset clock T -> T + 1 and saves state YAML to fcr_repository/."""
        return self.auto_save_state("step", 1.0 + 0j, advance_clock=True)

    def discover_attractors(self, max_depth: int = 5) -> dict:
        r"""
        Executes a Depth-First Search (DFS) over topodynamical mutation branches up to max_depth (default: 5)
        to discover stable attractors (capacity compliant states with closed phase recirculation Q_{T+k} \cong Q_T).
        """
        discovered = []
        seen_attractor_hashes = set()
        visited_branch_hashes = set()

        att_dir = os.path.join(REPOS_DIR, "attractors")
        os.makedirs(att_dir, exist_ok=True)

        def dfs(state: FCRStateGraph, depth: int, path_hashes: list):
            curr_hash = state.compute_canonical_hash()

            if curr_hash in path_hashes:
                first_idx = path_hashes.index(curr_hash)
                period = len(path_hashes) - first_idx
                if curr_hash not in seen_attractor_hashes:
                    seen_attractor_hashes.add(curr_hash)
                    attractor_info = {
                        "canonical_hash": curr_hash,
                        "depth_found": depth,
                        "period_length": period,
                        "nodes": state.n,
                        "max_capacity_sum": state.max_capacity_sum(),
                        "is_compliant": state.is_capacity_compliant(),
                    }
                    discovered.append(attractor_info)

                    att_file = os.path.join(att_dir, f"attractor_{curr_hash}.yaml")
                    src_file = os.path.join(REPOS_DIR, f"M{state.n}", f"T_{state.time_step}", f"state_{curr_hash}.yaml")
                    if os.path.exists(src_file):
                        shutil.copy(src_file, att_file)
                    else:
                        state.auto_save_state("attractor_discovery", 1.0 + 0j, advance_clock=False)
                        src_file = os.path.join(REPOS_DIR, f"M{state.n}", f"T_{state.time_step}", f"state_{curr_hash}.yaml")
                        if os.path.exists(src_file):
                            shutil.copy(src_file, att_file)
                return

            if depth >= max_depth:
                return

            if (curr_hash, depth) in visited_branch_hashes:
                return
            visited_branch_hashes.add((curr_hash, depth))

            new_path = path_hashes + [curr_hash]

            # 1. Triangulation branches
            for i in range(state.n):
                for x in range(state.n):
                    if x == i: continue
                    for j in range(state.n):
                        if j == i or j == x: continue
                        if abs(state.correlation_matrix[i][j]) <= NOISE_THRESHOLD and \
                           abs(state.correlation_matrix[i][x]) > NOISE_THRESHOLD and \
                           abs(state.correlation_matrix[x][j]) > NOISE_THRESHOLD:
                            child = state.clone()
                            try:
                                child.triangulate(i, x, j)
                                dfs(child, depth + 1, new_path)
                            except Exception:
                                pass

            # 2. Decay branches
            for u in range(state.n):
                for v in range(u + 1, state.n):
                    if abs(state.correlation_matrix[u][v]) > NOISE_THRESHOLD:
                        child = state.clone()
                        try:
                            child.decay(u, v, gamma=0.1)
                            dfs(child, depth + 1, new_path)
                        except Exception:
                            pass

            # 3. Metric Evolve branches
            for u in range(state.n):
                for v in range(u + 1, state.n):
                    if abs(state.correlation_matrix[u][v]) > NOISE_THRESHOLD:
                        child = state.clone()
                        try:
                            child.metric_evolve(u, v)
                            dfs(child, depth + 1, new_path)
                        except Exception:
                            pass

            # 4. Virtual Lock branch
            if not state.is_capacity_compliant():
                child = state.clone()
                try:
                    child.virtual_lock_normalize()
                    dfs(child, depth + 1, new_path)
                except Exception:
                    pass

        dfs(self, 0, [])

        return {
            "max_depth": max_depth,
            "branches_visited": len(visited_branch_hashes),
            "discovered_attractors": discovered,
        }

    def render_display(self) -> str:
        """Renders the n x n state matrix grid formatted according to ANTIGRAVITY_MASTER_SPEC.md."""
        current_hash = self.compute_canonical_hash()
        lines = []
        lines.append(f"=== FCR State: M{self.n} | Step T = {self.time_step} | Hash: {current_hash} ===")
        lines.append("")

        col_w = 20
        header_cells = [f"{c:^{col_w}}" for c in range(self.n)]
        header_str = "    | " + " | ".join(header_cells)
        sep_str = "----+" + "+".join(["-" * (col_w + 2)] * self.n)

        lines.append(header_str)
        lines.append(sep_str)

        for i in range(self.n):
            row_cells = []
            for j in range(self.n):
                mu = self.get_geodesic_distance(i, j)
                mu_str = f"{mu:.1f}" if mu != float("inf") else "inf"
                z = self.correlation_matrix[i][j]
                if abs(z) < NOISE_THRESHOLD and i != j:
                    cell_text = f"({mu_str}, 0.0)"
                else:
                    z_str = f"{z.real:.2f}+{z.imag:.2f}i" if z.imag >= 0 else f"{z.real:.2f}{z.imag:.2f}i"
                    cell_text = f"({mu_str}, {z_str})"
                row_cells.append(f"{cell_text:^{col_w}}")
            lines.append(f" {i:2d} | " + " | ".join(row_cells))

        lines.append("")
        lines.append("Capacity Audit:")
        for i in range(self.n):
            cap = self.capacity_sum(i)
            status = "[OVERLOADED!]" if cap > 1.0 + 1e-9 else "[OK]"
            lines.append(f"  Node {i}: capacity_sum = {cap:.6f} <= 1.0 {status}")

        if self.ejected_remnants:
            lines.append(f"\nEjected Radiation Remnants (M2 chains): {self.ejected_remnants}")

        return "\n".join(lines)


class FCRMasterRepl(cmd.Cmd):
    intro = "\n=================================================================\n  FUSION CONSTRUCTIVE REALISM (FCR) MASTER INTERACTIVE REPL\n=================================================================\nType 'help' or '?' to list commands.\n"
    prompt = "fcr> "

    def __init__(self, seed_name: str = "M6_M3^4"):
        super().__init__()
        self.state = FCRStateGraph(seed_name=seed_name)

    def do_init(self, arg):
        """init <seed_or_n> : Initializes graph state via attractor template (M6_M3^4, M3_triangle, M3^2, M6_octahedron)."""
        seed_name = arg.strip() if arg.strip() else "M6_M3^4"
        try:
            self.state = FCRStateGraph(seed_name=seed_name)
            print(f"Initialized graph state via attractor seed: '{seed_name}'")
            print(self.state.render_display())
        except ValueError as e:
            print(f"Error: {e}")

    def do_seed(self, arg):
        """seed <type> : Loads a boundary assembly seed template (M6_M3^4, M3_triangle, M3^2, M6_octahedron)."""
        self.do_init(arg)

    def do_wedge(self, arg):
        """wedge <attractor1> [attractor2 ...] : Synthesizes state space via wedge product of lower-order attractors. Example: wedge M3 M3"""
        attractors = arg.strip().split()
        if not attractors:
            print("Error: Usage 'wedge <attractor1> <attractor2> ...'")
            return
        self.state.wedge_product_compose(attractors)
        print(f"Synthesized wedge product of attractors: {attractors}")
        print(self.state.render_display())

    def do_show(self, arg):
        """show / print : Redraws the n x n state matrix grid and capacity audit."""
        print(self.state.render_display())

    do_print = do_show

    def do_set(self, arg):
        """set <i,j> <mu> <z_re+z_im> : Sets edge (i, j) metric and complex correlation (allowed only at T=0). Example: set 0,1 1.0 0.707+0.707j"""
        try:
            parts = arg.strip().split()
            if len(parts) < 3:
                print("Error: Usage 'set <i,j> <mu> <z_re+z_im>'")
                return
            ij = parts[0].split(",")
            i, j = int(ij[0]), int(ij[1])
            mu_val = float(parts[1])
            z_val = complex(parts[2].replace("j", "j").replace("I", "j"))
            self.state.set_edge(i, j, mu_val, z_val)
            print(f"Edge ({i}, {j}) updated.")
            print(self.state.render_display())
        except ValueError as e:
            print(f"Warning: {e}")
        except Exception as e:
            print(f"Error updating edge: {e}")

    def do_triangulate(self, arg):
        """triangulate <i> <x> <j> : Executes Mutation 2 strictly on open 2-path i -> x -> j."""
        parts = arg.strip().split()
        if len(parts) < 3:
            print("Error: Usage 'triangulate <i> <x> <j>'")
            return
        try:
            i, x, j = int(parts[0]), int(parts[1]), int(parts[2])
            prod = self.state.triangulate(i, x, j)
            print(f"Executed Mutation 2 (Triangulation) on path {i} -> {x} -> {j}: C({i},{j}) = {prod}")
            print(self.state.render_display())
        except ValueError as e:
            print(f"Warning: {e}")
        except Exception as e:
            print(f"Error: {e}")

    def do_decay(self, arg):
        """decay <i> <j> [gamma] : Executes Mutation 3 strictly on edge (i, j). Example: decay 0 1 0.1"""
        try:
            parts = arg.strip().split()
            i, j = int(parts[0]), int(parts[1])
            gamma = float(parts[2]) if len(parts) > 2 else 0.1
            self.state.decay(i, j, gamma)
            print(f"Executed Mutation 3 (Decay) on edge ({i},{j}) with gamma={gamma}.")
            print(self.state.render_display())
        except Exception as e:
            print(f"Error: Usage 'decay <i> <j> [gamma]' ({e})")

    def do_metric_evolve(self, arg):
        """metric_evolve <i> <j> : Executes Mutation 4 strictly on edge (i, j)."""
        try:
            parts = arg.strip().split()
            i, j = int(parts[0]), int(parts[1])
            self.state.metric_evolve(i, j)
            print(f"Executed Mutation 4 (Metric Evolution) on edge ({i},{j}).")
            print(self.state.render_display())
        except Exception as e:
            print(f"Error: Usage 'metric_evolve <i> <j>' ({e})")

    def do_lock(self, arg):
        """lock : Audits capacity. If overloaded (> 1.0), performs coherent scaling, vents M_{1/2}, severs links < 10^-6, splits fission components."""
        res = self.state.virtual_lock_normalize()
        print("Executed Sub-Tick Virtual Lock Normalization:")
        print(f"  Phase Venting (M_1/2) Events : {len(res['vent_events'])}")
        print(f"  Severed Noise Links          : {res['severed_count']}")
        print(f"  Fission Component Split      : {res['fission_split']}")
        print(self.state.render_display())

    def do_discover(self, arg):
        """discover [max_depth] / find_attractors : Executes Depth-First Search (DFS) over topodynamical mutation branches up to max_depth (default: 5)."""
        max_depth = int(arg.strip()) if arg.strip() else 5
        print(f"Running Depth-First Search (DFS) attractor discovery loop up to max depth {max_depth}...")
        res = self.state.discover_attractors(max_depth=max_depth)
        print(f"Visited {res['branches_visited']} mutation branch states across max depth {res['max_depth']}.")
        if res["discovered_attractors"]:
            print(f"\n🎉 DISCOVERED {len(res['discovered_attractors'])} STABLE ATTRACTOR(S):")
            for att in res["discovered_attractors"]:
                print(f"  - Canonical Hash : {att['canonical_hash']}")
                print(f"    Depth Found    : depth {att['depth_found']}")
                print(f"    Period Length  : {att['period_length']} steps")
                print(f"    Nodes          : {att['nodes']}")
                print(f"    Max Capacity   : {att['max_capacity_sum']:.6f} <= 1.0")
                print(f"    Registered at  : fcr_repository/attractors/attractor_{att['canonical_hash']}.yaml")
        else:
            print(f"No limit cycles encountered within max depth {max_depth}.")
        print(self.state.render_display())

    do_find_attractors = do_discover

    def do_attractors(self, arg):
        """attractors : Scans repository for registered attractors and states satisfying closed phase recirculation."""
        print("Scanning repository for topodynamical attractors...")
        attractor_records = []
        seen_hashes = set()

        att_dir = os.path.join(REPOS_DIR, "attractors")
        if os.path.exists(att_dir):
            for f in os.listdir(att_dir):
                if f.endswith(".yaml"):
                    fpath = os.path.join(att_dir, f)
                    try:
                        with open(fpath, "r", encoding="utf-8") as yf:
                            data = yaml.safe_load(yf)
                        h = data.get("metadata", {}).get("canonical_hash", f)
                        v_count = data.get("metadata", {}).get("visit_count", 1)
                        attractor_records.append((fpath, h, v_count))
                        seen_hashes.add(h)
                    except Exception:
                        pass

        if os.path.exists(REPOS_DIR):
            for root, dirs, files in os.walk(REPOS_DIR):
                if "attractors" in root:
                    continue
                for f in files:
                    if f.endswith(".yaml"):
                        fpath = os.path.join(root, f)
                        try:
                            with open(fpath, "r", encoding="utf-8") as yf:
                                data = yaml.safe_load(yf)
                            h = data.get("metadata", {}).get("canonical_hash")
                            v_count = data.get("metadata", {}).get("visit_count", 1)
                            if (v_count > 1 or h in seen_hashes) and h not in seen_hashes:
                                attractor_records.append((fpath, h, v_count))
                                seen_hashes.add(h)
                        except Exception:
                            pass

        if attractor_records:
            print(f"Found {len(attractor_records)} registered / recirculating attractor state records:")
            for fpath, h, visits in attractor_records:
                print(f"  - Hash: {h} | File: {fpath} (Visit Count: {visits})")
        else:
            print("No recirculating attractor states recorded yet in repository.")

    def do_exit(self, arg):
        """exit / quit : Quits the REPL session."""
        print("Exiting FCR Master REPL.")
        return True

    do_quit = do_exit


def main():
    parser = argparse.ArgumentParser(description="FCR Master Interactive REPL")
    parser.add_argument("--seed", "-s", "--wedge", type=str, default="M6_M3^4", help="Initial attractor seed or wedge product (default: M6_M3^4)")
    parser.add_argument("--nodes", "-n", type=int, default=None, help="Initial number of nodes (legacy option)")
    args = parser.parse_args()

    seed_name = args.seed
    if args.nodes is not None:
        seed_name = str(args.nodes)

    repl = FCRMasterRepl(seed_name=seed_name)
    print(repl.state.render_display())
    repl.cmdloop()


if __name__ == "__main__":
    main()
