pub mod worker_supervisor;

/// Version supported by the private host/worker protocol.
pub const IPC_PROTOCOL_VERSION: u32 = 1;

/// Reports the protocol version through a small, testable host capability.
pub fn protocol_version() -> u32 {
    IPC_PROTOCOL_VERSION
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::protocol_version;

    #[test]
    fn protocol_version_is_positive_and_stable() {
        assert_eq!(protocol_version(), 1);
    }
}
