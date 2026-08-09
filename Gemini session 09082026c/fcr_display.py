#!/usr/bin/env python3
"""
FCR 2.1 State-Space Display & Visualization Tool
"""

import os
import sys
import json
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

fn_engine_exe = get_engine_exe()

def run_engine_command(args_list):
    if fn_engine_exe:
        cmd = [fn_engine_exe] + args_list
    else:
        cmd = ["cargo", "run", "--quiet", "--"] + args_list
    return subprocess.run(cmd, capture_output=True, text=True)

def plot_state_graph(json_data, output_path=None):
    if not HAS_PLOT_LIBS:
        print("Error: matplotlib and networkx are required for plotting.", file=sys.stderr)
        return

    n = json_data["n"]
    state = json_data["state"]
    wl_hash = json_data["wl_hash"]
    path_count = json_data["path_count"]
    acc_wt = json_data["accumulated_weight_a"]

    G = nx.Graph()

    # Add nodes
    for p in range(n):
        # Calculate S(p)
        s_p = 0.0
        for q in range(n):
            if p != q:
                c_val = state["c"][p * n + q]
                if isinstance(c_val, (list, tuple)):
                    re, im = c_val[0], c_val[1]
                elif isinstance(c_val, dict):
                    re, im = c_val.get("re", 0.0), c_val.get("im", 0.0)
                else:
                    re, im = 0.0, 0.0
                s_p += (re**2 + im**2)
        G.add_node(p, label=f"Node {p}\nS(p)={s_p:.3f}")

    # Add active edges
    edge_labels = {}
    edge_weights = []

    for i in range(n):
        for j in range(i + 1, n):
            c_val = state["c"][i * n + j]
            if isinstance(c_val, (list, tuple)):
                re, im = c_val[0], c_val[1]
            elif isinstance(c_val, dict):
                re, im = c_val.get("re", 0.0), c_val.get("im", 0.0)
            else:
                re, im = 0.0, 0.0
            mag = np.hypot(re, im)
            phase_deg = np.degrees(np.arctan2(im, re))
            mu_val = state["mu"][i * n + j]

            if mag > 1e-6:
                G.add_edge(i, j, weight=mag)
                edge_labels[(i, j)] = f"|C|={mag:.2f}\nμ={mu_val:.2f}\nθ={phase_deg:.1f}°"
                edge_weights.append(mag * 3.5 + 1.0)

    fig, ax = plt.subplots(figsize=(8, 6))
    pos = nx.spring_layout(G, seed=42)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=1200, node_color="#2b5c8f", alpha=0.9, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, "label"), font_color="white", font_size=9, font_weight="bold", ax=ax)

    # Draw edges
    if G.number_of_edges() > 0:
        nx.draw_networkx_edges(G, pos, width=edge_weights, edge_color="#3a9254", alpha=0.75, ax=ax)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)

    ax.set_title(f"FCR 2.1 State Graph | WL Hash: {wl_hash[:16]}...\nPath Count: {path_count} | Weight A: {acc_wt:.4e}", fontsize=11, fontweight="bold", pad=12)
    ax.axis("off")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300)
        print(f"Saved state plot visualization to: {output_path}")
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="FCR 2.1 State-Space Display & Visualization Tool")
    parser.add_argument("--file", "-f", type=str, default=None, help="Path to a specific .fcrstate file to inspect")
    parser.add_argument("--run-id", type=str, default="demo_run", help="ID of trajectory run")
    parser.add_argument("--time-step", type=int, default=3, help="Poset time step T_k to evaluate")
    parser.add_argument("--storage-root", type=str, default="./output", help="Root directory storing run data")
    parser.add_argument("--top", type=int, default=10, help="Number of top states to display (0 for all)")
    parser.add_argument("--plot", action="store_true", help="Display graph visualization plot for state")
    parser.add_argument("--save-plot", type=str, default=None, help="Save graph visualization plot to PNG file")

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        # Terminal inspection
        res = run_engine_command(["inspect", "--file", str(file_path)])
        print(res.stdout)

        if args.plot or args.save_plot:
            res_json = run_engine_command(["inspect", "--file", str(file_path), "--json"])
            try:
                json_data = json.loads(res_json.stdout)
                plot_state_graph(json_data, output_path=args.save_plot)
            except Exception as e:
                print(f"Error parsing state JSON for plotting: {e}", file=sys.stderr)

    else:
        run_dir = Path(args.storage_root) / f"run_{args.run_id}"
        if not run_dir.exists():
            print(f"Error: Run directory '{run_dir}' does not exist.", file=sys.stderr)
            sys.exit(1)

        res = run_engine_command(["evaluate", "--run-dir", str(run_dir), "--step", str(args.time_step), "--top", str(args.top)])
        print(res.stdout)

if __name__ == "__main__":
    main()
