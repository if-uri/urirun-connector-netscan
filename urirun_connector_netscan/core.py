# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# netscan:// connector — opt-in LAN discovery of urirun nodes. The mesh is explicit + key-enrolled
# by design (discover_mesh only refreshes ALREADY-configured nodes; there is deliberately no
# auto-discovery), so this is a user-triggered, read-only sweep: probe GET /health on every host
# of the local /24 at the node port and keep the ones that answer as a urirun node. It never
# connects/enrolls/trusts — it returns candidates for the user to ADD. Bounded (short per-host
# timeout + worker cap).
#
#   netscan://host/lan/query/nodes              → scan the local /24 for urirun nodes
#   netscan://host/host/query/probe?host=...    → probe one host's /health

from __future__ import annotations

import concurrent.futures
import json
import socket
import urllib.request
from typing import Any, Callable

import urirun

from . import _urirun_compat

CONNECTOR_ID = "netscan"
NETSCAN = _urirun_compat.connector(CONNECTOR_ID, scheme="netscan", target="host",
                           meta={"label": "LAN scan for urirun nodes"})

DEFAULT_NODE_PORT = 8765


def local_ipv4() -> str:
    """The host's primary LAN IPv4 (UDP egress-interface pick; no packets sent). Loopback on error."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def local_subnet24(ip: str | None = None) -> str:
    """The /24 the host sits on, e.g. 192.0.2.1 -> 192.0.2.0/24."""
    ip = ip or local_ipv4()
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        return "127.0.0.0/24"
    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"


def hosts_in_subnet(subnet: str) -> list[str]:
    """Usable host addresses of a /24 (.1 .. .254)."""
    base = subnet.rsplit("/", 1)[0].rsplit(".", 1)[0]
    return [f"{base}.{i}" for i in range(1, 255)]


def probe_health(host: str, port: int, timeout: float) -> dict[str, Any] | None:
    """GET http://host:port/health; return a node summary if it is a urirun node, else None."""
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001 - unreachable / non-HTTP host is simply "not a node"
        return None
    if not isinstance(data, dict) or not data.get("ok") or data.get("kind") != "node":
        return None
    return {"url": f"http://{host}:{port}", "host": host, "port": port,
            "name": data.get("name"), "version": data.get("version"),
            "routeCount": data.get("routeCount"), "execute": bool(data.get("execute"))}


def _sweep(targets: list[str], port: int, timeout: float, concurrency: int,
           probe: Callable[[str, int, float], dict | None]) -> list[dict]:
    workers = max(1, min(int(concurrency or 1), 256))
    found: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(probe, host, int(port), float(timeout)) for host in targets]
        for fut in concurrent.futures.as_completed(futures):
            try:
                res = fut.result()
            except Exception:  # noqa: BLE001 - one bad probe must not fail the sweep
                res = None
            if res:
                found.append(res)
    found.sort(key=lambda n: tuple(int(x) for x in str(n.get("host") or "0").split(".") if x.isdigit()))
    return found


# Test seam: tests inject a probe + hosts so the sweep runs without touching the network.
def scan_lan(port: int = DEFAULT_NODE_PORT, subnet: str | None = None, *, timeout: float = 0.6,
             concurrency: int = 64, hosts: list[str] | None = None,
             probe: Callable[[str, int, float], dict | None] | None = None) -> dict[str, Any]:
    subnet = subnet or local_subnet24()
    targets = hosts if hosts is not None else hosts_in_subnet(subnet)
    found = _sweep(targets, port, timeout, concurrency, probe or probe_health)
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "node-scan", "live": False,
            "subnet": subnet, "port": int(port), "scanned": len(targets), "found": len(found),
            "nodes": found}


@NETSCAN.handler("lan/query/nodes", isolated=True,
                 meta={"label": "Scan the local /24 for urirun nodes", "cliAlias": "nodes"})
def scan_nodes(port: int = DEFAULT_NODE_PORT, subnet: str = "", timeout: float = 0.6,
               concurrency: int = 64) -> dict[str, Any]:
    """Sweep the host's local /24 (or `subnet`) on `port` and return the urirun nodes that answer
    GET /health — read-only candidates for the user to add. Bounded by `timeout`/`concurrency`."""
    return scan_lan(port=port, subnet=subnet.strip() or None, timeout=timeout, concurrency=concurrency)


@NETSCAN.handler("host/query/probe", isolated=True,
                 meta={"label": "Probe one host's /health for a urirun node", "cliAlias": "probe"})
def probe(host: str = "", port: int = DEFAULT_NODE_PORT, timeout: float = 1.0) -> dict[str, Any]:
    """Probe a single host: is there a urirun node at http://host:port/health?"""
    host = (host or "").strip()
    if not host:
        return {"ok": False, "error": "host is required", "connector": CONNECTOR_ID}
    node = probe_health(host, int(port), float(timeout))
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "node-probe", "live": False,
            "host": host, "port": int(port), "isNode": node is not None, "node": node}

@NETSCAN.handler("netscan://host/doctor/query/report", isolated=True, meta={"label": "Connector readiness report"})
def doctor() -> dict[str, Any]:
    """Return a safe, read-only connector readiness report for CI smoke tests."""
    return {
        "ok": True,
        "connector": CONNECTOR_ID,
        "version": _connector_version(),
        "status": "ready",
    }


def _connector_version() -> str:
    try:
        from importlib.metadata import version

        return version("urirun-connector-netscan")
    except Exception:
        return "0.1.0"


def main(argv: list[str] | None = None) -> int:
    return NETSCAN.cli(argv, manifest_prose=_urirun_compat.load_manifest(__package__))


urirun_bindings = NETSCAN.bindings
