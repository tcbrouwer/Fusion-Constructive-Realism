use crate::reduction::EPSILON_CANCEL;
use crate::state::StateQ;
use num_complex::Complex64;
use serde::{Deserialize, Serialize};

pub const EPSILON_SEVER: f64 = 1e-6;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MutationType {
    Triangulation { i: usize, x: usize, j: usize },
    CorrelationDecay { i: usize, j: usize },
    AsymptoticMetricEvolution { i: usize, j: usize },
}

impl MutationType {
    pub fn short_code(&self) -> &'static str {
        match self {
            MutationType::Triangulation { .. } => "t",
            MutationType::CorrelationDecay { .. } => "d",
            MutationType::AsymptoticMetricEvolution { .. } => "m",
        }
    }

    pub fn variant_id(&self) -> u8 {
        match self {
            MutationType::Triangulation { .. } => 1,
            MutationType::CorrelationDecay { .. } => 2,
            MutationType::AsymptoticMetricEvolution { .. } => 3,
        }
    }

    pub fn canonical_id(&self) -> u64 {
        match self {
            MutationType::Triangulation { i, x, j } => {
                1_000_000 + (*i as u64) * 10000 + (*x as u64) * 100 + (*j as u64)
            }
            MutationType::CorrelationDecay { i, j } => {
                2_000_000 + (*i as u64) * 1000 + (*j as u64)
            }
            MutationType::AsymptoticMetricEvolution { i, j } => {
                3_000_000 + (*i as u64) * 1000 + (*j as u64)
            }
        }
    }

    pub fn canonical_index(&self) -> u64 {
        self.canonical_id()
    }

    pub fn is_disjoint(&self, other: &MutationType) -> bool {
        match (self, other) {
            (MutationType::Triangulation { i: i1, x: x1, j: j1 }, MutationType::Triangulation { i: i2, x: x2, j: j2 }) => {
                i1 != i2 && i1 != x2 && i1 != j2 &&
                x1 != i2 && x1 != x2 && x1 != j2 &&
                j1 != i2 && j1 != x2 && j1 != j2
            }
            (MutationType::Triangulation { i: i1, x: x1, j: j1 }, MutationType::CorrelationDecay { i: i2, j: j2 }) |
            (MutationType::Triangulation { i: i1, x: x1, j: j1 }, MutationType::AsymptoticMetricEvolution { i: i2, j: j2 }) => {
                i1 != i2 && i1 != j2 &&
                x1 != i2 && x1 != j2 &&
                j1 != i2 && j1 != j2
            }
            (MutationType::CorrelationDecay { i: i1, j: j1 }, MutationType::Triangulation { i: i2, x: x2, j: j2 }) |
            (MutationType::AsymptoticMetricEvolution { i: i1, j: j1 }, MutationType::Triangulation { i: i2, x: x2, j: j2 }) => {
                i1 != i2 && i1 != x2 && i1 != j2 &&
                j1 != i2 && j1 != x2 && j1 != j2
            }
            (MutationType::CorrelationDecay { i: i1, j: j1 }, MutationType::CorrelationDecay { i: i2, j: j2 }) |
            (MutationType::CorrelationDecay { i: i1, j: j1 }, MutationType::AsymptoticMetricEvolution { i: i2, j: j2 }) |
            (MutationType::AsymptoticMetricEvolution { i: i1, j: j1 }, MutationType::CorrelationDecay { i: i2, j: j2 }) |
            (MutationType::AsymptoticMetricEvolution { i: i1, j: j1 }, MutationType::AsymptoticMetricEvolution { i: i2, j: j2 }) => {
                i1 != i2 && i1 != j2 && j1 != i2 && j1 != j2
            }
        }
    }

    pub fn to_u64(&self) -> u64 {
        self.canonical_id()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MutationStep {
    pub mutation_type: MutationType,
    pub weight: f64,
}

pub struct PhysicalParameters {
    pub gamma: f64,   // Decay constant
    pub alpha: f64,   // Metric contraction coupling
    pub beta: f64,    // Spatial elasticity recovery
}

impl Default for PhysicalParameters {
    fn default() -> Self {
        Self {
            gamma: (2.0f64).ln(), // ln(2) ≈ 0.69314718
            alpha: 0.5,
            beta: 0.1,
        }
    }
}

/// Generate all valid single operational mutations for a state
pub fn find_valid_mutations(state: &StateQ, params: &PhysicalParameters) -> Vec<(MutationType, f64)> {
    let mut mutations = Vec::new();
    let n = state.n as usize;

    // 1. Triangulation (t): for each unordered triplet {p1, p2, p3} with p1 < p2 < p3
    for p1 in 0..n {
        for p2 in (p1 + 1)..n {
            for p3 in (p2 + 1)..n {
                let c_12 = state.get_c(p1, p2);
                let c_23 = state.get_c(p2, p3);
                let c_13 = state.get_c(p1, p3);

                // Option 1: Update edge (p1, p2) via intermediate p3
                if c_13.norm() > EPSILON_CANCEL && c_23.norm() > EPSILON_CANCEL {
                    let mu_12 = state.get_mu(p1, p2);
                    let c_new = c_12 + c_13 * c_23;
                    let s1_new = state.calculate_capacity(p1) - c_12.norm() + c_new.norm();
                    let s2_new = state.calculate_capacity(p2) - c_12.norm() + c_new.norm();
                    let capacity_excess = (s1_new - 1.0).max(0.0) + (s2_new - 1.0).max(0.0);
                    let mut weight = (-(mu_12 * mu_12)).exp();
                    if capacity_excess > 0.0 {
                        weight *= (-capacity_excess * capacity_excess).exp();
                    }
                    mutations.push((MutationType::Triangulation { i: p1, x: p3, j: p2 }, weight));
                }

                // Option 2: Update edge (p1, p3) via intermediate p2
                if c_12.norm() > EPSILON_CANCEL && c_23.norm() > EPSILON_CANCEL {
                    let mu_13 = state.get_mu(p1, p3);
                    let c_new = c_13 + c_12 * c_23;
                    let s1_new = state.calculate_capacity(p1) - c_13.norm() + c_new.norm();
                    let s3_new = state.calculate_capacity(p3) - c_13.norm() + c_new.norm();
                    let capacity_excess = (s1_new - 1.0).max(0.0) + (s3_new - 1.0).max(0.0);
                    let mut weight = (-(mu_13 * mu_13)).exp();
                    if capacity_excess > 0.0 {
                        weight *= (-capacity_excess * capacity_excess).exp();
                    }
                    mutations.push((MutationType::Triangulation { i: p1, x: p2, j: p3 }, weight));
                }

                // Option 3: Update edge (p2, p3) via intermediate p1
                if c_12.norm() > EPSILON_CANCEL && c_13.norm() > EPSILON_CANCEL {
                    let mu_23 = state.get_mu(p2, p3);
                    let c_new = c_23 + c_12 * c_13;
                    let s2_new = state.calculate_capacity(p2) - c_23.norm() + c_new.norm();
                    let s3_new = state.calculate_capacity(p3) - c_23.norm() + c_new.norm();
                    let capacity_excess = (s2_new - 1.0).max(0.0) + (s3_new - 1.0).max(0.0);
                    let mut weight = (-(mu_23 * mu_23)).exp();
                    if capacity_excess > 0.0 {
                        weight *= (-capacity_excess * capacity_excess).exp();
                    }
                    mutations.push((MutationType::Triangulation { i: p2, x: p1, j: p3 }, weight));
                }
            }
        }
    }

    // 2. Correlation Decay (d): active edges (i,j) with i < j
    for i in 0..n {
        for j in (i + 1)..n {
            let c_ij = state.get_c(i, j);
            if c_ij.norm() > EPSILON_CANCEL {
                let mu_ij = state.get_mu(i, j);
                let decayed_c = c_ij * (-params.gamma * mu_ij).exp();
                let norm_decayed = if decayed_c.norm() < EPSILON_SEVER { 0.0 } else { decayed_c.norm() };
                let s1_new = state.calculate_capacity(i) - c_ij.norm() + norm_decayed;
                let s2_new = state.calculate_capacity(j) - c_ij.norm() + norm_decayed;
                let capacity_excess = (s1_new - 1.0).max(0.0) + (s2_new - 1.0).max(0.0);
                let mut weight = (-params.gamma * mu_ij).exp();
                if capacity_excess > 0.0 {
                    weight *= (-capacity_excess * capacity_excess).exp();
                }
                mutations.push((MutationType::CorrelationDecay { i, j }, weight));
            }
        }
    }

    // 3. Asymptotic Metric Evolution (mu): active edges or connected pairs (i,j) with i < j
    for i in 0..n {
        for j in (i + 1)..n {
            let c_ij = state.get_c(i, j);
            if c_ij.norm() > EPSILON_CANCEL {
                let mu_old = state.get_mu(i, j);
                let mag_c = c_ij.norm();
                let c_excess = mag_c - 0.5; // Difference from M6 ground-state capacity
                let mu_new = mu_old * (-params.alpha * c_excess).exp() + params.beta * (1.0 - mu_old);
                let s_i = state.calculate_capacity(i);
                let s_j = state.calculate_capacity(j);
                let capacity_excess = (s_i - 1.0).max(0.0) + (s_j - 1.0).max(0.0);
                let mut weight = calculate_metric_transition_weight(mu_old, mu_new);
                if capacity_excess > 0.0 {
                    weight *= (-capacity_excess * capacity_excess).exp();
                }
                mutations.push((MutationType::AsymptoticMetricEvolution { i, j }, weight));
            }
        }
    }

    mutations
}

pub fn calculate_metric_transition_weight(mu_old: f64, mu_new: f64) -> f64 {
    if mu_old <= 0.0 {
        return 1.0;
    }

    let strain = (mu_new - mu_old).abs() / mu_old;
    (-strain).exp()
}

/// Apply a chosen mutation to a state, returning the updated state and mutation step metadata
pub fn apply_mutation(
    state: &StateQ,
    mutation: &MutationType,
    params: &PhysicalParameters,
) -> (StateQ, MutationStep) {
    let mut new_state = state.clone();

    match mutation {
        MutationType::Triangulation { i, x, j } => {
            let c_old = state.get_c(*i, *j);
            let c_ix = state.get_c(*i, *x);
            let c_xj = state.get_c(*x, *j);
            let c_new = c_old + c_ix * c_xj;
            new_state.set_c(*i, *j, c_new);

            let mu_ij = state.get_mu(*i, *j);
            let mut weight = (-(mu_ij * mu_ij)).exp();

            // Calculate post-mutation capacity excess across all affected nodes
            let s_i = new_state.calculate_capacity(*i);
            let s_j = new_state.calculate_capacity(*j);
            let capacity_excess = (s_i - 1.0).max(0.0) + (s_j - 1.0).max(0.0);

            if capacity_excess > 0.0 {
                // Soft Gaussian action penalty for virtual over-capacity states
                weight *= (-capacity_excess * capacity_excess).exp();
            }

            new_state.last_mutation_type = mutation.to_u64();

            (
                new_state,
                MutationStep {
                    mutation_type: mutation.clone(),
                    weight,
                },
            )
        }
        MutationType::CorrelationDecay { i, j } => {
            let mu_ij = state.get_mu(*i, *j);
            let c_ij = state.get_c(*i, *j);
            let decayed_c = c_ij * (-params.gamma * mu_ij).exp();

            if decayed_c.norm() < EPSILON_SEVER {
                new_state.set_c(*i, *j, Complex64::new(0.0, 0.0));
            } else {
                new_state.set_c(*i, *j, decayed_c);
            }

            let mut weight = (-params.gamma * mu_ij).exp();

            // Calculate post-mutation capacity excess across all affected nodes
            let s_i = new_state.calculate_capacity(*i);
            let s_j = new_state.calculate_capacity(*j);
            let capacity_excess = (s_i - 1.0).max(0.0) + (s_j - 1.0).max(0.0);

            if capacity_excess > 0.0 {
                // Soft Gaussian action penalty for virtual over-capacity states
                weight *= (-capacity_excess * capacity_excess).exp();
            }

            new_state.last_mutation_type = mutation.to_u64();

            (
                new_state,
                MutationStep {
                    mutation_type: mutation.clone(),
                    weight,
                },
            )
        }
        MutationType::AsymptoticMetricEvolution { i, j } => {
            let mu_old = state.get_mu(*i, *j);
            let c_ij = state.get_c(*i, *j);
            let mag_c = c_ij.norm();

            let c_excess = mag_c - 0.5; // Difference from M6 ground-state capacity
            let mu_new = mu_old * (-params.alpha * c_excess).exp() + params.beta * (1.0 - mu_old);
            new_state.set_mu(*i, *j, mu_new);

            let mut weight = calculate_metric_transition_weight(mu_old, mu_new);

            // Calculate post-mutation capacity excess across all affected nodes
            let s_i = new_state.calculate_capacity(*i);
            let s_j = new_state.calculate_capacity(*j);
            let capacity_excess = (s_i - 1.0).max(0.0) + (s_j - 1.0).max(0.0);

            if capacity_excess > 0.0 {
                // Soft Gaussian action penalty for virtual over-capacity states
                weight *= (-capacity_excess * capacity_excess).exp();
            }

            new_state.last_mutation_type = mutation.to_u64();

            (
                new_state,
                MutationStep {
                    mutation_type: mutation.clone(),
                    weight,
                },
            )
        }
    }
}
