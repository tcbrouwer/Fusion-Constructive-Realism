#!/usr/bin/env python3
"""
FCR 2.1 Interactive State Building & Trajectory REPL (fcr_repl.py)

Commands:
  init <n>                  - Initialize n nodes with default metric (1.0) and empty correlation graph
  set <a> <b> <m> <w>       - Set edge a-b metric to m and complex correlation to w
                              (e.g., set 0 1 1.0 0.8+0.2j or set 0 1 1.0 0.5@45)
  show                      - Print current draft state matrices, capacities S(p), and active edges
  plot                      - Open 2D NetworkX graph plot window of the current draft state
  load <path/to/.fcrstate>  - Load a state from a .fcrstate file into the REPL
  save [path_or_dir]        - Save current state to .fcrstate file (uses WL hash for filename if dir given)
  run [run_id] [steps]      - Save & launch trajectory evolution from this custom state Q0
  help                      - Display help menu
  exit / quit               - Exit REPL
"""

import os
import sys
import re
import json
import cmath
import argparse
import subprocess
from pathlib import Path

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_PLOT_LIBS = True
except ImportError:
    HAS_PLOT_LIBS = False


def get_engine_exe():
    exe_name = "fcr_engine.exe" if sys.platform == "win32" else "fcr_engine"
    target_exe = Path("target/release") / exe_name
    debug_exe = Path("target/debug") / exe_name
    if target_exe.exists():
        return str(target_exe)
    elif debug_exe.exists():
        return str(debug_exe)
    return None

ENGINE_EXE = get_engine_exe()

def parse_complex(val_str):
    val_str = val_str.strip().replace("i", "j")
    # Check polar format e.g. "0.8@45" or "0.8@45deg"
    if "@" in val_str:
        parts = val_str.split("@")
        mag = float(parts[0])
        deg_str = parts[1].replace("deg", "").strip()
        rad = np.radians(float(deg_str))
        return cmath.rect(mag, rad)
    # Check comma separated e.g. "0.8, 0.2"
    if "," in val_str:
        parts = val_str.split(",")
        return complex(float(parts[0]), float(parts[1]))
    # Standard Python complex parser
    return complex(val_str)


class FcrReplState:
    def __init__(self, n=3):
        self.n = n
        self.mu = [1.0] * (n * n)
        self.c = [[0.0, 0.0] for _ in range(n * n)]

        for i in range(n):
            self.mu[i * n + i] = 0.0
            self.c[i * n + i] = [1.0, 0.0]

    def set_edge(self, i, j, mu_val, c_val):
        if i >= self.n or j >= self.n:
            raise ValueError(f"Node index out of range (n={self.n})")
        if i == j:
            raise ValueError("Self-loops cannot be modified manually")

        c_comp = parse_complex(str(c_val)) if not isinstance(c_val, complex) else c_val
        mu_f = float(mu_val)

        idx1 = i * self.n + j
        idx2 = j * self.n + i

        self.mu[idx1] = mu_f
        self.mu[idx2] = mu_f

        self.c[idx1] = [c_comp.real, c_comp.imag]
        self.c[idx2] = [c_comp.real, -c_comp.imag]

    def calculate_capacity(self, p):
        s_p = 0.0
        for q in range(self.n):
            if q != p:
                c_val = self.c[p * self.n + q]
                if isinstance(c_val, (list, tuple)):
                    re, im = c_val[0], c_val[1]
                elif isinstance(c_val, dict):
                    re, im = c_val.get("re", 0.0), c_val.get("im", 0.0)
                else:
                    re, im = 0.0, 0.0
                s_p += (re**2 + im**2)
        return s_p

    def to_json(self):
        return json.dumps({
            "n": self.n,
            "mu": self.mu,
            "c": self.c,
            "last_mutation_type": 0,
            "node_capacity_exceeded": 0,
        })

    def show(self):
        print(f"\n========================================================================================")
        print(f"FCR 2.1 State Draft (n = {self.n} nodes)")
        print(f"========================================================================================")
        print("--- Node Capacities S(p) ---")
        for p in range(self.n):
            s_p = self.calculate_capacity(p)
            status = "EXCEEDED (>1.0)" if s_p > 1.0 + 1e-6 else "OK"
            print(f"  Node {p:>2} | S(p) = {s_p:.6f}  [{status}]")

        print("\n--- Complex Correlation Matrix C(i,j) [Magnitude @ Phase (deg)] ---")
        header = "    " + "".join([f"   Node {j:<2}      " for j in range(self.n)])
        print(header)
        for i in range(self.n):
            row_str = f"N{i:>2} "
            for j in range(self.n):
                c_val = self.c[i * self.n + j]
                if isinstance(c_val, (list, tuple)):
                    re, im = c_val[0], c_val[1]
                elif isinstance(c_val, dict):
                    re, im = c_val.get("re", 0.0), c_val.get("im", 0.0)
                else:
                    re, im = 0.0, 0.0
                mag = np.hypot(re, im)
                deg = np.degrees(np.arctan2(im, re))
                row_str += f"[{mag:.3f} @ {deg:>5.1f}°] "
            print(row_str)

        print("\n--- Spatial Metric Matrix mu(i,j) ---")
        header_mu = "    " + "".join([f"  Node {j:<2} " for j in range(self.n)])
        print(header_mu)
        for i in range(self.n):
            row_mu = f"N{i:>2} "
            for j in range(self.n):
                mu_val = self.mu[i * self.n + j]
                row_mu += f" {mu_val:>7.4f} "
            print(row_mu)

        print("\n--- Active Edges (|C| > 1e-6) ---")
        active = 0
        for i in range(self.n):
            for j in range(i + 1, self.n):
                c_val = self.c[i * self.n + j]
                if isinstance(c_val, (list, tuple)):
                    re, im = c_val[0], c_val[1]
                elif isinstance(c_val, dict):
                    re, im = c_val.get("re", 0.0), c_val.get("im", 0.0)
                else:
                    re, im = 0.0, 0.0
                mag = np.hypot(re, im)
                deg = np.degrees(np.arctan2(im, re))
                if mag > 1e-6:
                    active += 1
                    print(f"  Edge ({i:>2} <-> {j:>2}) | Mag: {mag:.6f} | Phase: {deg:>6.2f}° | Metric mu: {self.mu[i*self.n+j]:.4f}")
        if active == 0:
            print("  (No active edges)")
        print(f"========================================================================================\n")


