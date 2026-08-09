use num_complex::Complex64;
use serde::{Deserialize, Serialize};

/// Internal World State Q in M_n under FCR v2.1
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StateQ {
    pub n: u32,
    pub mu: Vec<f64>,
    pub c: Vec<Complex64>,
    pub last_mutation_type: u64,
    pub node_capacity_exceeded: u32,
}

impl StateQ {
    /// Creates a new state with n nodes, rest metrics mu(i,j)=1.0 (for i!=j), mu(i,i)=0.0,
    /// C(i,i)=1.0+0i, and C(i,j)=0.0 for i!=j.
    pub fn new(n: usize) -> Self {
        let n_u32 = n as u32;
        let mut mu = vec![1.0; n * n];
        let mut c = vec![Complex64::new(0.0, 0.0); n * n];

        for i in 0..n {
            mu[i * n + i] = 0.0;
            c[i * n + i] = Complex64::new(1.0, 0.0);
        }

        Self {
            n: n_u32,
            mu,
            c,
            last_mutation_type: 0,
            node_capacity_exceeded: 0,
        }
    }

    #[inline]
    pub fn idx(&self, i: usize, j: usize) -> usize {
        let n = self.n as usize;
        i * n + j
    }

    pub fn get_raw_mu(&self, i: usize, j: usize) -> f64 {
        self.mu[self.idx(i, j)]
    }

    pub fn get_mu(&self, i: usize, j: usize) -> f64 {
        if i == j {
            return 0.0;
        }

        let c_ij = self.get_c(i, j);
        if c_ij.norm() > crate::reduction::EPSILON_CANCEL {
            return self.mu[self.idx(i, j)];
        }

        // For any unlinked pair (C(i,j) = 0), mu(i,j) is strictly defined as the
        // Shortest-Path Geodesic across active intermediate correlations:
        // mu(i,j) = ShortestPath_mu(i -> j) = min_gamma \sum_{e in gamma} mu(e)
        let n = self.n as usize;
        let mut dist = vec![f64::INFINITY; n];
        let mut visited = vec![false; n];
        dist[i] = 0.0;

        for _ in 0..n {
            let mut u = None;
            let mut min_d = f64::INFINITY;
            for v in 0..n {
                if !visited[v] && dist[v] < min_d {
                    min_d = dist[v];
                    u = Some(v);
                }
            }

            let u = match u {
                Some(u) => u,
                None => break,
            };

            if u == j {
                break;
            }

            visited[u] = true;

            for v in 0..n {
                if !visited[v] {
                    let c_uv = self.get_c(u, v);
                    if c_uv.norm() > crate::reduction::EPSILON_CANCEL {
                        let weight = self.mu[self.idx(u, v)];
                        if dist[u] + weight < dist[v] {
                            dist[v] = dist[u] + weight;
                        }
                    }
                }
            }
        }

        if dist[j].is_finite() {
            dist[j]
        } else {
            self.mu[self.idx(i, j)]
        }
    }

    pub fn set_mu(&mut self, i: usize, j: usize, val: f64) {
        let idx1 = self.idx(i, j);
        let idx2 = self.idx(j, i);
        self.mu[idx1] = val;
        self.mu[idx2] = val;
    }

    pub fn get_c(&self, i: usize, j: usize) -> Complex64 {
        self.c[self.idx(i, j)]
    }

    pub fn set_c(&mut self, i: usize, j: usize, val: Complex64) {
        let idx1 = self.idx(i, j);
        let idx2 = self.idx(j, i);
        self.c[idx1] = val;
        self.c[idx2] = val.conj();
    }

    /// Calculate external correlation capacity sum S(p) = sum_{q != p} |C(p,q)|^2
    pub fn calculate_capacity(&self, p: usize) -> f64 {
        let n = self.n as usize;
        let mut sum = 0.0;
        for q in 0..n {
            if q != p {
                let c_val = self.get_c(p, q);
                sum += c_val.norm_sqr();
            }
        }
        sum
    }

    /// Validates core FCR 2.1 axioms for this state
    pub fn validate_axioms(&self) -> Result<(), String> {
        let n = self.n as usize;
        for i in 0..n {
            if (self.get_mu(i, i)).abs() > 1e-9 {
                return Err(format!("Axiom Violation: mu({},{}) != 0.0", i, i));
            }
            if (self.get_c(i, i) - Complex64::new(1.0, 0.0)).norm() > 1e-9 {
                return Err(format!("Axiom Violation: C({},{}) != 1.0", i, i));
            }
            for j in 0..n {
                let mu_val = self.get_mu(i, j);
                if mu_val < 0.0 && mu_val != f64::NEG_INFINITY {
                    return Err(format!("Axiom Violation: mu({},{}) < 0", i, j));
                }
                let c_val = self.get_c(i, j);
                if c_val.norm() > 1.0 + 1e-7 {
                    return Err(format!("Axiom Violation: |C({},{})| > 1.0", i, j));
                }
                let c_ji = self.get_c(j, i);
                if (c_val.conj() - c_ji).norm() > 1e-7 {
                    return Err(format!("Axiom Violation: C({},{}) != C({},{})*", i, j, j, i));
                }
            }
        }
        Ok(())
    }
}
