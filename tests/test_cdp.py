import http.client
import http.server
import json
import socket
import threading
import urllib.request

import pytest

from deepwick_spec.cdp import (
    OP_CLOSE,
    OP_CONT,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    CDPError,
    CDPSession,
    accept_key,
    connect,
    encode_frame,
    read_frame,
    wait_for_page,
)


def reader(data: bytes):
    pos = 0

    def read(n):
        nonlocal pos
        chunk = data[pos : pos + n]
        pos += n
        return chunk

    return read


class FakeDevTools:
    """One-connection WebSocket server. reply(request) returns the raw frames to send back."""

    def __init__(self, reply, accept=None):
        self.reply = reply
        self.accept = accept
        self.received = []
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.url = f"ws://127.0.0.1:{self.listener.getsockname()[1]}/devtools/page/FAKE"
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        conn, _ = self.listener.accept()
        with conn, self.listener:
            buf = b""
            while b"\r\n\r\n" not in buf:
                buf += conn.recv(4096)
            head, _, pending = buf.partition(b"\r\n\r\n")
            key = next(
                line.split(b":", 1)[1].strip().decode()
                for line in head.split(b"\r\n")
                if line.lower().startswith(b"sec-websocket-key:")
            )
            accept = self.accept or accept_key(key)
            conn.sendall(
                b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                b"Sec-WebSocket-Accept: " + accept.encode() + b"\r\n\r\n"
            )

            def read(n):
                nonlocal pending
                while len(pending) < n:
                    chunk = conn.recv(65536)
                    if not chunk:
                        raise ConnectionError
                    pending += chunk
                data, pending = pending[:n], pending[n:]
                return data

            try:
                while True:
                    fin, opcode, payload, masked = read_frame(read)
                    self.received.append((masked, opcode, payload))
                    if opcode == OP_CLOSE:
                        return
                    if opcode == OP_TEXT:
                        for frame in self.reply(json.loads(payload)):
                            conn.sendall(frame)
            except (ConnectionError, OSError):
                return


def result(req, value):
    body = {"id": req["id"], "result": {"result": {"type": "object", "value": value}}}
    return [encode_frame(json.dumps(body).encode())]


def test_accept_key_rfc6455_example():
    assert accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_encode_frame_rfc6455_examples():
    assert encode_frame(b"Hello") == bytes.fromhex("810548656c6c6f")
    assert encode_frame(b"Hello", mask=bytes.fromhex("37fa213d")) == bytes.fromhex("818537fa213d7f9f4d5158")
    assert encode_frame(b"\0" * 256, 0x2)[:4] == bytes.fromhex("827e0100")
    assert encode_frame(b"\0" * 65536, 0x2)[:10] == bytes.fromhex("827f0000000000010000")


def test_read_frame_unmasks():
    assert read_frame(reader(bytes.fromhex("818537fa213d7f9f4d5158"))) == (True, OP_TEXT, b"Hello", True)
    assert read_frame(reader(bytes.fromhex("010348656c"))) == (False, OP_TEXT, b"Hel", False)


def test_evaluate_returns_value_and_masks_every_frame():
    server = FakeDevTools(lambda req: result(req, {"expr": req["params"]["expression"], "await": req["params"]["awaitPromise"]}))
    with CDPSession(server.url, timeout=5) as session:
        assert session.evaluate("1 + 1") == {"expr": "1 + 1", "await": True}
    server.thread.join(5)
    assert server.received and all(masked for masked, _, _ in server.received)
    assert server.received[-1][1] == OP_CLOSE


@pytest.mark.parametrize("size", [125, 1000, 70000])
def test_large_messages_both_directions(size):
    server = FakeDevTools(lambda req: result(req, req["params"]["expression"]))
    with CDPSession(server.url, timeout=5) as session:
        assert session.evaluate("x" * size) == "x" * size


def test_fragmented_reply_with_ping_between_fragments():
    def reply(req):
        body = json.dumps({"id": req["id"], "result": {"result": {"value": "joined"}}}).encode()
        return [encode_frame(body[:10], OP_TEXT, fin=False), encode_frame(b"hb", OP_PING), encode_frame(body[10:], OP_CONT)]

    server = FakeDevTools(reply)
    with CDPSession(server.url, timeout=5) as session:
        assert session.evaluate("x") == "joined"
    server.thread.join(5)
    assert (True, OP_PONG, b"hb") in server.received


