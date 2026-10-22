"""Bounded NDJSON framing and strict v1 request decoding."""

import json
from dataclasses import dataclass
from typing import BinaryIO
from uuid import UUID

MAX_FRAME_BYTES = 1_048_576


class ProtocolError(Exception):
    """Invalid input; deliberately contains no received content."""


@dataclass(frozen=True)
class Request:
    id: str
    method: str
    params: dict


def read_frame(stream: BinaryIO) -> bytes | None:
    frame = stream.readline(MAX_FRAME_BYTES + 1)
    if not frame:
        return None
    if len(frame) >= MAX_FRAME_BYTES or not frame.endswith(b"\n"):
        raise ProtocolError("Invalid frame boundary")
    return frame


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("Duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ProtocolError("Invalid JSON constant")


def decode_request(frame: bytes) -> Request:
    try:
        value = json.loads(
            frame.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_invalid_constant,
        )
        if not isinstance(value, dict) or set(value) != {"v", "type", "id", "method", "params"}:
            raise ValueError
        if type(value["v"]) is not int or value["v"] != 1 or value["type"] != "request":
            raise ValueError
        if not isinstance(value["id"], str) or str(UUID(value["id"])) != value["id"].lower():
            raise ValueError
        if not isinstance(value["method"], str) or not value["method"]:
            raise ValueError
        if not isinstance(value["params"], dict):
            raise ValueError
        return Request(value["id"], value["method"], value["params"])
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("Invalid request envelope") from exc


def encode_response(response: dict) -> bytes:
    return (json.dumps(response, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
