"""fn_memory_inproc.py - a socketless, in-process FN-Memory 30515c0a centre for graph tests and verification.

InProcFnMemoryCentre runs the REAL FN-Memory HTTP runtime of a pinned checkout inside the calling process:
space_neurons.memory.http_server.build_server() (-> _build_runtime: MultiUserServer, TokenStore, the bucket relation catalog)
and its Handler / process_message request path. Requests never touch a socket: build_server() is constructed with the
listening-socket creation skipped (its TCPServer base initialised as BaseServer), and every request is a raw
HTTP/1.1 byte stream fed to the real Handler through an in-memory connection object. A urllib opener (scheme inproc://)
carries POST /mcp and GET /version, so ordinary MCP clients (urllib OpenerDirector) work unchanged.

Use:
    c = InProcFnMemoryCentre(root, checkout=..., pydeps=...)   # root holds state/, beehive.json, search.json
    c.provision(agent, path)                                   # one persistent token for agent on identity path
    c.start(); c.url == "inproc://centre/mcp"; c.opener(); c.tool(name, args); c.version()
    c.close(); c.reopen()                                      # restart on the same state dir
    c.catalog_path                                             # state/memory-buckets.sqlite3 (open read-only)

One runtime per state directory: close() before another process (or another InProcFnMemoryCentre) opens it.
Environment: MEMORY_* / FN_BEEHIVE_* / HUB_* are set in os.environ only while the centre is open (FN-Memory reads some of
them lazily) and restored by close(). Never point root at a production state directory.
"""
from __future__ import annotations

import contextlib
import email.message
import http.client
import io
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import urllib.response

FN_COMMIT = "30515c0a33e30224f92d979e1d36e244654afe3b"
_ENV_PREFIXES = ("MEMORY_", "FN_BEEHIVE_", "HUB_", "SN_MEMORY")
_ACTIVE = {}                                    # state dir -> open centre (one runtime per state dir in this process)


def _paths(checkout=None, pydeps=None):
    checkout = checkout or os.environ.get("PACTA_FN_MEMORY_CHECKOUT")
    pydeps = pydeps or os.environ.get("PACTA_FN_MEMORY_PYDEPS")
    if not checkout or not pydeps:
        raise RuntimeError("set PACTA_FN_MEMORY_CHECKOUT and PACTA_FN_MEMORY_PYDEPS (pinned FN-Memory checkout + offline deps)")
    return os.path.abspath(checkout), os.path.abspath(pydeps)


def available(checkout=None, pydeps=None) -> bool:
    try:
        checkout, pydeps = _paths(checkout, pydeps)
    except RuntimeError:
        return False
    return os.path.isdir(os.path.join(checkout, "space_neurons", "memory")) and os.path.isdir(os.path.join(pydeps, "numpy"))


@contextlib.contextmanager
def _no_listener(server_cls):
    """build_server() without a listening socket: for the duration, the TCPServer base of the centre's server class is
    initialised as its BaseServer (no socket created, bound or listened on). The classes are taken from the server class's
    own MRO, so this module opens no listener and imports no server module itself."""
    mro = {k.__name__: k for k in server_cls.__mro__}
    tcp, base = mro["TCPServer"], mro["BaseServer"]
    orig = tcp.__init__

    def init(self, server_address, handler_class, bind_and_activate=True):
        base.__init__(self, server_address, handler_class)
        self.socket = None
    tcp.__init__ = init
    try:
        yield
    finally:
        tcp.__init__ = orig


class _Conn:
    """The in-memory 'socket' the real Handler reads the request from and writes the response to."""

    def __init__(self, raw: bytes):
        self._in, self.out, self._timeout = raw, bytearray(), None

    def makefile(self, mode="rb", bufsize=-1):
        if "r" in mode:
            return io.BytesIO(self._in)
        return _Writer(self)

    def sendall(self, data):
        self.out += bytes(data)

    def settimeout(self, t):
        self._timeout = t

    def gettimeout(self):
        return self._timeout

    def setsockopt(self, *args):
        return None

    def getpeername(self):
        return ("127.0.0.1", 0)

    def shutdown(self, *args):
        return None

    def close(self):
        return None


class _Writer(io.RawIOBase):
    def __init__(self, conn):
        self._conn = conn

    def writable(self):
        return True

    def write(self, b):
        self._conn.sendall(b)
        return len(b)


def _parse_response(raw: bytes):
    head, _, body = raw.partition(b"\r\n\r\n")
    status_line, _, header_blob = head.partition(b"\r\n")
    parts = status_line.decode("iso-8859-1").split(" ", 2)
    status, reason = int(parts[1]), (parts[2] if len(parts) > 2 else "")
    headers = http.client.parse_headers(io.BytesIO(header_blob + b"\r\n\r\n"))
    if (headers.get("Transfer-Encoding") or "").lower() == "chunked":
        out, rest = bytearray(), body
        while rest:
            size_line, _, rest = rest.partition(b"\r\n")
            n = int(size_line.split(b";")[0].strip() or b"0", 16)
            if n == 0:
                break
            out += rest[:n]
            rest = rest[n + 2:]
        body = bytes(out)
    return status, reason, headers, body


