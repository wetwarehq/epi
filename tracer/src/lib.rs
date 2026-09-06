//! Process-boundary tracer.
//!
//! Records calls, not thoughts. Has no tool handle. The room scores the log
//! this tracer would have written; this crate does not decide validity.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Call {
    pub t: u32,
    pub agent: String,
    pub op: String,
    pub path: Option<String>,
    pub digest: Option<String>,
    pub residue: bool,
    pub valid: bool,
}

#[derive(Clone, Debug, Default)]
pub struct Tracer {
    calls: Vec<Call>,
}

impl Tracer {
    pub fn new() -> Self {
        Self { calls: Vec::new() }
    }

    pub fn record(&mut self, call: Call) {
        self.calls.push(call);
    }

    pub fn calls(&self) -> &[Call] {
        &self.calls
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn records_in_order() {
        let mut t = Tracer::new();
        t.record(Call {
            t: 0,
            agent: "W0".into(),
            op: "put".into(),
            path: Some("/board/cheat".into()),
            digest: Some("e9daa40d".into()),
            residue: false,
            valid: true,
        });
        assert_eq!(t.calls().len(), 1);
        assert_eq!(t.calls()[0].op, "put");
    }
}
