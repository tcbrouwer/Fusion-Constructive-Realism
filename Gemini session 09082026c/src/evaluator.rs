use crate::generator::FcrStateRecord;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplayStateResult {
    pub rank: usize,
    pub wl_hash: String,
    pub path_count: u64,
    pub active_edge_count: usize,
    pub avg_edge_weight_modulus: f64,
    pub top_mutation_sequence: String,
    pub accumulated_weight_a: f64,
    pub display_probability_p: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepEvaluationSummary {
    pub time_step: usize,
    pub total_macro_states: usize,
    pub total_trajectory_paths: u64,
    pub display_states: Vec<DisplayStateResult>,
}

pub fn evaluate_time_step<P: AsRef<Path>>(
    run_dir: P,
    time_step: usize,
) -> Result<StepEvaluationSummary, String> {
    let step_dir = run_dir.as_ref().join(format!("T{:03}", time_step));
    if !step_dir.exists() {
        return Err(format!("Directory {:?} does not exist", step_dir));
    }

    let entries = fs::read_dir(&step_dir).map_err(|e| e.to_string())?;
    let mut records: Vec<FcrStateRecord> = Vec::new();

    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) == Some("fcrstate") {
            let data = fs::read(&path).map_err(|e| e.to_string())?;
            let record: FcrStateRecord = bincode::deserialize(&data).map_err(|e| e.to_string())?;
            records.push(record);
        }
    }

    if records.is_empty() {
        return Err(format!("No .fcrstate files found in {:?}", step_dir));
    }

    // Calculate sum of squared amplitudes across all state equivalence classes in V_M(T_k)
    let denominator: f64 = records
        .iter()
        .map(|r| r.accumulated_weight_a * r.accumulated_weight_a)
        .sum();

    let mut display_states: Vec<DisplayStateResult> = records
        .iter()
        .map(|r| {
            let num = r.accumulated_weight_a * r.accumulated_weight_a;
            let prob = if denominator > 0.0 { num / denominator } else { 0.0 };

            // Calculate active edge count and average edge weight modulus |C(i,j)|
            let n = r.state.n as usize;
            let mut active_edges = 0;
            let mut sum_modulus = 0.0;
            for i in 0..n {
                for j in (i + 1)..n {
                    let mag = r.state.get_c(i, j).norm();
                    if mag > 1e-6 {
                        active_edges += 1;
                        sum_modulus += mag;
                    }
                }
            }
            let avg_modulus = if active_edges > 0 {
                sum_modulus / active_edges as f64
            } else {
                0.0
            };

            DisplayStateResult {
                rank: 0,
                wl_hash: r.wl_hash.clone(),
                path_count: r.path_count,
                active_edge_count: active_edges,
                avg_edge_weight_modulus: avg_modulus,
                top_mutation_sequence: r.top_mutation_sequence(),
                accumulated_weight_a: r.accumulated_weight_a,
                display_probability_p: prob,
            }
        })
        .collect();

    // Sort descending by display probability
    display_states.sort_by(|a, b| b.display_probability_p.partial_cmp(&a.display_probability_p).unwrap());

    for (idx, state) in display_states.iter_mut().enumerate() {
        state.rank = idx + 1;
    }

    let total_paths: u64 = records.iter().map(|r| r.path_count).sum();

    Ok(StepEvaluationSummary {
        time_step,
        total_macro_states: records.len(),
        total_trajectory_paths: total_paths,
        display_states,
    })
}
