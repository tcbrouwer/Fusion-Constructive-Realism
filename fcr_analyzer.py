#!/usr/bin/env python3
r"""
Offline Born-Rule Probability Analyzer for Fusion Constructive Realism (FCR)
Implements Section 6 of ANTIGRAVITY_MASTER_SPEC.md:
- Scans fcr_repository/M<n>/T_<k>/ for all state files at poset step T_k.
- Reconstructs convergent path trajectories \gamma from state incoming_paths.
- Evaluates total phase product Z(\gamma) = \prod_{e \in \gamma} z_e across all paths leading to state Q.
- Computes Born-rule display probability distribution P(Q):
  P(Q) = |\sum_{\gamma \to Q} Z(\gamma)|^2 / \sum_{Q'} |\sum_{\gamma' \to Q'} Z(\gamma')|^2
- Outputs formatted probability table and exports summary JSON report.
"""

import os
import sys
import argparse
import json
import yaml

REPOS_DIR = "fcr_repository"

def scan_states_at_step(level: int, poset_step: int) -> list:
    """Scans repository directory for all state files at level M<n> and poset step T_<k>."""
    step_dir = os.path.join(REPOS_DIR, f"M{level}", f"T_{poset_step}")
    if not os.path.exists(step_dir):
        return []

    states = []
    for fname in os.listdir(step_dir):
        if fname.endswith(".yaml") and fname.startswith("state_"):
            fpath = os.path.join(step_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                states.append((fpath, data))
            except Exception as e:
                print(f"Warning: Failed to load {fpath}: {e}")
    return states

def calculate_born_probabilities(states: list) -> dict:
    """
    Computes Born-rule probability distribution P(Q) across all states Q at timestep T_k.
    """
    state_amplitudes = {}
    total_unnorm_prob = 0.0

    for fpath, data in states:
        metadata = data.get("metadata", {})
        hash_id = metadata.get("canonical_hash", "unknown")
        incoming = data.get("incoming_paths", [])

        # Sum phase amplitudes Z(\gamma) across all incoming trajectories leading to state Q
        net_amplitude = 0.0 + 0.0j
        for path_entry in incoming:
            phase_dict = path_entry.get("transition_phase", {})
            re = float(phase_dict.get("real", 1.0))
            im = float(phase_dict.get("imag", 0.0))
            net_amplitude += complex(re, im)

        # If no explicit incoming path recorded, default to baseline identity amplitude
        if not incoming:
            net_amplitude = 1.0 + 0.0j

        unnorm_prob = abs(net_amplitude) ** 2
        state_amplitudes[hash_id] = {
            "file_path": fpath,
            "net_amplitude": {"real": net_amplitude.real, "imag": net_amplitude.imag},
            "unnorm_prob": unnorm_prob,
            "visit_count": metadata.get("visit_count", 1),
            "max_capacity_sum": data.get("capacity_audit", {}).get("max_node_sum", 0.0),
        }
        total_unnorm_prob += unnorm_prob

    # Normalize probabilities
    results = {}
    for hash_id, info in state_amplitudes.items():
        prob = info["unnorm_prob"] / total_unnorm_prob if total_unnorm_prob > 1e-15 else 1.0 / len(states)
        info["probability"] = round(prob, 6)
        results[hash_id] = info

    return results

def analyze(level: int, poset_step: int) -> dict:
    """Main analysis function for level M<n> and poset step T_<k>."""
    states = scan_states_at_step(level, poset_step)
    if not states:
        print(f"No state records found in {REPOS_DIR}/M{level}/T_{poset_step}/")
        return {}

    probs = calculate_born_probabilities(states)

    print("=" * 70)
    print(f"  FCR BORN-RULE DISPLAY PROBABILITY DISTRIBUTION (M{level} | Step T = {poset_step})")
    print("=" * 70)
    print(f"{'State Hash':<15} | {'Probability P(Q)':<18} | {'Net Amplitude (Re, Im)':<24} | {'Visits'}")
    print("-" * 70)

    sorted_probs = sorted(probs.items(), key=lambda x: x[1]["probability"], reverse=True)
    for hash_id, info in sorted_probs:
        amp = info["net_amplitude"]
        amp_str = f"({amp['real']:.4f}, {amp['imag']:.4f}i)"
        print(f"{hash_id:<15} | {info['probability']:<18.6f} | {amp_str:<24} | {info['visit_count']}")

    print("-" * 70)

    # Export report JSON
    report_file = os.path.join(REPOS_DIR, f"probability_report_M{level}_T{poset_step}.json")
    os.makedirs(REPOS_DIR, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(probs, f, indent=2)

    print(f"Exported Born-rule probability report: {report_file}\n")
    return probs

def main():
    parser = argparse.ArgumentParser(description="FCR Offline Born-Rule Probability Analyzer")
    parser.add_argument("--level", "-l", type=int, default=3, help="Poset level M<n> (default: 3)")
    parser.add_argument("--step", "-s", type=int, default=1, help="Poset step T_<k> (default: 1)")
    args = parser.parse_args()

    analyze(level=args.level, poset_step=args.step)

if __name__ == "__main__":
    main()
