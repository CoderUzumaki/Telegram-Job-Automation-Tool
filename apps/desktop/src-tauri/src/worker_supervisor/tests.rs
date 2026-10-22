use super::*;
use serde_json::json;
use std::{
    io::{BufReader, Cursor},
    path::PathBuf,
};

fn command(script: Option<&str>) -> WorkerCommand {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    let worker = root.join("worker");
    let python = if cfg!(windows) {
        worker.join(".venv/Scripts/python.exe")
    } else {
        worker.join(".venv/bin/python")
    };
    WorkerCommand {
        executable: std::env::var_os("JOB_RADAR_TEST_PYTHON")
            .map(PathBuf::from)
            .unwrap_or(python),
        arguments: match script {
            Some(script) => vec!["-u".into(), "-c".into(), script.into()],
            None => vec!["-u".into(), "-m".into(), "job_radar".into()],
        },
        working_directory: worker,
    }
}

#[test]
fn real_worker_handshake_health_crash_restart_and_quit() {
    let mut supervisor = WorkerSupervisor::new(command(None), Duration::from_secs(5));
    supervisor.start().unwrap();
    assert_eq!(supervisor.state(), WorkerState::Ready);
    let health = supervisor.request("app.health").unwrap().wait().unwrap();
    assert_eq!(health["db"], "NOT_CONFIGURED");
    assert!(matches!(
        supervisor.request("shell.run"),
        Err(WorkerError::UnknownMethod)
    ));
    supervisor.process.as_mut().unwrap().kill();
    let now = Instant::now();
    supervisor.tick(now).unwrap();
    assert_eq!(supervisor.state(), WorkerState::Restarting);
    supervisor.tick(now + Duration::from_secs(2)).unwrap();
    assert_eq!(supervisor.state(), WorkerState::Ready);
    supervisor.request("app.health").unwrap().wait().unwrap();
    supervisor.shutdown(Duration::from_secs(2)).unwrap();
    assert_eq!(supervisor.state(), WorkerState::Stopped);
    assert!(supervisor.process.is_none());
    supervisor.tick(now + Duration::from_secs(10)).unwrap();
    assert_eq!(supervisor.state(), WorkerState::Stopped);
}

#[test]
fn routes_out_of_order_replies() {
    let script = "import sys,json\na=json.loads(sys.stdin.readline())\nb=json.loads(sys.stdin.readline())\nfor r in [b,a]:\n print(json.dumps({'v':1,'type':'response','id':r['id'],'ok':True,'result':{'method':r['method']}}),flush=True)\nsys.stdin.read()";
    let mut process = WorkerProcess::spawn(&command(Some(script))).unwrap();
    let first = process
        .request("app.hello", Duration::from_secs(5))
        .unwrap();
    let second = process
        .request("app.health", Duration::from_secs(5))
        .unwrap();
    assert_eq!(second.wait().unwrap()["method"], "app.health");
    assert_eq!(first.wait().unwrap()["method"], "app.hello");
    process.stop(Duration::from_secs(2)).unwrap();
}

#[test]
fn stalled_worker_times_out_caps_requests_and_is_reaped() {
    let mut process = WorkerProcess::spawn(&command(Some("import time; time.sleep(60)"))).unwrap();
    let ticket = process
        .request("app.health", Duration::from_millis(20))
        .unwrap();
    assert_eq!(ticket.wait(), Err(WorkerError::Timeout));
    let tickets: Vec<_> = (0..64)
        .map(|_| {
            process
                .request("app.health", Duration::from_secs(5))
                .unwrap()
        })
        .collect();
    assert!(matches!(
        process.request("app.health", Duration::from_secs(5)),
        Err(WorkerError::Busy)
    ));
    process.stop(Duration::from_millis(10)).unwrap();
    for ticket in tickets {
        assert!(ticket.wait().is_err());
    }
}

#[test]
fn permanent_version_failure_does_not_restart() {
    let script = "import sys,json\nr=json.loads(sys.stdin.readline())\nprint(json.dumps({'v':2,'type':'response','id':r['id'],'ok':True,'result':{}}),flush=True)";
    let mut supervisor = WorkerSupervisor::new(command(Some(script)), Duration::from_secs(5));
    assert_eq!(supervisor.start(), Err(WorkerError::VersionMismatch));
    assert_eq!(supervisor.state(), WorkerState::FailedPermanent);
    supervisor.tick(Instant::now()).unwrap();
    assert!(supervisor.process.is_none());
}

