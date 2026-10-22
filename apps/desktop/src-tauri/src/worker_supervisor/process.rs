use std::{
    collections::HashMap,
    ffi::OsString,
    io::{BufReader, Write},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{mpsc, Arc, Mutex},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

use serde_json::Value;
use uuid::Uuid;

use super::{protocol, WorkerError};

type Reply = Result<Value, WorkerError>;
type Pending = Arc<Mutex<HashMap<Uuid, mpsc::Sender<Reply>>>>;

/// Supplied by trusted host composition, never by a UI command payload.
#[derive(Clone)]
pub struct WorkerCommand {
    pub executable: PathBuf,
    pub arguments: Vec<OsString>,
    pub working_directory: PathBuf,
}

pub struct ResponseTicket {
    id: Uuid,
    receiver: mpsc::Receiver<Reply>,
    pending: Pending,
    deadline: Instant,
}

impl ResponseTicket {
    pub fn wait(self) -> Reply {
        self.receiver
            .recv_timeout(self.deadline.saturating_duration_since(Instant::now()))
            .unwrap_or_else(|error| {
                Err(match error {
                    mpsc::RecvTimeoutError::Timeout => WorkerError::Timeout,
                    mpsc::RecvTimeoutError::Disconnected => WorkerError::Unavailable,
                })
            })
    }
}

impl Drop for ResponseTicket {
    fn drop(&mut self) {
        self.pending.lock().unwrap().remove(&self.id);
    }
}

pub(super) struct WorkerProcess {
    child: Child,
    writer: Option<mpsc::SyncSender<Vec<u8>>>,
    writer_thread: Option<JoinHandle<()>>,
    pending: Pending,
    reader: Option<JoinHandle<()>>,
    failure: Arc<Mutex<Option<WorkerError>>>,
}

impl WorkerProcess {
    pub fn spawn(config: &WorkerCommand) -> Result<Self, WorkerError> {
        let mut command = Command::new(&config.executable);
        command
            .args(&config.arguments)
            .current_dir(&config.working_directory)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        // A sidecar must not open a console window on Windows.
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command.spawn().map_err(|_| WorkerError::Unavailable)?;
        let mut stdin = child.stdin.take().ok_or(WorkerError::Unavailable)?;
        let stdout = child.stdout.take().ok_or(WorkerError::Unavailable)?;
        let pending: Pending = Arc::default();
        let routes = Arc::clone(&pending);
        let failure = Arc::new(Mutex::new(None));
        let (writer, outgoing) = mpsc::sync_channel::<Vec<u8>>(64);
        let writer_failure = Arc::clone(&failure);
        let writer_routes = Arc::clone(&pending);
        let writer_thread = thread::spawn(move || {
            for bytes in outgoing {
                if stdin.write_all(&bytes).is_err() {
                    *writer_failure.lock().unwrap() = Some(WorkerError::Unavailable);
                    for (_, sender) in writer_routes.lock().unwrap().drain() {
                        let _ = sender.send(Err(WorkerError::Unavailable));
                    }
                    break;
                }
            }
        });
        let reader_failure = Arc::clone(&failure);
        let reader = thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            let error = loop {
                let frame = match protocol::read_frame(&mut reader) {
                    Ok(Some(frame)) => frame,
                    Ok(None) => break WorkerError::Unavailable,
                    Err(error) => break error,
                };
                match protocol::decode(&frame) {
                    Ok((id, result)) => {
                        // Late responses after timeout are advisory and discarded.
                        if let Some(sender) = routes.lock().unwrap().remove(&id) {
                            let _ = sender.send(result);
                        }
                    }
                    Err(error) => break error,
                }
            };
            *reader_failure.lock().unwrap() = Some(error.clone());
            for (_, sender) in routes.lock().unwrap().drain() {
                let _ = sender.send(Err(error.clone()));
            }
        });
        Ok(Self {
            child,
            writer: Some(writer),
            writer_thread: Some(writer_thread),
            pending,
            reader: Some(reader),
            failure,
        })
    }

    pub fn request(
        &mut self,
        method: &str,
        timeout: Duration,
    ) -> Result<ResponseTicket, WorkerError> {
        let id = Uuid::new_v4();
        let bytes = protocol::request(id, method)?;
        if let Some(error) = self.failure.lock().unwrap().clone() {
            return Err(error);
        }
        let (sender, receiver) = mpsc::channel();
        {
            let mut pending = self.pending.lock().unwrap();
            if pending.len() >= 64 {
                return Err(WorkerError::Busy);
            }
            pending.insert(id, sender);
        }
        let ticket = ResponseTicket {
            id,
            receiver,
            pending: Arc::clone(&self.pending),
            deadline: Instant::now() + timeout,
        };
        self.writer
            .as_mut()
            .ok_or(WorkerError::Stopped)?
            .try_send(bytes)
            .map_err(|error| match error {
                mpsc::TrySendError::Full(_) => WorkerError::Busy,
                mpsc::TrySendError::Disconnected(_) => WorkerError::Unavailable,
            })?;
        Ok(ticket)
    }

    pub fn failure(&mut self) -> Option<WorkerError> {
        self.failure
            .lock()
            .unwrap()
            .clone()
            .or_else(|| match self.child.try_wait() {
                Ok(None) => None,
                _ => Some(WorkerError::Unavailable),
            })
    }

    pub fn stop(&mut self, grace: Duration) -> Result<(), WorkerError> {
        self.writer.take(); // EOF is the current worker's graceful shutdown signal.
        let deadline = Instant::now() + grace;
        loop {
            match self.child.try_wait() {
                Ok(Some(_)) => break,
                Ok(None) if Instant::now() < deadline => thread::sleep(Duration::from_millis(5)),
                _ => {
                    self.child.kill().map_err(|_| WorkerError::Unavailable)?;
                    self.child.wait().map_err(|_| WorkerError::Unavailable)?;
                    break;
                }
            }
        }
        if let Some(reader) = self.reader.take() {
            let _ = reader.join();
        }
        if let Some(writer) = self.writer_thread.take() {
            let _ = writer.join();
        }
        Ok(())
    }

    #[cfg(test)]
    pub fn kill(&mut self) {
        self.child.kill().unwrap();
        self.child.wait().unwrap();
    }
}

impl Drop for WorkerProcess {
    fn drop(&mut self) {
        let _ = self.stop(Duration::ZERO);
    }
}