def load_state_from_fcrstate(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File '{path}' does not exist.", file=sys.stderr)
        return None

    if ENGINE_EXE:
        cmd = [ENGINE_EXE, "inspect", "--file", str(path), "--json"]
    else:
        cmd = ["cargo", "run", "--quiet", "--", "inspect", "--file", str(path), "--json"]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error reading .fcrstate file: {res.stderr}", file=sys.stderr)
        return None

    try:
        record_json = json.loads(res.stdout)
        state_data = record_json["state"]
        n = state_data["n"]
        new_state = FcrReplState(n)
        new_state.mu = list(state_data["mu"])
        new_state.c = list(state_data["c"])
        wl_hash = record_json.get("wl_hash", "UNKNOWN")
        print(f"[+] Successfully loaded state from: {path}")
        print(f"  Nodes n: {n}")
        print(f"  Canonical WL Hash: {wl_hash}")
        return new_state
    except Exception as e:
        print(f"Error parsing .fcrstate payload: {e}", file=sys.stderr)
        return None


def save_state_to_fcrstate(state_obj, out_path_or_dir):
    out_path = Path(out_path_or_dir)
    json_str = state_obj.to_json()

    if ENGINE_EXE:
        cmd = [ENGINE_EXE, "save-state", "--json-state", json_str, "--out-dir", str(out_path if out_path.is_dir() or not out_path.suffix else out_path.parent)]
    else:
        cmd = ["cargo", "run", "--quiet", "--", "save-state", "--json-state", json_str, "--out-dir", str(out_path if out_path.is_dir() or not out_path.suffix else out_path.parent)]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error saving state: {res.stderr}", file=sys.stderr)
        return None

    # Parse output WL_HASH
    wl_hash = None
    saved_file = None
    for line in res.stdout.splitlines():
        if "WL_HASH:" in line:
            wl_hash = line.split(":")[-1].strip()
        if "Saved state to:" in line:
            saved_file = line.split(":", 1)[-1].strip().strip('"')

    if out_path.suffix == ".fcrstate" and saved_file and Path(saved_file).exists():
        target_file = out_path
        if target_file != Path(saved_file):
            import shutil
            shutil.copy(saved_file, target_file)
            saved_file = str(target_file)

    print(f"[+] Saved state to: {saved_file}")
    if wl_hash:
        print(f"  Canonical WL Hash: {wl_hash}")
    return saved_file


def run_repl():
    print("========================================================================================")
    print("FCR 2.1 Interactive State Building & Trajectory REPL")
    print("Type 'help' for available commands or 'exit' to quit.")
    print("========================================================================================\n")

    current_state = FcrReplState(3)
    last_saved_file = None

    while True:
        try:
            line = input("fcr> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting REPL.")
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ["exit", "quit"]:
            print("Exiting REPL.")
            break

        elif cmd == "help":
            print("""
Available REPL Commands:
  init <n>                  - Initialize n nodes with default metric (1.0) and empty correlation graph
  set <a> <b> <m> <w>       - Set edge a-b metric to m and complex correlation to w
                              Syntaxes for w: 0.8+0.2j, 0.8+0.2i, 0.8,0.2, 0.5, or 0.8@45
  show                      - Print state draft matrices, node capacities S(p), and active edges
  plot                      - View 2D NetworkX graph plot of draft state
  load <path/to/.fcrstate>  - Load a specified state file into the REPL
  save [path_or_dir]        - Save state to binary .fcrstate file (defaults to ./output)
  run [run_id] [steps]      - Save & launch trajectory evolution from this custom state Q0
  eval [run_id] [step] [top]- Evaluate display probabilities for step T with top N rows (0 for all)
  help                      - Show this help menu
  exit / quit               - Exit REPL
""")

        elif cmd == "init":
            if len(parts) < 2:
                print("Usage: init <n>")
                continue
            try:
                n = int(parts[1])
                if n < 1:
                    raise ValueError()
                current_state = FcrReplState(n)
                print(f"[+] Initialized new state with n = {n} nodes.")
            except ValueError:
                print("Error: n must be a positive integer.")

        elif cmd == "set":
            if len(parts) < 5:
                print("Usage: set <a> <b> <m> <w>  (e.g., set 0 1 1.0 0.8+0.2j or set 0 1 1.0 0.5@45)")
                continue
            try:
                a = int(parts[1])
                b = int(parts[2])
                m = float(parts[3])
                w_str = parts[4]
                current_state.set_edge(a, b, m, w_str)
                print(f"[+] Set edge ({a} <-> {b}): metric mu = {m}, correlation C = {parse_complex(w_str)}")
            except Exception as e:
                print(f"Error setting edge: {e}")

        elif cmd in ["show", "status"]:
            current_state.show()

        elif cmd == "plot":
            if not HAS_PLOT_LIBS:
                print("Error: matplotlib and networkx are required for plotting.", file=sys.stderr)
                continue
            from fcr_display import plot_state_graph
            plot_state_graph({"n": current_state.n, "state": {"c": current_state.c, "mu": current_state.mu}, "wl_hash": "DRAFT", "path_count": 1, "accumulated_weight_a": 1.0})

        elif cmd == "load":
            if len(parts) < 2:
                print("Usage: load <path/to/.fcrstate>")
                continue
            loaded = load_state_from_fcrstate(parts[1])
            if loaded:
                current_state = loaded

        elif cmd == "save":
            out_dir = parts[1] if len(parts) > 1 else "./output"
            saved_file = save_state_to_fcrstate(current_state, out_dir)
            if saved_file:
                last_saved_file = saved_file

        elif cmd == "run":
            run_id = parts[1] if len(parts) > 1 else "custom_run_001"
            steps = int(parts[2]) if len(parts) > 2 else 3
            top_states = int(parts[3]) if len(parts) > 3 else 100
            out_dir = "./output"

            saved_file = save_state_to_fcrstate(current_state, out_dir)
            if not saved_file:
                print("Error: Could not save initial state for run.")
                continue

            print(f"\nLaunching trajectory generation starting from Q0 = {saved_file} (top_states={top_states})...")
            if ENGINE_EXE:
                cmd_gen = [ENGINE_EXE, "generate", "--initial-state", saved_file, "--run-id", run_id, "--steps", str(steps), "--top-states", str(top_states), "--out-dir", out_dir]
            else:
                cmd_gen = ["cargo", "run", "--quiet", "--", "generate", "--initial-state", saved_file, "--run-id", run_id, "--steps", str(steps), "--top-states", str(top_states), "--out-dir", out_dir]

            subprocess.run(cmd_gen)

            print(f"\nEvaluating display probabilities at step T = {steps}...")
            run_dir = Path(out_dir) / f"run_{run_id}"
            if ENGINE_EXE:
                cmd_eval = [ENGINE_EXE, "evaluate", "--run-dir", str(run_dir), "--step", str(steps), "--top", "10"]
            else:
                cmd_eval = ["cargo", "run", "--quiet", "--", "evaluate", "--run-dir", str(run_dir), "--step", str(steps), "--top", "10"]
            subprocess.run(cmd_eval)

        elif cmd in ["eval", "evaluate"]:
            run_id = parts[1] if len(parts) > 1 else "custom_run_001"
            step = int(parts[2]) if len(parts) > 2 else 3
            top = int(parts[3]) if len(parts) > 3 else 10

            out_dir = "./output"
            run_dir = Path(out_dir) / f"run_{run_id}"
            if not run_dir.exists():
                print(f"Error: Run directory '{run_dir}' does not exist.", file=sys.stderr)
                continue

            if ENGINE_EXE:
                cmd_eval = [ENGINE_EXE, "evaluate", "--run-dir", str(run_dir), "--step", str(step), "--top", str(top)]
            else:
                cmd_eval = ["cargo", "run", "--quiet", "--", "evaluate", "--run-dir", str(run_dir), "--step", str(step), "--top", str(top)]
            subprocess.run(cmd_eval)

        else:
            print(f"Unknown command '{cmd}'. Type 'help' for available commands.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FCR 2.1 Interactive REPL")
    parser.add_argument("--script", type=str, default=None, help="Execute REPL commands from script file")
    args = parser.parse_args()

    if args.script:
        with open(args.script) as f:
            lines = f.readlines()
        current_state = FcrReplState(3)
        for l in lines:
            l_str = l.strip()
            if not l_str or l_str.startswith("#"): continue
            print(f"fcr> {l_str}")
    else:
        run_repl()
