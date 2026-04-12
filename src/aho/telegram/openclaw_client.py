"""OpenClaw Unix socket client for Telegram inbound bridge.

Speaks the existing openclaw JSON protocol: one line JSON in, one line JSON out.
Supports sync wait with configurable timeout and async ack fallback.
"""
import json
import socket
from pathlib import Path

OPENCLAW_SOCK = Path.home() / ".local/share/aho/openclaw.sock"


def send_chat(message: str, timeout: float = 30.0, role: str = "assistant") -> dict:
    """Send a chat message to openclaw and wait for response.

    Returns dict with keys:
        ok: bool
        response: str (if ok)
        error: str (if not ok)
        timed_out: bool
    """
    if not OPENCLAW_SOCK.exists():
        return {"ok": False, "error": "openclaw socket not found", "timed_out": False}

    req = json.dumps({"cmd": "chat", "message": message, "role": role}) + "\n"

    sock = None
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(OPENCLAW_SOCK))
        sock.sendall(req.encode("utf-8"))

        # Use makefile for reliable line-buffered reading with timeout
        sock.settimeout(timeout)
        fobj = sock.makefile("rb")
        line = fobj.readline()
        fobj.close()

        if not line.strip():
            return {"ok": False, "error": "empty response from openclaw", "timed_out": False}

        resp = json.loads(line.decode("utf-8").strip())
        return {**resp, "timed_out": False}

    except socket.timeout:
        return {"ok": False, "error": "openclaw timeout", "timed_out": True}
    except ConnectionRefusedError:
        return {"ok": False, "error": "openclaw not running", "timed_out": False}
    except Exception as e:
        return {"ok": False, "error": str(e), "timed_out": False}
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def get_status() -> dict:
    """Query openclaw status."""
    if not OPENCLAW_SOCK.exists():
        return {"ok": False, "error": "openclaw socket not found"}

    req = json.dumps({"cmd": "status"}) + "\n"
    sock = None
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(OPENCLAW_SOCK))
        sock.sendall(req.encode("utf-8"))

        sock.settimeout(5.0)
        fobj = sock.makefile("rb")
        line = fobj.readline()
        fobj.close()

        return json.loads(line.decode("utf-8").strip())
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass
