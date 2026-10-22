use std::fmt;

/// Public failures never include process output, paths or received payloads.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WorkerError {
    Unavailable,
    InvalidFrame,
    VersionMismatch,
    UnknownMethod,
    Busy,
    Timeout,
    Stopped,
    RestartLimit,
    Remote,
}

impl fmt::Display for WorkerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Worker failure: {self:?}")
    }
}

impl std::error::Error for WorkerError {}
