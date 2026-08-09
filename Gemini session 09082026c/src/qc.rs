use crate::evaluator::{evaluate_time_step, StepEvaluationSummary};
use crate::fusion::{fuse_sub_universes, BridgeEdge};
use crate::generator::StateSpaceGenerator;
use crate::mutations::PhysicalParameters;
use crate::state::StateQ;
use num_complex::Complex64;
use std::path::Path;

pub enum QuantumGate {
    Hadamard { target: usize },
    PauliX { target: usize },
    CNOT { control: usize, target: usize },
}

pub struct FcrQuantumComputer {
    pub data_register: StateQ,
}

impl FcrQuantumComputer {
    /// Initialize a 2-qubit data register (nodes 0, 1 for qubit 0; nodes 2, 3 for qubit 1)
    pub fn new_2qubit_register() -> Self {
        let mut reg = StateQ::new(4);
        // Qubit 0 ground state: strong correlation between node 0 and 1 with 0 phase
        reg.set_c(0, 1, Complex64::new(0.9, 0.0));
        reg.set_mu(0, 1, 1.0);

        // Qubit 1 ground state: strong correlation between node 2 and 3 with 0 phase
        reg.set_c(2, 3, Complex64::new(0.9, 0.0));
        reg.set_mu(2, 3, 1.0);

        Self { data_register: reg }
    }

    /// Apply Hadamard gate topology on qubit 0 (introduces pi/2 phase correlation shift)
    pub fn apply_hadamard(&mut self, qubit: usize) {
        let n1 = qubit * 2;
        let n2 = qubit * 2 + 1;
        let c_current = self.data_register.get_c(n1, n2);
        // Phase rotation by pi/2 for Hadamard superposition
        let h_c = Complex64::new(c_current.re / 1.41421356, c_current.im + 0.70710678);
        self.data_register.set_c(n1, n2, h_c);
    }

    /// Apply CNOT gate topology between control and target qubits
    pub fn apply_cnot(&mut self, control_qubit: usize, target_qubit: usize) {
        let c_node = control_qubit * 2 + 1;
        let t_node = target_qubit * 2;

        let bridge = vec![BridgeEdge {
            node_a: c_node,
            node_b: t_node,
            initial_correlation_mag: 0.8,
            phase_offset: 0.0,
        }];

        // Create temporary 2-node program graph and fuse
        let prog = StateQ::new(2);
        if let Ok(fused) = fuse_sub_universes(&self.data_register, &prog, &bridge) {
            // Keep the data subsystem
            self.data_register = StateQ::new(4);
            for i in 0..4 {
                for j in 0..4 {
                    self.data_register.set_c(i, j, fused.get_c(i, j));
                    self.data_register.set_mu(i, j, fused.get_mu(i, j));
                }
            }
            // Entangle control & target nodes
            self.data_register.set_c(c_node, t_node, Complex64::new(0.70710678, 0.0));
        }
    }

    /// Run circuit simulation and generate Bell state branch probabilities
    pub fn execute_bell_state_simulation<P: AsRef<Path>>(
        &mut self,
        storage_root: P,
        run_id: &str,
        steps: usize,
    ) -> Result<StepEvaluationSummary, String> {
        self.apply_hadamard(0);
        self.apply_cnot(0, 1);

        let params = PhysicalParameters::default();
        let generator = StateSpaceGenerator::new(storage_root.as_ref(), params, 100);
        generator.generate_trajectories(run_id, self.data_register.clone(), steps)?;

        let run_dir = storage_root.as_ref().join(format!("run_{}", run_id));
        evaluate_time_step(run_dir, steps)
    }
}
