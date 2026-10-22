use std::io::BufRead;

use serde::Deserialize;
use serde_json::{json, Value};
use uuid::Uuid;

use super::WorkerError;

pub const MAX_FRAME_BYTES: usize = 1_048_576;

/// fill_buf/consume bounds allocation even when a child never emits a newline.
pub fn read_frame(reader: &mut impl BufRead) -> Result<Option<Vec<u8>>, WorkerError> {
    let mut frame = Vec::new();
    loop {
        let chunk = reader.fill_buf().map_err(|_| WorkerError::Unavailable)?;
        if chunk.is_empty() {
            return if frame.is_empty() {
                Ok(None)
            } else {
                Err(WorkerError::InvalidFrame)
            };
        }
        let newline = chunk.iter().position(|byte| *byte == b'\n');
        let take = newline.map_or(chunk.len(), |index| index + 1);
        if frame.len() + take >= MAX_FRAME_BYTES {
            return Err(WorkerError::InvalidFrame);
        }
        frame.extend_from_slice(&chunk[..take]);
        reader.consume(take);
        if newline.is_some() {
            return Ok(Some(frame));
        }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope {
    v: u32,
    #[serde(rename = "type")]
    kind: String,
    id: String,
    ok: bool,
    #[serde(default, deserialize_with = "present")]
    result: Option<Value>,
    #[serde(default, deserialize_with = "present")]
    error: Option<RemoteError>,
}

fn present<'de, D, T>(deserializer: D) -> Result<Option<T>, D::Error>
where
    D: serde::Deserializer<'de>,
    T: Deserialize<'de>,
{
    T::deserialize(deserializer).map(Some)
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RemoteError {
    code: String,
    message: String,
    retryable: bool,
}

pub fn decode(frame: &[u8]) -> Result<(Uuid, Result<Value, WorkerError>), WorkerError> {
    let envelope: Envelope =
        serde_json::from_slice(frame).map_err(|_| WorkerError::InvalidFrame)?;
    if envelope.v != 1 {
        return Err(WorkerError::VersionMismatch);
    }
    if envelope.kind != "response" {
        return Err(WorkerError::InvalidFrame);
    }
    let id = Uuid::parse_str(&envelope.id).map_err(|_| WorkerError::InvalidFrame)?;
    match (envelope.ok, envelope.result, envelope.error) {
        (true, Some(result), None) => Ok((id, Ok(result))),
        (false, None, Some(error)) => {
            // Consume but never surface untrusted messages or hints.
            let _ = (error.message, error.retryable);
            let error = if error.code == "IPC_VERSION_MISMATCH" {
                WorkerError::VersionMismatch
            } else {
                WorkerError::Remote
            };
            Ok((id, Err(error)))
        }
        _ => Err(WorkerError::InvalidFrame),
    }
}

pub fn request(id: Uuid, method: &str) -> Result<Vec<u8>, WorkerError> {
    let params = match method {
        "app.hello" => json!({"protocol_version": 1}),
        "app.health" => json!({}),
        _ => return Err(WorkerError::UnknownMethod),
    };
    let mut bytes = serde_json::to_vec(&json!({
        "v": 1, "type": "request", "id": id.to_string(), "method": method, "params": params,
    }))
    .map_err(|_| WorkerError::InvalidFrame)?;
    bytes.push(b'\n');
    Ok(bytes)
}
