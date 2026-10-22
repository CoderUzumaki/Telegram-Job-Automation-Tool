# Worker supervisor increment (JR-003)

The Rust supervisor now starts and handshakes with the real development Python
worker. This is a tested host library; the desktop event loop and React UI do not
yet start it. JR-003 remains in progress.

## Ownership

- `worker_supervisor/protocol.rs`: bounded framing, typed response decoding and
  the hello/health command allowlist.
- `worker_supervisor/process.rs`: private child pipes, bounded writer queue,
  response correlation and child cleanup. Up to 64 requests may be pending.
- `worker_supervisor/restart.rs`: three restart attempts in a ten-minute window,
  with one-, two- and four-second delays.
- `worker_supervisor/mod.rs`: handshake, lifecycle states and scheduled recovery.
  The future host background loop calls `tick`; no polling thread is hidden here.

The host composition root supplies the executable, arguments and working
directory. These are never accepted through a frontend command. Requests return
independent response tickets; waiting on one does not prevent another response
from being routed. Timeout/drop removes that ticket, and late or duplicate
responses cannot complete a different request. Timeouts do not prove cancellation
and commands are not automatically replayed.

EOF asks the worker to exit. Shutdown waits for a bounded grace period, then kills
and reaps the child and joins pipe threads. Dropping the process also reaps it.
Exhausting automatic restarts leaves the supervisor degraded until an explicit
stop/start. Incompatible protocol or malformed frames are permanent failures.
Worker stderr is currently discarded, rather than forwarded without redaction;
a useful sanitized diagnostics sink remains future work.

## Verification

After `uv sync --project worker --dev --locked`, run:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
```

The Rust suite uses the worker virtual environment by default. Set
`JOB_RADAR_TEST_PYTHON` to an explicit Python executable to override it. Tests run
without Telegram, databases or credentials. Fixtures cover out-of-order and
duplicate replies, protocol mismatch, silent children, request limits, forced
termination, bounded restart policy and the real hello/health/crash/restart/stop
sequence. CI provisions Python before running these tests.

## Remaining JR-003 work

- Shared method schemas and conformance checks across Python, Rust and TypeScript.
- Desktop background-loop integration, safe Tauri commands and health events.
- Packaged sidecar resolution and native quit integration; tests here exercise
  development Python processes, not a signed installer or close-to-tray behavior.
- Sanitized diagnostic capture and future event-envelope dispatch.

See [ADR-0002](decisions/ADR-0002.md) for the architecture baseline.
