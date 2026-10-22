"""Serve private pipes until EOF; malformed input fails closed."""

from typing import BinaryIO, TextIO

from job_radar.transport.dispatcher import Dispatcher
from job_radar.transport.protocol import (
    ProtocolError,
    decode_request,
    encode_response,
    read_frame,
)


def serve(source: BinaryIO, destination: BinaryIO, diagnostics: TextIO) -> int:
    dispatcher = Dispatcher()
    try:
        while (frame := read_frame(source)) is not None:
            response = dispatcher.dispatch(decode_request(frame))
            destination.write(encode_response(response))
            destination.flush()
        return 0
    except ProtocolError:
        diagnostics.write("Worker rejected invalid IPC input\n")
        return 2
    except (BrokenPipeError, OSError):
        return 1


def main() -> int:
    import sys

    return serve(sys.stdin.buffer, sys.stdout.buffer, sys.stderr)
