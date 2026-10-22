"""Allowlisted startup commands; no process or stream ownership."""

from job_radar import worker_version
from job_radar.transport.protocol import Request


class Dispatcher:
    def __init__(self):
        self.ready = False
        self.handlers = {"app.hello": self.hello, "app.health": self.health}

    def dispatch(self, request: Request) -> dict:
        response = {"v": 1, "type": "response", "id": request.id}
        handler = self.handlers.get(request.method)
        if handler is None:
            return response | self.error("VALIDATION_ERROR", "Unknown method")
        if request.method != "app.hello" and not self.ready:
            return response | self.error("IPC_VERSION_MISMATCH", "Handshake required")
        return response | handler(request.params)

    @staticmethod
    def error(code: str, message: str) -> dict:
        return {"ok": False, "error": {"code": code, "message": message, "retryable": False}}

    def hello(self, params: dict) -> dict:
        if set(params) != {"protocol_version"} or type(params["protocol_version"]) is not int:
            return self.error("VALIDATION_ERROR", "Invalid hello parameters")
        if params["protocol_version"] != 1:
            self.ready = False
            return self.error("IPC_VERSION_MISMATCH", "Unsupported protocol version")
        self.ready = True
        return {"ok": True, "result": {
            "protocol_version": 1, "version": worker_version(),
            "capabilities": list(self.handlers), "worker": "READY",
        }}

    def health(self, params: dict) -> dict:
        if params:
            return self.error("VALIDATION_ERROR", "Invalid health parameters")
        return {"ok": True, "result": {
            "worker": "READY", "telegram": "NOT_CONFIGURED",
            "sync": "STOPPED", "db": "NOT_CONFIGURED",
        }}