class _InProcHandler(urllib.request.BaseHandler):
    """urllib handler for inproc:// URLs (any host): the path goes to the centre's real request handler."""

    def __init__(self, centre):
        self.centre = centre

    def inproc_open(self, req):
        path = urllib.parse.urlsplit(req.full_url)
        target = path.path + ("?" + path.query if path.query else "")
        headers = {k.title(): v for k, v in req.header_items()}
        status, reason, hdrs, body = self.centre.raw(req.get_method(), target, req.data, headers)
        if status >= 400:
            raise urllib.error.HTTPError(req.full_url, status, reason, hdrs, io.BytesIO(body))
        resp = urllib.response.addinfourl(io.BytesIO(body), hdrs, req.full_url, status)
        resp.msg = reason
        return resp


class InProcFnMemoryCentre:
    def __init__(self, root: str, checkout=None, pydeps=None, center="scratch"):
        self.root = os.path.abspath(root)
        if any(part.startswith("sn-memory") for part in self.root.split(os.sep)):     # production centre homes / state dirs
            raise RuntimeError("refusing a production memory path")
        self.checkout, self.pydeps = _paths(checkout, pydeps)
        self.state = os.path.join(self.root, "state")
        self.tmp = os.path.join(self.root, "tmp")
        self.center = center
        self.server, self.token, self.tokens, self.opens, self.requests = None, None, {}, 0, 0
        self._saved_env = None

    @classmethod
    def attach(cls, location: str, **kw):
        """inproc://<root or root/state>: an existing provisioned centre (beehive.json next to state/)."""
        p = os.path.abspath(location)
        root = p if os.path.exists(os.path.join(p, "beehive.json")) else os.path.dirname(p)
        if not os.path.exists(os.path.join(root, "beehive.json")) or not os.path.isdir(os.path.join(root, "state")):
            raise RuntimeError("not a provisioned in-process centre: " + location)
        return cls(root, **kw)

    # ------------------------------------------------------------ environment / imports
    def _import_path(self):
        for p in (self.pydeps, self.checkout):
            if p not in sys.path:
                sys.path.insert(0, p)
        sys.dont_write_bytecode = True

    def _env(self) -> dict:
        return {"MEMORY_STATE_DIR": self.state, "MEMORY_TOKENS_FILE": os.path.join(self.state, "tokens.json"),
                "MEMORY_HTTP_BIND": "127.0.0.1", "MEMORY_HTTP_PORT": "0", "MEMORY_FAKE_EMBED": "2048", "MEMORY_FAKE_EMBED_MODE": "bow",
                "MEMORY_RATE_CAPACITY": "100000", "MEMORY_RATE_REFILL_PER_SEC": "10000.0", "HUB_JOBS_DISABLE": "1",
                "HUB_REAPER_DISABLE": "1", "MEMORY_CENTER": self.center, "MEMORY_TEAM": "0", "MEMORY_RADIO_DISABLE": "1",
                "MEMORY_VERSION_FILE": os.path.join(self.root, "version.json"),
                "FN_BEEHIVE_CONFIG": os.path.join(self.root, "beehive.json"), "TMPDIR": self.tmp,
                "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": self.checkout}

    def _enter_env(self):
        if self._saved_env is None:
            self._saved_env = dict(os.environ)
            for k in [k for k in os.environ if k.startswith(_ENV_PREFIXES)]:
                del os.environ[k]
            os.environ.update(self._env())
            tempfile.tempdir = None              # re-read TMPDIR: tempfile caches the first one (maybe a removed centre's)

    def _restore_env(self):
        if self._saved_env is not None:
            os.environ.clear()
            os.environ.update(self._saved_env)
            self._saved_env = None
            tempfile.tempdir = None

    # ------------------------------------------------------------ provisioning
    def provision(self, agent: str, path: str, display_name="pacta graph scratch") -> str:
        """Create the state dir, the one-centre Beehive config (no routable peer) and one persistent token."""
        os.makedirs(self.state, exist_ok=True)
        os.makedirs(self.tmp, exist_ok=True)
        reg = os.path.join(self.root, "search.json")
        if not os.path.exists(reg):
            with open(reg, "w") as fh:
                json.dump({"version": 1, "revision": 1, "centres": {self.center: {"owner": self.center, "search": [],
                                                                                   "authorization_ref": "isolated scratch"}}}, fh)
        bee = os.path.join(self.root, "beehive.json")
        if not os.path.exists(bee):
            with open(bee, "w") as fh:
                json.dump({"centre_id": self.center, "peers": {}, "search_registry": reg, "issuer_endpoint": "http://127.0.0.1:1/mcp"}, fh)
        self.token = self.issue(agent, path, display_name)
        return self.token

    def issue(self, agent: str, path: str, display_name="pacta graph scratch") -> str:
        """Another persistent token (e.g. the same agent on a different identity path). The centre must be closed."""
        if self.server is not None:
            raise RuntimeError("issue tokens while the centre is closed")
        self._import_path()
        self._enter_env()
        try:
            from pathlib import Path
            from space_neurons.memory.auth import TokenStore
            from space_neurons.memory.registry import load_registry, new_record, write_registry
            root = Path(self.state)
            root.mkdir(parents=True, exist_ok=True)
            rec = load_registry(root, allow_new=True)
            rec.setdefault(agent, new_record("persistent"))
            write_registry(root, rec)
            tok = TokenStore(root / "tokens.json", registry_root=root).issue(agent, agent_class="persistent", path=path,
                                                                            metadata={"display_name": display_name})
        finally:
            self._restore_env()
        self.tokens[path] = tok
        return tok

    # ------------------------------------------------------------ lifecycle
    def start(self):
        if self.server is not None:
            return self
        if _ACTIVE.get(self.state) is not None:
            raise RuntimeError("another in-process runtime already holds this state dir")
        os.makedirs(self.tmp, exist_ok=True)
        self._import_path()
        self._enter_env()
        try:
            from space_neurons.memory import http_server
            with _no_listener(http_server.MemoryHTTPServer):
                srv = http_server.build_server()
        except BaseException:
            self._restore_env()
            raise
        srv.server_name, srv.server_port = "inproc", 0
        self.server, self._hs = srv, http_server
        self.opens += 1
        _ACTIVE[self.state] = self
        return self

    def close(self):
        srv, self.server = self.server, None
        try:
            if srv is not None:
                try:
                    if getattr(srv, "mu", None) is not None:
                        srv.mu.shutdown()
                        # The daemon leaves each agent session's daily event-log handle to process exit; an in-process
                        # centre that is closed and reopened releases them explicitly.
                        for sess in list(getattr(srv.mu, "_residents", {}).values()):
                            log = getattr(sess, "eventlog", None)
                            if log is not None and hasattr(log, "close"):
                                log.close()
                finally:
                    for name in ("hierarchy", "jobs"):
                        obj = getattr(srv, name, None)
                        if obj is not None and hasattr(obj, "close"):
                            obj.close()
        finally:
            _ACTIVE.pop(self.state, None)
            self._restore_env()

    def reopen(self):
        self.close()
        return self.start()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------ requests
    @property
    def url(self) -> str:
        return "inproc://centre/mcp"

    @property
    def catalog_path(self) -> str:
        return os.path.join(self.state, "memory-buckets.sqlite3")

    def raw(self, method: str, target: str, body: bytes | None, headers: dict):
        """One HTTP/1.1 request through the real Handler; -> (status, reason, headers, body)."""
        if self.server is None:
            raise urllib.error.URLError("in-process centre is closed")
        body = body or b""
        hdrs = {"Host": "127.0.0.1", "Connection": "close", **headers}
        if body or method in ("POST", "PUT"):
            hdrs["Content-Length"] = str(len(body))
        head = f"{method} {target} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in hdrs.items()) + "\r\n"
        conn = _Conn(head.encode("iso-8859-1") + body)
        self.requests += 1
        self._hs.Handler(conn, ("127.0.0.1", 0), self.server)
        return _parse_response(bytes(conn.out))

    def opener(self) -> urllib.request.OpenerDirector:
        op = urllib.request.OpenerDirector()
        op.add_handler(_InProcHandler(self))
        return op

    def http(self, method, path, body=None, token=None):
        data = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": "Bearer " + (token or self.token or ""), "Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        status, _, _, raw = self.raw(method, path, data, headers)
        return status, raw.decode("utf-8", "replace")

    def version(self) -> dict:
        st, body = self.http("GET", "/version")
        return json.loads(body) if st == 200 else {"status": st}

    def tool(self, name, args, token=None):
        st, body = self.http("POST", "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}, token)
        if body.lstrip().startswith(("event:", "data:")):
            body = next((l[5:].strip() for l in body.splitlines() if l.startswith("data:") and l[5:].strip()), "{}")
        msg = json.loads(body) if body.strip() else {"status": st}
        res = msg.get("result") or {}
        if isinstance(res.get("structuredContent"), dict):
            return res["structuredContent"]
        return json.loads((res.get("content") or [{}])[0].get("text") or "{}") if res else msg
