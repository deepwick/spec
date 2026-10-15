"""Minimal Chrome DevTools Protocol client (stdlib only) for driving Electron apps in tests."""

import base64
import hashlib
import json
import os
import socket
import struct
import time
import urllib.request
from urllib.parse import urlsplit

OP_CONT, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA
_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class CDPError(RuntimeError):
    pass


def accept_key(key: str) -> str:
    return base64.b64encode(hashlib.sha1((key + _GUID).encode()).digest()).decode()


def _apply_mask(data: bytes, mask: bytes) -> bytes:
    if not data:
        return b""
    key = (mask * (len(data) // 4 + 1))[: len(data)]
    return (int.from_bytes(data, "big") ^ int.from_bytes(key, "big")).to_bytes(len(data), "big")


def encode_frame(payload: bytes, opcode: int = OP_TEXT, *, fin: bool = True, mask: bytes | None = None) -> bytes:
    head = bytearray([(0x80 if fin else 0) | opcode])
    masked = 0x80 if mask is not None else 0
    n = len(payload)
    if n < 126:
        head.append(masked | n)
    elif n < 1 << 16:
        head.append(masked | 126)
        head += struct.pack("!H", n)
    else:
        head.append(masked | 127)
        head += struct.pack("!Q", n)
    if mask is None:
        return bytes(head) + payload
    return bytes(head) + mask + _apply_mask(payload, mask)


def read_frame(read) -> tuple[bool, int, bytes, bool]:
    """Read one frame through read(n), which returns exactly n bytes."""
    b1, b2 = read(2)
    n = b2 & 0x7F
    if n == 126:
        n = struct.unpack("!H", read(2))[0]
    elif n == 127:
        n = struct.unpack("!Q", read(8))[0]
    mask = read(4) if b2 & 0x80 else None
    payload = read(n)
    if mask is not None:
        payload = _apply_mask(payload, mask)
    return bool(b1 & 0x80), b1 & 0x0F, payload, mask is not None


class WebSocket:
    def __init__(self, url: str, timeout: float = 60.0):
        parts = urlsplit(url)
        if parts.scheme != "ws" or not parts.hostname:
            raise ValueError(f"not a ws:// URL: {url}")
        self._buf = b""
        self._sock = socket.create_connection((parts.hostname, parts.port or 80), timeout=timeout)
        try:
            self._handshake(parts)
        except BaseException:
            self._sock.close()
            raise

    def _handshake(self, parts) -> None:
        key = base64.b64encode(os.urandom(16)).decode()
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        self._sock.sendall(
            f"GET {target} HTTP/1.1\r\nHost: {parts.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode()
        )
        while b"\r\n\r\n" not in self._buf:
            self._fill()
        head, _, self._buf = self._buf.partition(b"\r\n\r\n")
        status, *lines = head.decode("latin-1").split("\r\n")
        if status.split()[1:2] != ["101"]:
            raise ConnectionError(f"WebSocket upgrade refused: {status}")
        headers = {name.strip().lower(): value.strip() for name, _, value in (line.partition(":") for line in lines)}
        if headers.get("sec-websocket-accept") != accept_key(key):
            raise ConnectionError("WebSocket upgrade: bad Sec-WebSocket-Accept")

    def _fill(self) -> None:
        chunk = self._sock.recv(65536)
        if not chunk:
            raise ConnectionError("WebSocket closed by peer")
        self._buf += chunk

    def _read(self, n: int) -> bytes:
        while len(self._buf) < n:
            self._fill()
        data, self._buf = self._buf[:n], self._buf[n:]
        return data

    def send(self, text: str) -> None:
        self._sock.sendall(encode_frame(text.encode(), OP_TEXT, mask=os.urandom(4)))

    def recv(self) -> str:
        parts = []
        while True:
            fin, opcode, payload, _ = read_frame(self._read)
            if opcode == OP_PING:
                self._sock.sendall(encode_frame(payload, OP_PONG, mask=os.urandom(4)))
            elif opcode == OP_CLOSE:
                raise ConnectionError("WebSocket closed by peer")
            elif opcode != OP_PONG:
                parts.append(payload)
                if fin:
                    return b"".join(parts).decode()

    def close(self) -> None:
        try:
            self._sock.sendall(encode_frame(b"", OP_CLOSE, mask=os.urandom(4)))
        except OSError:
            pass
        finally:
            self._sock.close()


def wait_for_page(port: int, timeout: float = 60.0, host: str = "127.0.0.1") -> str:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout
    last = "no response"
    while True:
        try:
            with opener.open(f"http://{host}:{port}/json", timeout=2) as response:
                for target in json.load(response):
                    if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                        return target["webSocketDebuggerUrl"]
            last = "no page target yet"
        except (OSError, ValueError) as e:
            last = str(e)
        if time.monotonic() >= deadline:
            raise TimeoutError(f"no CDP page target on port {port} after {timeout}s ({last})")
        time.sleep(0.25)


class CDPSession:
    def __init__(self, ws_url: str, timeout: float = 60.0):
        self._ws = WebSocket(ws_url, timeout)
        self._id = 0

    def call(self, method: str, **params) -> dict:
        self._id += 1
        self._ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            message = json.loads(self._ws.recv())
            if message.get("id") != self._id:
                continue
            if "error" in message:
                raise CDPError(f"{method}: {message['error'].get('message', message['error'])}")
            return message.get("result", {})

    def evaluate(self, expression: str):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in result:
            details = result["exceptionDetails"]
            raise CDPError(details.get("exception", {}).get("description") or details.get("text", "exception"))
        return result.get("result", {}).get("value")

    def close(self) -> None:
        self._ws.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def connect(port: int, timeout: float = 60.0, host: str = "127.0.0.1") -> CDPSession:
    return CDPSession(wait_for_page(port, timeout, host), timeout)
