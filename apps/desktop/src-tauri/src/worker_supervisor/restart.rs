use std::{
    collections::VecDeque,
    time::{Duration, Instant},
};

use super::WorkerError;

pub(super) struct RestartBudget {
    attempts: VecDeque<Instant>,
    base_delay: Duration,
}

impl RestartBudget {
    pub fn new(base_delay: Duration) -> Self {
        Self {
            attempts: VecDeque::new(),
            base_delay,
        }
    }

    pub fn reserve(&mut self, now: Instant) -> Result<Duration, WorkerError> {
        while self
            .attempts
            .front()
            .is_some_and(|at| now.duration_since(*at) >= Duration::from_secs(600))
        {
            self.attempts.pop_front();
        }
        if self.attempts.len() >= 3 {
            return Err(WorkerError::RestartLimit);
        }
        let delay = self.base_delay.saturating_mul(1 << self.attempts.len());
        self.attempts.push_back(now);
        Ok(delay)
    }
}
