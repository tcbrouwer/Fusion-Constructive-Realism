use crate::state::StateQ;
use num_complex::Complex64;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub const EPSILON_BIN: f64 = 1e-2;
pub const EPSILON_CANCEL: f64 = 1e-2;

/// Calculate global 3-cycle loop trace phase:
/// \Phi_{global} = arg(Tr(C^3)) = arg( \sum_{i,j,k} C(i,j) C(j,k) C(k,i) )
pub fn calculate_global_loop_phase(state: &StateQ) -> f64 {
    let n = state.n as usize;
    let mut tr_c3 = Complex64::new(0.0, 0.0);

    for i in 0..n {
        for j in 0..n {
            let c_ij = state.get_c(i, j);
            if c_ij.norm() < EPSILON_CANCEL {
                continue;
            }
            for k in 0..n {
                let c_jk = state.get_c(j, k);
                let c_ki = state.get_c(k, i);
                tr_c3 += c_ij * c_jk * c_ki;
            }
        }
    }

    if tr_c3.norm() < EPSILON_CANCEL {
        0.0
    } else {
        tr_c3.arg()
    }
}

/// Apply global loop phase gauge-fixing: C_gauge(a,b) = C(a,b) * e^{-i \Phi_{global}} (for a != b)
pub fn gauge_fix_state(state: &StateQ) -> StateQ {
    let phi_global = calculate_global_loop_phase(state);
    let shift = Complex64::from_polar(1.0, -phi_global);
    let mut gauge_fixed = state.clone();

    let n = state.n as usize;
    for i in 0..n {
        for j in 0..n {
            if i != j {
                let c_val = state.get_c(i, j);
                gauge_fixed.set_c(i, j, c_val * shift);
            }
        }
    }

    gauge_fixed
}

/// Helper function to bin a float to precision \epsilon_{bin}
#[inline]
pub fn bin_float(val: f64, precision: f64) -> i64 {
    (val / precision).round() as i64
}

/// Weisfeiler-Lehman (WL) Canonical Graph Hash algorithm for state deduplication
pub fn compute_wl_hash(state: &StateQ) -> String {
    let gauge_fixed = gauge_fix_state(state);
    let n = state.n as usize;

    if n == 0 {
        return format!("{:x}", Sha256::digest(b"empty"));
    }

    // 1. Initial Node Colors based on local node degree and binned capacity
    let mut node_colors: Vec<String> = (0..n)
        .map(|i| {
            let cap = bin_float(state.calculate_capacity(i), EPSILON_BIN);
            format!("c_{}", cap)
        })
        .collect();

    // 2. Perform 3 WL Refinement Rounds
    for _round in 0..3 {
        let mut next_colors = Vec::with_capacity(n);

        for i in 0..n {
            let mut neighbor_signatures = Vec::with_capacity(n);
            for j in 0..n {
                if i == j {
                    continue;
                }
                let mu_binned = bin_float(gauge_fixed.get_mu(i, j), EPSILON_BIN);
                let c_val = gauge_fixed.get_c(i, j);
                let mag_binned = bin_float(c_val.norm(), EPSILON_BIN);
                let phase_binned = bin_float(c_val.arg(), EPSILON_BIN);

                // Combine neighbor color and binned edge attributes
                let edge_sig = format!(
                    "({},mu:{},mag:{},ph:{})",
                    node_colors[j], mu_binned, mag_binned, phase_binned
                );
                neighbor_signatures.push(edge_sig);
            }

            // Deterministic sort of neighbor signatures
            neighbor_signatures.sort();

            let combined = format!("{}:[{}]", node_colors[i], neighbor_signatures.join(","));
            let node_hash = format!("{:x}", Sha256::digest(combined.as_bytes()));
            next_colors.push(node_hash);
        }

        node_colors = next_colors;
    }

    // 3. Count frequencies of node color hashes to create a canonical graph signature
    let mut color_counts: BTreeMap<String, usize> = BTreeMap::new();
    for color in node_colors {
        *color_counts.entry(color).or_insert(0) += 1;
    }

    let mut canonical_repr = String::new();
    for (color, count) in color_counts {
        canonical_repr.push_str(&format!("{}:{};", color, count));
    }

    format!("{:x}", Sha256::digest(canonical_repr.as_bytes()))
}

/// Struct representing a canonical state class [Q]
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct CanonicalState {
    pub wl_hash: String,
    pub state: StateQ,
}

impl CanonicalState {
    pub fn from_state(state: &StateQ) -> Self {
        let hash = compute_wl_hash(state);
        Self {
            wl_hash: hash,
            state: state.clone(),
        }
    }
}
