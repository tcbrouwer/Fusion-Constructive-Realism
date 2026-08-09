use fcr_core::*;
use num_complex::Complex64;

#[test]
fn test_state_q_axioms() {
    let mut state = StateQ::new(3);
    assert_eq!(state.validate_axioms(), Ok(()));

    state.set_c(0, 1, Complex64::new(0.5, 0.5));
    assert_eq!(state.get_c(1, 0), Complex64::new(0.5, -0.5));
    assert_eq!(state.validate_axioms(), Ok(()));
}



#[test]
fn test_global_loop_phase_and_wl_hashing() {
    let mut state1 = StateQ::new(3);
    state1.set_c(0, 1, Complex64::new(0.5, 0.2));
    state1.set_c(1, 2, Complex64::new(0.4, 0.3));
    state1.set_c(2, 0, Complex64::new(0.6, -0.1));

    let hash1 = compute_wl_hash(&state1);
    assert!(!hash1.is_empty());

    // Permute nodes 0 and 1 -> state2
    let mut state2 = StateQ::new(3);
    state2.set_c(1, 0, Complex64::new(0.5, 0.2));
    state2.set_c(0, 2, Complex64::new(0.4, 0.3));
    state2.set_c(2, 1, Complex64::new(0.6, -0.1));

    let hash2 = compute_wl_hash(&state2);
    // Canonical WL hash must be permutation invariant
    assert_eq!(hash1, hash2, "WL Hash must be permutation invariant!");
}

#[test]
fn test_asymptotic_metric_evolution_positivity() {
    let mut state = StateQ::new(2);
    state.set_mu(0, 1, 0.1);
    state.set_c(0, 1, Complex64::new(0.9, 0.0));

    let params = PhysicalParameters::default();
    let (next_state, _) = apply_mutation(
        &state,
        &MutationType::AsymptoticMetricEvolution { i: 0, j: 1 },
        &params,
    );

    let new_mu = next_state.get_mu(0, 1);
    assert!(new_mu > 0.0, "Metric positivity must strictly hold!");
}

#[test]
fn test_trajectory_generator_and_evaluator() {
    let temp_dir = std::env::temp_dir().join("fcr_test_gen");
    let _ = std::fs::remove_dir_all(&temp_dir);
    let mut q0 = StateQ::new(3);
    q0.set_c(0, 1, Complex64::new(0.7, 0.1));
    q0.set_c(1, 2, Complex64::new(0.6, 0.2));

    let params = PhysicalParameters::default();
    let generator = StateSpaceGenerator::new(&temp_dir, params, 100);
    let meta = generator.generate_trajectories("test_run", q0, 2).unwrap();

    assert!(meta.total_states_generated > 0);

    let run_dir = temp_dir.join("run_test_run");
    let summary = evaluate_time_step(run_dir, 2).unwrap();
    assert!(!summary.display_states.is_empty());
    
    // Sum of display probabilities must be 1.0
    let prob_sum: f64 = summary.display_states.iter().map(|s| s.display_probability_p).sum();
    assert!((prob_sum - 1.0).abs() < 1e-6);
}

#[test]
fn test_sub_universe_fusion() {
    let mut qa = StateQ::new(2);
    qa.set_c(0, 1, Complex64::new(0.8, 0.0));

    let mut qb = StateQ::new(2);
    qb.set_c(0, 1, Complex64::new(0.7, 0.0));

    let bridges = vec![BridgeEdge {
        node_a: 1,
        node_b: 0,
        initial_correlation_mag: 0.5,
        phase_offset: 0.0,
    }];

    let fused = fuse_sub_universes(&qa, &qb, &bridges).unwrap();
    assert_eq!(fused.n, 4);
    assert_eq!(fused.get_c(1, 2), Complex64::new(0.5, 0.0));
}

#[test]
fn test_quantum_computer_bell_state() {
    let temp_dir = std::env::temp_dir().join("fcr_test_qc");
    let _ = std::fs::remove_dir_all(&temp_dir);
    let mut qc = FcrQuantumComputer::new_2qubit_register();
    let summary = qc.execute_bell_state_simulation(&temp_dir, "qc_test", 1).unwrap();
    assert!(!summary.display_states.is_empty());
}

#[test]
fn test_examples_electron_state() {
    let manifest_dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let electron_path = manifest_dir
        .join("examples")
        .join("electron")
        .join("b82c86cddd3c0b7c1b4bf5f6aae8b873f21900841bbdc87c12ec23b6b4e5f009.fcrstate");

    assert!(electron_path.exists(), "Electron .fcrstate file must exist in examples/electron!");

    let data = std::fs::read(&electron_path).unwrap();
    let record: FcrStateRecord = bincode::deserialize(&data).unwrap();

    assert!(record.n > 0);
    assert_eq!(record.state.validate_axioms(), Ok(()));
    assert!(!record.wl_hash.is_empty());

    let temp_dir = std::env::temp_dir().join("fcr_test_electron");
    let _ = std::fs::remove_dir_all(&temp_dir);

    let params = PhysicalParameters::default();
    let generator = StateSpaceGenerator::new(&temp_dir, params, 100);
    let meta = generator.generate_trajectories("electron_run", record.state.clone(), 2).unwrap();

    assert!(meta.total_states_generated > 0);

    let run_dir = temp_dir.join("run_electron_run");
    let summary = evaluate_time_step(run_dir, 2).unwrap();
    assert!(!summary.display_states.is_empty());

    let prob_sum: f64 = summary.display_states.iter().map(|s| s.display_probability_p).sum();
    assert!((prob_sum - 1.0).abs() < 1e-6);
}

#[test]
fn test_examples_muon_state() {
    let manifest_dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let muon_path = manifest_dir
        .join("examples")
        .join("muon")
        .join("0f04caf659452e9b4ea0eab2f4f15388b3900c42717be0d04c8600900d0fbf78.fcrstate");

    assert!(muon_path.exists(), "Muon .fcrstate file must exist in examples/muon!");

    let data = std::fs::read(&muon_path).unwrap();
    let record: FcrStateRecord = bincode::deserialize(&data).unwrap();

    assert_eq!(record.n, 6, "Muon M6 ground state must have n = 6 nodes!");
    assert_eq!(record.state.validate_axioms(), Ok(()));
    assert_eq!(record.wl_hash, "0f04caf659452e9b4ea0eab2f4f15388b3900c42717be0d04c8600900d0fbf78");

    let temp_dir = std::env::temp_dir().join("fcr_test_muon");
    let _ = std::fs::remove_dir_all(&temp_dir);

    let params = PhysicalParameters::default();
    let generator = StateSpaceGenerator::new(&temp_dir, params, 100);
    let meta = generator.generate_trajectories("muon_run", record.state.clone(), 2).unwrap();

    assert!(meta.total_states_generated > 0);

    let run_dir = temp_dir.join("run_muon_run");
    let summary = evaluate_time_step(run_dir, 2).unwrap();
    assert!(!summary.display_states.is_empty());

    let prob_sum: f64 = summary.display_states.iter().map(|s| s.display_probability_p).sum();
    assert!((prob_sum - 1.0).abs() < 1e-6);
}
