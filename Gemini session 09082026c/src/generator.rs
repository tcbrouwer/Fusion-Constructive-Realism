use crate::mutations::{apply_mutation, find_valid_mutations, PhysicalParameters};
use crate::reduction::compute_wl_hash;
use crate::state::StateQ;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

/// Binary file record saved as `.fcrstate`
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FcrStateRecord {
    pub n: u32,
    pub path_count: u64,
    pub accumulated_weight_a: f64,
    pub wl_hash: String,
    pub state: StateQ,
    pub parent_hashes: Vec<String>,
    pub transition_weights: Vec<f64>,
    #[serde(default)]
    pub mutation_sequences: HashMap<String, u64>,
    #[serde(default)]
    pub last_mutation: Option<crate::mutations::MutationType>,
    #[serde(default)]
    pub block_variant: u8,
    #[serde(default)]
    pub block_length: u32,
    #[serde(default)]
    pub block_multiplicities: HashMap<u64, u32>,
}

impl FcrStateRecord {
    pub fn top_mutation_sequence(&self) -> String {
        if self.mutation_sequences.is_empty() {
            return "-".to_string();
        }
        self.mutation_sequences
            .iter()
            .max_by(|a, b| {
                a.1.cmp(b.1).then_with(|| b.0.cmp(a.0))
            })
            .map(|(seq, _count)| if seq.is_empty() { "-".to_string() } else { seq.clone() })
            .unwrap_or_else(|| "-".to_string())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrajectoryMetadata {
    pub run_id: String,
    pub total_poset_steps: usize,
    pub total_states_generated: usize,
    pub top_states_limit: usize,
    pub created_at: String,
}

pub struct StateSpaceGenerator {
    pub storage_root: PathBuf,
    pub params: PhysicalParameters,
    pub top_states_limit: usize, // Default 100 (0 means unlimited)
}

impl StateSpaceGenerator {
    pub fn new<P: AsRef<Path>>(
        storage_root: P,
        params: PhysicalParameters,
        top_states_limit: usize,
    ) -> Self {
        Self {
            storage_root: storage_root.as_ref().to_path_buf(),
            params,
            top_states_limit,
        }
    }

    /// Run full macro-trajectory tree generation from Q0 across max_poset_steps
    pub fn generate_trajectories(
        &self,
        run_id: &str,
        initial_state: StateQ,
        max_poset_steps: usize,
    ) -> Result<TrajectoryMetadata, String> {
        let run_dir = self.storage_root.join(format!("run_{}", run_id));
        fs::create_dir_all(&run_dir).map_err(|e| e.to_string())?;

        let mut current_level_states: HashMap<String, FcrStateRecord> = HashMap::new();
        let initial_hash = compute_wl_hash(&initial_state);

        let mut initial_seqs = HashMap::new();
        initial_seqs.insert(String::new(), 1);

        let initial_record = FcrStateRecord {
            n: initial_state.n,
            path_count: 1,
            accumulated_weight_a: 1.0,
            wl_hash: initial_hash.clone(),
            state: initial_state.clone(),
            parent_hashes: Vec::new(),
            transition_weights: Vec::new(),
            mutation_sequences: initial_seqs,
            last_mutation: None,
            block_variant: 0,
            block_length: 0,
            block_multiplicities: HashMap::new(),
        };

        current_level_states.insert(initial_hash.clone(), initial_record.clone());

        // Save step T000
        let t0_dir = run_dir.join("T000");
        fs::create_dir_all(&t0_dir).map_err(|e| e.to_string())?;
        self.save_record(&t0_dir.join(format!("{}.fcrstate", initial_hash)), &initial_record)?;

        let mut total_generated = 1;

        for step in 1..=max_poset_steps {
            let step_dir_name = format!("T{:03}", step);
            let step_dir = run_dir.join(&step_dir_name);
            fs::create_dir_all(&step_dir).map_err(|e| e.to_string())?;

            // Parallel mutation generation using Rayon
            let current_records: Vec<FcrStateRecord> = current_level_states.values().cloned().collect();
            let next_branches: Vec<Vec<(StateQ, f64, String, HashMap<String, u64>, Option<crate::mutations::MutationType>, u8, u32, HashMap<u64, u32>)>> = current_records
                .par_iter()
                .map(|record| {
                    let mut branches = Vec::new();
                    let valid_muts = find_valid_mutations(&record.state, &self.params);

                    for (mut_type, base_weight) in valid_muts {
                        let variant = mut_type.variant_id();
                        let can_idx = mut_type.canonical_id();

                        let is_disjoint_commuting = if let Some(ref prev_mut) = record.last_mutation {
                            mut_type.is_disjoint(prev_mut)
                        } else {
                            false
                        };

                        // Enforce increasing canonical index order for commuting operations on disjoint node sets
                        if is_disjoint_commuting {
                            if let Some(ref prev_mut) = record.last_mutation {
                                if can_idx < prev_mut.canonical_id() {
                                    // Skip non-canonical permutation of commuting operations
                                    continue;
                                }
                            }
                        }

                        // Compute block tracking & combinatorial symmetry factor (k! / prod n_i!)
                        let (new_block_len, new_mults, symmetry_mult) = if is_disjoint_commuting || record.block_variant == variant {
                            let new_len = record.block_length + 1;
                            let mut mults = record.block_multiplicities.clone();
                            let count = mults.entry(can_idx).or_insert(0);
                            *count += 1;
                            let mult = new_len as f64 / (*count as f64);
                            (new_len, mults, mult)
                        } else {
                            let mut mults = HashMap::new();
                            mults.insert(can_idx, 1);
                            (1, mults, 1.0)
                        };

                        let effective_weight = base_weight * symmetry_mult;
                        let (next_state, _step_meta) = apply_mutation(&record.state, &mut_type, &self.params);
                        let mut_code = mut_type.short_code();
                        let mut next_seqs = HashMap::new();
                        for (seq, count) in &record.mutation_sequences {
                            let mut new_seq = seq.clone();
                            new_seq.push_str(mut_code);
                            *next_seqs.entry(new_seq).or_insert(0) += count;
                        }
                        branches.push((
                            next_state,
                            effective_weight,
                            record.wl_hash.clone(),
                            next_seqs,
                            Some(mut_type),
                            variant,
                            new_block_len,
                            new_mults,
                        ));
                    }
                    branches
                })
                .collect();

            let mut next_level_states: HashMap<String, FcrStateRecord> = HashMap::new();

            for branch_set in next_branches {
                for (next_state, weight, parent_hash, branch_seqs, last_mut, b_variant, b_len, b_mults) in branch_set {
                    let next_hash = compute_wl_hash(&next_state);
                    let branch_path_count: u64 = branch_seqs.values().sum();

                    next_level_states
                        .entry(next_hash.clone())
                        .and_modify(|rec| {
                            rec.path_count += branch_path_count;
                            rec.accumulated_weight_a += weight;
                            if !rec.parent_hashes.contains(&parent_hash) {
                                rec.parent_hashes.push(parent_hash.clone());
                                rec.transition_weights.push(weight);
                            }
                            for (seq, count) in &branch_seqs {
                                *rec.mutation_sequences.entry(seq.clone()).or_insert(0) += count;
                            }
                        })
                        .or_insert_with(|| {
                            total_generated += 1;
                            FcrStateRecord {
                                n: next_state.n,
                                path_count: branch_path_count,
                                accumulated_weight_a: weight,
                                wl_hash: next_hash.clone(),
                                state: next_state,
                                parent_hashes: vec![parent_hash],
                                transition_weights: vec![weight],
                                mutation_sequences: branch_seqs,
                                last_mutation: last_mut,
                                block_variant: b_variant,
                                block_length: b_len,
                                block_multiplicities: b_mults,
                            }
                        });
                }
            }

            // Prune to top_states_limit if top_states_limit > 0
            if self.top_states_limit > 0 && next_level_states.len() > self.top_states_limit {
                let mut records_vec: Vec<FcrStateRecord> = next_level_states.into_values().collect();
                records_vec.sort_by(|a, b| {
                    b.accumulated_weight_a
                        .partial_cmp(&a.accumulated_weight_a)
                        .unwrap_or(std::cmp::Ordering::Equal)
                });
                records_vec.truncate(self.top_states_limit);

                next_level_states = records_vec
                    .into_iter()
                    .map(|r| (r.wl_hash.clone(), r))
                    .collect();
            }

            // Save records for step T_k (only top_states_limit states saved)
            for (hash, record) in &next_level_states {
                self.save_record(&step_dir.join(format!("{}.fcrstate", hash)), record)?;
            }

            if next_level_states.is_empty() {
                break;
            }

            current_level_states = next_level_states;
        }

        let metadata = TrajectoryMetadata {
            run_id: run_id.to_string(),
            total_poset_steps: max_poset_steps,
            total_states_generated: total_generated,
            top_states_limit: self.top_states_limit,
            created_at: "2026-08-09".to_string(),
        };

        let meta_file = run_dir.join("metadata.json");
        let meta_json = serde_json::to_string_pretty(&metadata).map_err(|e| e.to_string())?;
        fs::write(meta_file, meta_json).map_err(|e| e.to_string())?;

        Ok(metadata)
    }

    fn save_record(&self, path: &Path, record: &FcrStateRecord) -> Result<(), String> {
        let encoded = bincode::serialize(record).map_err(|e| e.to_string())?;
        fs::write(path, encoded).map_err(|e| e.to_string())?;
        Ok(())
    }
}
