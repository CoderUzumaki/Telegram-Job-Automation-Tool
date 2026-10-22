//! Host-owned worker lifecycle. No Tauri, UI or business logic dependencies.
mod error;
mod process;
mod protocol;
mod restart;

pub use error::WorkerError;
pub use process::{ResponseTicket, WorkerCommand};

use process::WorkerProcess;
use restart::RestartBudget;
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WorkerState {
    Stopped,
    Starting,
    Ready,
    Degraded,
    Restarting,
    Stopping,
    FailedPermanent,
}

pub struct WorkerSupervisor {
    command: WorkerCommand,
    process: Option<WorkerProcess>,
    state: WorkerState,
    budget: RestartBudget,
    restart_at: Option<Instant>,
    timeout: Duration,
    restart_exhausted: bool,
}

impl WorkerSupervisor {
    pub fn new(command: WorkerCommand, timeout: Duration) -> Self {
        Self {
            command,
            process: None,
            state: WorkerState::Stopped,
            budget: RestartBudget::new(Duration::from_secs(1)),
            restart_at: None,
            timeout,
            restart_exhausted: false,
        }
    }

    pub fn state(&self) -> WorkerState {
        self.state
    }

    pub fn start(&mut self) -> Result<(), WorkerError> {
        if self.state != WorkerState::Stopped {
            return Err(WorkerError::Busy);
        }
        self.state = WorkerState::Starting;
        self.restart_exhausted = false;
        self.budget = RestartBudget::new(Duration::from_secs(1));
        self.launch()
    }

    fn launch(&mut self) -> Result<(), WorkerError> {
        let result = (|| {
            let mut process = WorkerProcess::spawn(&self.command)?;
            let hello = process.request("app.hello", self.timeout)?.wait()?;
            if hello.get("protocol_version").and_then(|v| v.as_u64()) != Some(1) {
                return Err(WorkerError::VersionMismatch);
            }
            if hello.get("worker").and_then(|v| v.as_str()) != Some("READY") {
                return Err(WorkerError::InvalidFrame);
            }
            let capabilities = hello
                .get("capabilities")
                .and_then(|v| v.as_array())
                .ok_or(WorkerError::InvalidFrame)?;
            if !["app.hello", "app.health"]
                .iter()
                .all(|name| capabilities.iter().any(|v| v.as_str() == Some(name)))
                || hello.get("version").and_then(|v| v.as_str()).is_none()
            {
                return Err(WorkerError::InvalidFrame);
            }
            self.process = Some(process);
            Ok(())
        })();
        self.state = match &result {
            Ok(()) => WorkerState::Ready,
            Err(WorkerError::VersionMismatch | WorkerError::InvalidFrame) => {
                WorkerState::FailedPermanent
            }
            Err(_) => WorkerState::Degraded,
        };
        result
    }

    pub fn request(&mut self, method: &str) -> Result<ResponseTicket, WorkerError> {
        if self.state != WorkerState::Ready {
            return Err(WorkerError::Unavailable);
        }
        self.process
            .as_mut()
            .ok_or(WorkerError::Unavailable)?
            .request(method, self.timeout)
    }

    /// Call from the host's background lifecycle loop, never its UI thread.
    /// Backoff is scheduled, not slept; failed requests are never replayed.
    pub fn tick(&mut self, now: Instant) -> Result<(), WorkerError> {
        if matches!(
            self.state,
            WorkerState::Stopped | WorkerState::Stopping | WorkerState::FailedPermanent
        ) {
            return Ok(());
        }
        if let Some(process) = self.process.as_mut() {
            if let Some(error) = process.failure() {
                self.process.take();
                self.state = if matches!(
                    error,
                    WorkerError::VersionMismatch | WorkerError::InvalidFrame
                ) {
                    WorkerState::FailedPermanent
                } else {
                    WorkerState::Degraded
                };
                if self.state == WorkerState::FailedPermanent {
                    return Err(error);
                }
            }
        }
        if self.state == WorkerState::Degraded {
            if self.restart_exhausted {
                return Err(WorkerError::RestartLimit);
            }
            let delay = self.budget.reserve(now).inspect_err(|_| {
                self.restart_exhausted = true;
            })?;
            self.restart_at = Some(now + delay);
            self.state = WorkerState::Restarting;
        }
        if self.state == WorkerState::Restarting && self.restart_at.is_some_and(|at| now >= at) {
            self.restart_at = None;
            return self.launch();
        }
        Ok(())
    }

    pub fn shutdown(&mut self, grace: Duration) -> Result<(), WorkerError> {
        self.state = WorkerState::Stopping;
        self.restart_at = None;
        if let Some(mut process) = self.process.take() {
            process.stop(grace)?;
        }
        self.state = WorkerState::Stopped;
        Ok(())
    }
}

#[cfg(test)]
mod tests;
