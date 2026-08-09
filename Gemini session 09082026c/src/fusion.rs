use crate::state::StateQ;
use num_complex::Complex64;

#[derive(Debug, Clone)]
pub struct BridgeEdge {
    pub node_a: usize,
    pub node_b: usize,
    pub initial_correlation_mag: f64,
    pub phase_offset: f64,
}

pub fn fuse_sub_universes(
    state_a: &StateQ,
    state_b: &StateQ,
    bridges: &[BridgeEdge],
) -> Result<StateQ, String> {
    let n_a = state_a.n as usize;
    let n_b = state_b.n as usize;
    let n_fused = n_a + n_b;

    let mut fused = StateQ::new(n_fused);

    // 1. Copy block state A into top-left
    for i in 0..n_a {
        for j in 0..n_a {
            fused.set_mu(i, j, state_a.get_mu(i, j));
            fused.set_c(i, j, state_a.get_c(i, j));
        }
    }

    // 2. Copy block state B into bottom-right (offset by n_a)
    for i in 0..n_b {
        for j in 0..n_b {
            let fi = n_a + i;
            let fj = n_a + j;
            fused.set_mu(fi, fj, state_b.get_mu(i, j));
            fused.set_c(fi, fj, state_b.get_c(i, j));
        }
    }

    // 3. Set bridge edges
    for bridge in bridges {
        if bridge.node_a >= n_a || bridge.node_b >= n_b {
            return Err(format!(
                "Invalid bridge node indices: A={}, B={}",
                bridge.node_a, bridge.node_b
            ));
        }
        let fi = bridge.node_a;
        let fj = n_a + bridge.node_b;

        let mag = bridge.initial_correlation_mag.min(1.0).max(0.0);
        let c_val = Complex64::from_polar(mag, bridge.phase_offset);
        fused.set_c(fi, fj, c_val);

        // Bridge metric default = 1.0
        fused.set_mu(fi, fj, 1.0);
    }

    // 4. Compute shortest-path cross-boundary metrics
    for i in 0..n_a {
        for j in 0..n_b {
            let fj = n_a + j;
            let mut min_dist = f64::INFINITY;

            for bridge in bridges {
                let a_node = bridge.node_a;
                let b_node = n_a + bridge.node_b;

                let dist_i_a = fused.get_mu(i, a_node);
                let dist_b_j = fused.get_mu(b_node, fj);
                let total = dist_i_a + 1.0 + dist_b_j; // bridge dist = 1.0

                if total < min_dist {
                    min_dist = total;
                }
            }

            if min_dist.is_finite() {
                fused.set_mu(i, fj, min_dist);
            }
        }
    }

    Ok(fused)
}
