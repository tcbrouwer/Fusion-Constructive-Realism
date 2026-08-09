use clap::{Parser, Subcommand};
use fcr_core::{
    evaluate_time_step, FcrQuantumComputer, PhysicalParameters, StateQ, StateSpaceGenerator,
};
use num_complex::Complex64;
use std::path::PathBuf;
use std::time::Instant;

#[derive(Parser)]
#[command(name = "fcr_engine")]
#[command(about = "Foundational State-Space & Reduction Engine for FCR 2.1", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate state-space macro trajectories from an initial Q0
    Generate {
        #[arg(short, long, default_value_t = 3)]
        nodes: usize,

        #[arg(short, long, default_value_t = 3)]
        steps: usize,

        #[arg(short, long, default_value = "./output")]
        out_dir: PathBuf,

        #[arg(short, long, default_value = "run_001")]
        run_id: String,

        #[arg(short, long)]
        initial_state: Option<PathBuf>,

        #[arg(short = 't', long, default_value_t = 100)]
        top_states: usize,
    },

    /// Evaluate Born-rule display probability distribution for a given time step
    Evaluate {
        #[arg(short, long)]
        run_dir: PathBuf,

        #[arg(short, long, default_value_t = 3)]
        step: usize,

        #[arg(short = 't', long, default_value_t = 10)]
        top: usize,
    },

    /// Run Quantum Computer Simulator Bell State demonstration
    QcDemo {
        #[arg(short, long, default_value = "./output")]
        out_dir: PathBuf,

        #[arg(short, long, default_value = "qc_bell_001")]
        run_id: String,
    },

    /// Inspect a specific .fcrstate file in detail
    Inspect {
        #[arg(short, long)]
        file: PathBuf,

        #[arg(short, long)]
        json: bool,
    },

    /// Save a raw JSON state payload to a .fcrstate binary file
    SaveState {
        #[arg(short, long)]
        json_state: String,

        #[arg(short, long)]
        out_dir: PathBuf,
    },

    /// Run engine performance benchmarks
    Benchmark {
        #[arg(short, long, default_value_t = 4)]
        nodes: usize,

        #[arg(short, long, default_value_t = 3)]
        steps: usize,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Generate {
            nodes,
            steps,
            out_dir,
            run_id,
            initial_state,
            top_states,
        } => {
            let q0 = if let Some(init_path) = initial_state {
                if !init_path.exists() {
                    return Err(format!("Initial state file {:?} does not exist", init_path).into());
                }
                let data = std::fs::read(&init_path)?;
                let record: fcr_core::generator::FcrStateRecord = bincode::deserialize(&data)?;
                println!("Loaded custom initial state Q0 from {:?}", init_path);
                record.state
            } else {
                println!("Initializing FCR 2.1 State-Space Generator (n={} nodes, steps={}, top_states={})...", nodes, steps, top_states);
                let mut q0 = StateQ::new(nodes);
                if nodes >= 2 {
                    q0.set_c(0, 1, Complex64::new(0.8, 0.2));
                    q0.set_mu(0, 1, 1.0);
                }
                if nodes >= 3 {
                    q0.set_c(1, 2, Complex64::new(0.7, -0.3));
                    q0.set_mu(1, 2, 1.2);
                }
                q0
            };

            let params = PhysicalParameters::default();
            let generator = StateSpaceGenerator::new(&out_dir, params, top_states);
            let start = Instant::now();
            let meta = generator.generate_trajectories(&run_id, q0, steps)?;
            let elapsed = start.elapsed();

            println!(
                "Successfully generated {} states across {} steps in {:?}",
                meta.total_states_generated, meta.total_poset_steps, elapsed
            );
            println!("Run directory: {:?}", out_dir.join(format!("run_{}", run_id)));
        }

        Commands::Evaluate { run_dir, step, top } => {
            println!("Evaluating Born-Rule Display Probabilities for {:?}", run_dir);
            let summary = evaluate_time_step(&run_dir, step)?;

            let show_count = if top == 0 || top >= summary.display_states.len() {
                summary.display_states.len()
            } else {
                top
            };

            println!("\n======================================================================================================================");
            println!("FCR 2.1 State-Space Display Evaluator | Time Step T = {}", summary.time_step);
            println!("======================================================================================================================");
            println!(
                "{:<5} {:<30} {:<11} {:<7} {:<10} {:<15} {:<20} {:<18}",
                "Rank", "Canonical WL Hash", "Path Count", "Edges", "Avg |C|", "Top Seq", "Accumulated Weight", "Display Prob P([Q])"
            );
            println!("----------------------------------------------------------------------------------------------------------------------");

            for res in summary.display_states.iter().take(show_count) {
                let truncated_hash = if res.wl_hash.len() > 26 {
                    format!("{}...", &res.wl_hash[..23])
                } else {
                    res.wl_hash.clone()
                };
                println!(
                    "{:<5} {:<30} {:<11} {:<7} {:<10.4} {:<15} {:<20.4e} {:<18.6}",
                    res.rank,
                    truncated_hash,
                    res.path_count,
                    res.active_edge_count,
                    res.avg_edge_weight_modulus,
                    res.top_mutation_sequence,
                    res.accumulated_weight_a,
                    res.display_probability_p
                );
            }

            println!("----------------------------------------------------------------------------------------------------------------------");
            println!(
                "Total Macro States: {} | Trajectory Path Count Sum: {}",
                summary.total_macro_states, summary.total_trajectory_paths
            );
            if show_count < summary.display_states.len() {
                println!(
                    "Note: Displaying top {} of {} total states. Use '--top <N>' or '--top 0' (to show all) for more rows.",
                    show_count, summary.display_states.len()
                );
            }
            println!("======================================================================================================================\n");
        }

        Commands::Inspect { file, json } => {
            if !file.exists() {
                return Err(format!("File {:?} does not exist", file).into());
            }
            let data = std::fs::read(&file)?;
            let record: fcr_core::generator::FcrStateRecord = bincode::deserialize(&data)?;

            if json {
                println!("{}", serde_json::to_string_pretty(&record)?);
                return Ok(());
            }

            println!("\n========================================================================================");
            println!("FCR 2.1 State Inspector | File: {:?}", file);
            println!("========================================================================================");
            println!("Canonical WL Hash : {}", record.wl_hash);
            println!("Path Count        : {}", record.path_count);
            println!("Accumulated Wt A  : {:.6e}", record.accumulated_weight_a);
            println!("Top Sequence      : {}", record.top_mutation_sequence());
            println!("Node Count n      : {}", record.n);
            println!("Parent Hashes     : {:?}", record.parent_hashes);
            println!("----------------------------------------------------------------------------------------");

            println!("\n--- Node External Correlation Capacities S(p) ---");
            let n = record.n as usize;
            for p in 0..n {
                let s_p = record.state.calculate_capacity(p);
                let status = if s_p > 1.0 + 1e-6 { "EXCEEDED" } else { "OK" };
                println!("  Node {:>2} | S(p) = {:.6}  [{}]", p, s_p, status);
            }

            println!("\n--- Complex Correlation Matrix C(i,j) [Magnitude | Phase (deg)] ---");
            print!("    ");
            for j in 0..n {
                print!("{:>16} ", format!("Node {}", j));
            }
            println!();

            for i in 0..n {
                print!("Node {:>2} ", i);
                for j in 0..n {
                    let c_val = record.state.get_c(i, j);
                    let mag = c_val.norm();
                    let phase_deg = c_val.arg().to_degrees();
                    print!("{:>6.3} | {:>6.1}°  ", mag, phase_deg);
                }
                println!();
            }

            println!("\n--- Active Non-Zero Correlations (|C(i,j)| > 1e-6) ---");
            let mut edge_count = 0;
            for i in 0..n {
                for j in (i + 1)..n {
                    let c_val = record.state.get_c(i, j);
                    if c_val.norm() > 1e-6 {
                        edge_count += 1;
                        let mu_val = record.state.get_mu(i, j);
                        println!(
                            "  Edge ({}, {}): |C| = {:.6}, Phase = {:.2}°, Metric dist mu = {:.6}",
                            i,
                            j,
                            c_val.norm(),
                            c_val.arg().to_degrees(),
                            mu_val
                        );
                    }
                }
            }
            if edge_count == 0 {
                println!("  No active edges.");
            }
            println!("========================================================================================\n");
        }

        Commands::SaveState { json_state, out_dir } => {
            let state: fcr_core::state::StateQ = serde_json::from_str(&json_state)?;
            let wl_hash = fcr_core::reduction::compute_wl_hash(&state);
            let record = fcr_core::generator::FcrStateRecord {
                n: state.n,
                path_count: 1,
                accumulated_weight_a: 1.0,
                wl_hash: wl_hash.clone(),
                state,
                parent_hashes: Vec::new(),
                transition_weights: Vec::new(),
                mutation_sequences: std::collections::HashMap::new(),
                last_mutation: None,
                block_variant: 0,
                block_length: 0,
                block_multiplicities: std::collections::HashMap::new(),
            };
            std::fs::create_dir_all(&out_dir)?;
            let out_file = out_dir.join(format!("{}.fcrstate", wl_hash));
            let encoded = bincode::serialize(&record)?;
            std::fs::write(&out_file, encoded)?;
            println!("Saved state to: {:?}", out_file);
            println!("WL_HASH: {}", wl_hash);
        }

        Commands::QcDemo { out_dir, run_id } => {
            println!("Executing FCR Quantum Computer Simulator (Bell State Demo)...");
            let mut qc = FcrQuantumComputer::new_2qubit_register();
            let summary = qc.execute_bell_state_simulation(&out_dir, &run_id, 2)?;

            println!("\n========================================================================================");
            println!("FCR 2.1 Quantum Computer Simulation (Bell State |Phi+>) | Output Display Probabilities");
            println!("========================================================================================");
            for res in summary.display_states.iter().take(5) {
                println!(
                    "Rank {:<2} | WL Hash: {}... | Probability P([Q]): {:.6}",
                    res.rank, &res.wl_hash[..16], res.display_probability_p
                );
            }
            println!("========================================================================================\n");
        }

        Commands::Benchmark { nodes, steps } => {
            println!("Running FCR 2.1 Benchmark (nodes={}, steps={})...", nodes, steps);
            let mut q0 = StateQ::new(nodes);
            for i in 0..nodes {
                for j in (i+1)..nodes {
                    q0.set_c(i, j, Complex64::new(0.5, 0.1));
                }
            }

            let temp_dir = std::env::temp_dir().join("fcr_bench");
            let params = PhysicalParameters::default();
            let generator = StateSpaceGenerator::new(&temp_dir, params, 100);

            let start = Instant::now();
            let meta = generator.generate_trajectories("bench", q0, steps)?;
            let elapsed = start.elapsed();

            println!(
                "Benchmark Complete: {} states generated in {:?} ({:.2} states/sec)",
                meta.total_states_generated,
                elapsed,
                meta.total_states_generated as f64 / elapsed.as_secs_f64()
            );
        }
    }

    Ok(())
}