def test_events_and_other_ids_are_skipped():
    def reply(req):
        event = encode_frame(json.dumps({"method": "Runtime.consoleAPICalled", "params": {}}).encode())
        stale = encode_frame(json.dumps({"id": 999, "result": {"result": {"value": "stale"}}}).encode())
        return [event, stale, *result(req, "fresh")]

    server = FakeDevTools(reply)
    with CDPSession(server.url, timeout=5) as session:
        assert session.evaluate("x") == "fresh"


def test_js_exception_raises_cdperror():
    def reply(req):
        details = {"text": "Uncaught", "exception": {"description": "ReferenceError: nope is not defined"}}
        body = {"id": req["id"], "result": {"result": {"type": "object"}, "exceptionDetails": details}}
        return [encode_frame(json.dumps(body).encode())]

    server = FakeDevTools(reply)
    with CDPSession(server.url, timeout=5) as session, pytest.raises(CDPError, match="ReferenceError"):
        session.evaluate("nope")


def test_protocol_error_raises_cdperror():
    def reply(req):
        body = {"id": req["id"], "error": {"code": -32601, "message": "'Nope.method' wasn't found"}}
        return [encode_frame(json.dumps(body).encode())]

    server = FakeDevTools(reply)
    with CDPSession(server.url, timeout=5) as session, pytest.raises(CDPError, match="wasn't found"):
        session.call("Nope.method")


def test_bad_accept_header_is_rejected():
    server = FakeDevTools(lambda req: [], accept="bogus")
    with pytest.raises(ConnectionError, match="Accept"):
        CDPSession(server.url, timeout=5)


def test_close_frame_from_peer_raises():
    server = FakeDevTools(lambda req: [encode_frame(b"", OP_CLOSE)])
    with CDPSession(server.url, timeout=5) as session, pytest.raises(ConnectionError, match="closed"):
        session.evaluate("x")


def test_rejects_non_ws_urls():
    with pytest.raises(ValueError, match="ws://"):
        CDPSession("http://127.0.0.1:1/x")


@pytest.fixture
def json_endpoint():
    servers = []

    def serve(targets):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps(targets).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return server.server_address[1]

    yield serve
    for server in servers:
        server.shutdown()
        server.server_close()


def test_wait_for_page_picks_the_page_target(json_endpoint):
    port = json_endpoint([
        {"type": "service_worker", "webSocketDebuggerUrl": "ws://127.0.0.1:1/worker"},
        {"type": "page", "webSocketDebuggerUrl": "ws://127.0.0.1:1/page"},
    ])
    assert wait_for_page(port, timeout=5) == "ws://127.0.0.1:1/page"


def test_wait_for_page_ignores_proxy_settings(json_endpoint, monkeypatch):
    for name in ("http_proxy", "HTTP_PROXY"):
        monkeypatch.setenv(name, "http://127.0.0.1:9")
    for name in ("no_proxy", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
    port = json_endpoint([{"type": "page", "webSocketDebuggerUrl": "ws://127.0.0.1:1/page"}])
    assert wait_for_page(port, timeout=5) == "ws://127.0.0.1:1/page"


def test_wait_for_page_times_out_naming_the_port(json_endpoint):
    port = json_endpoint([{"type": "service_worker", "webSocketDebuggerUrl": "ws://127.0.0.1:1/worker"}])
    with pytest.raises(TimeoutError, match=f"port {port}"):
        wait_for_page(port, timeout=0.6)


def test_connect_finds_the_page_and_evaluates(json_endpoint):
    server = FakeDevTools(lambda req: result(req, 42))
    port = json_endpoint([{"type": "page", "webSocketDebuggerUrl": server.url}])
    with connect(port, timeout=5) as session:
        assert session.evaluate("6 * 7") == 42


def test_call_timeout_names_the_method():
    server = FakeDevTools(lambda req: [])
    session = CDPSession(server.url, timeout=0.5)
    with pytest.raises(CDPError, match=r"Runtime.evaluate: no reply within 0.5s"):
        session.evaluate("1")
    session.close()


def test_wait_for_page_retries_on_bad_http(monkeypatch):
    calls = []

    class Opener:
        def open(self, url, timeout):
            calls.append(url)
            raise http.client.BadStatusLine("garbage")

    monkeypatch.setattr(urllib.request, "build_opener", lambda *a: Opener())
    with pytest.raises(TimeoutError, match="garbage|BadStatusLine"):
        wait_for_page(1, timeout=0.6)
    assert len(calls) >= 2