#[test]
fn restart_budget_has_exponential_backoff_and_rolling_window() {
    let now = Instant::now();
    let mut budget = RestartBudget::new(Duration::from_secs(1));
    for seconds in [1, 2, 4] {
        assert_eq!(budget.reserve(now), Ok(Duration::from_secs(seconds)));
    }
    assert_eq!(budget.reserve(now), Err(WorkerError::RestartLimit));
    assert_eq!(
        budget.reserve(now + Duration::from_secs(600)),
        Ok(Duration::from_secs(1))
    );
}

#[test]
fn frames_are_bounded_and_support_split_unicode_and_coalesced_lines() {
    let mut reader = BufReader::with_capacity(1, Cursor::new("你好\nsecond\n".as_bytes()));
    assert_eq!(
        protocol::read_frame(&mut reader).unwrap().unwrap(),
        "你好\n".as_bytes()
    );
    assert_eq!(
        protocol::read_frame(&mut reader).unwrap().unwrap(),
        b"second\n"
    );
    assert_eq!(protocol::read_frame(&mut reader).unwrap(), None);
    for bytes in [vec![b'x'; protocol::MAX_FRAME_BYTES], b"truncated".to_vec()] {
        assert_eq!(
            protocol::read_frame(&mut Cursor::new(bytes)),
            Err(WorkerError::InvalidFrame)
        );
    }
}

#[test]
fn rejects_invalid_envelopes_and_does_not_echo_remote_details() {
    for bytes in [b"not json".as_slice(), b"[]", b"{\"v\":1,\"v\":1}"] {
        assert!(protocol::decode(bytes).is_err());
    }
    let id = uuid::Uuid::new_v4();
    let bytes = serde_json::to_vec(
        &json!({"v":1,"type":"response","id":id.to_string(),"ok":false,
        "error":{"code":"INTERNAL_ERROR","message":"secret-token","retryable":true}}),
    )
    .unwrap();
    assert_eq!(
        protocol::decode(&bytes).unwrap(),
        (id, Err(WorkerError::Remote))
    );
}

#[test]
fn null_result_is_valid_but_conflicting_error_is_not() {
    let mut response = json!({"v":1,"type":"response",
        "id":uuid::Uuid::new_v4().to_string(),"ok":true,"result":null});
    assert_eq!(
        protocol::decode(&serde_json::to_vec(&response).unwrap())
            .unwrap()
            .1,
        Ok(serde_json::Value::Null)
    );
    response["error"] = serde_json::Value::Null;
    assert!(protocol::decode(&serde_json::to_vec(&response).unwrap()).is_err());
}

#[test]
fn duplicate_reply_cannot_complete_another_request() {
    let script = "import sys,json\na=json.loads(sys.stdin.readline())\nb=json.loads(sys.stdin.readline())\nfor r in [a,a,b]:\n print(json.dumps({'v':1,'type':'response','id':r['id'],'ok':True,'result':r['method']}),flush=True)\nsys.stdin.read()";
    let mut process = WorkerProcess::spawn(&command(Some(script))).unwrap();
    let first = process
        .request("app.hello", Duration::from_secs(5))
        .unwrap();
    let second = process
        .request("app.health", Duration::from_secs(5))
        .unwrap();
    assert_eq!(first.wait().unwrap(), "app.hello");
    assert_eq!(second.wait().unwrap(), "app.health");
    process.stop(Duration::from_secs(2)).unwrap();
}

#[test]
fn exhausted_supervisor_requires_explicit_user_restart() {
    let mut supervisor = WorkerSupervisor::new(command(None), Duration::from_secs(5));
    let now = Instant::now();
    supervisor.state = WorkerState::Degraded;
    for _ in 0..3 {
        supervisor.budget.reserve(now).unwrap();
    }
    assert_eq!(supervisor.tick(now), Err(WorkerError::RestartLimit));
    assert_eq!(supervisor.state(), WorkerState::Degraded);
    assert_eq!(
        supervisor.tick(now + Duration::from_secs(601)),
        Err(WorkerError::RestartLimit)
    );
    supervisor.shutdown(Duration::ZERO).unwrap();
    supervisor.start().unwrap();
    supervisor.shutdown(Duration::from_secs(2)).unwrap();
}
