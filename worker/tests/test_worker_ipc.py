import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from job_radar.runtime.stdio import serve
from job_radar.transport.protocol import MAX_FRAME_BYTES, ProtocolError, decode_request, read_frame

WORKER = Path(__file__).resolve().parents[1]


def request(method="app.hello", params=None, **changes):
    value = {
        "v": 1, "type": "request", "id": "12345678-1234-1234-1234-123456789abc",
        "method": method, "params": {"protocol_version": 1} if params is None else params,
    }
    return (json.dumps(value | changes, ensure_ascii=False) + "\n").encode()


def run_frames(data):
    output, diagnostics = io.BytesIO(), io.StringIO()
    code = serve(io.BytesIO(data), output, diagnostics)
    responses = [json.loads(line) for line in output.getvalue().splitlines()]
    return code, responses, diagnostics.getvalue()


def test_handshake_health_correlation_and_eof():
    code, responses, diagnostics = run_frames(request() + request("app.health", {}))
    assert code == 0
    assert diagnostics == ""
    assert responses[0]["result"]["protocol_version"] == 1
    assert responses[1]["result"]["db"] == "NOT_CONFIGURED"
    assert responses[1]["id"] == "12345678-1234-1234-1234-123456789abc"


@pytest.mark.parametrize("frame", [
    b"not json\n", b"[]\n", b"\xff\n", b'{"v":1,"v":1}\n',
    request(v=True), request(v=2), request(id="bad"), request(params=[]),
    b'{"value":NaN}\n', request(extra="private-secret"),
])
def test_invalid_envelopes_fail_closed_without_echo(frame):
    code, responses, diagnostics = run_frames(frame)
    assert code == 2
    assert responses == []
    assert diagnostics == "Worker rejected invalid IPC input\n"


def test_frame_limit_and_truncated_frame():
    for data in (b"x" * (MAX_FRAME_BYTES - 1) + b"\n", request().rstrip(b"\n")):
        with pytest.raises(ProtocolError):
            read_frame(io.BytesIO(data))
    assert read_frame(io.BytesIO()) is None


def test_unicode_and_multiple_frames():
    stream = io.BytesIO(request("未知") + request())
    assert decode_request(read_frame(stream)).method == "未知"
    assert decode_request(read_frame(stream)).method == "app.hello"


def test_allowlist_parameters_and_handshake_gate():
    _, responses, _ = run_frames(
        request("app.health", {}) + request(params={"protocol_version": 2})
        + request() + request("unknown", {}) + request("app.health", {"extra": 1})
    )
    assert [r.get("error", {}).get("code") for r in responses] == [
        "IPC_VERSION_MISMATCH", "IPC_VERSION_MISMATCH", None,
        "VALIDATION_ERROR", "VALIDATION_ERROR",
    ]


def test_real_worker_pipes_and_clean_exit():
    result = subprocess.run(
        [sys.executable, "-m", "job_radar"], cwd=WORKER,
        input=request() + request("app.health", {}), capture_output=True, timeout=10,
    )
    assert result.returncode == 0
    assert result.stderr == b""
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(responses) == 2
    assert all(response["ok"] for response in responses)
