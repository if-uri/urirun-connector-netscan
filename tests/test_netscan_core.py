"""netscan connector: bindings + a bounded, read-only /health sweep (injected probe, so no real
network traffic in tests)."""
import urirun_connector_netscan.core as c


def test_bindings_valid():
    b = c.urirun_bindings()
    uris = set(b["bindings"])
    assert "netscan://host/lan/query/nodes" in uris
    assert "netscan://host/host/query/probe" in uris
    for spec in b["bindings"].values():
        assert spec["python"]["module"].endswith("core")
        assert spec["uri"].startswith("netscan://")


def test_local_subnet24():
    assert c.local_subnet24("192.168.188.201") == "192.168.188.0/24"
    assert c.local_subnet24("garbage") == "127.0.0.0/24"


def test_hosts_in_subnet():
    hosts = c.hosts_in_subnet("192.168.188.0/24")
    assert len(hosts) == 254 and hosts[0] == "192.168.188.1" and hosts[-1] == "192.168.188.254"


def test_scan_keeps_only_nodes_and_tags():
    def probe(host, port, timeout):
        if host == "192.168.188.201":
            return {"url": f"http://{host}:{port}", "host": host, "port": port,
                    "name": "laptop", "version": "0.4.96"}
        return None
    res = c.scan_lan(hosts=["192.168.188.5", "192.168.188.201"], probe=probe)
    assert res["ok"] and res["found"] == 1 and res["scanned"] == 2
    assert res["nodes"][0]["name"] == "laptop"
    assert res["kind"] == "node-scan" and res["live"] is False  # tagged as a frozen artifact


def test_scan_survives_probe_exceptions():
    def probe(host, port, timeout):
        if host.endswith(".7"):
            raise RuntimeError("boom")
        return {"host": host} if host.endswith(".201") else None
    res = c.scan_lan(hosts=["192.168.188.7", "192.168.188.201"], probe=probe)
    assert res["found"] == 1 and res["nodes"][0]["host"] == "192.168.188.201"


def test_probe_handler_requires_host():
    r = c.probe(host="")
    assert r["ok"] is False and "host is required" in r["error"]


def test_probe_health_filters_non_node(monkeypatch):
    import io, json as _json

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): self.close()

    monkeypatch.setattr(c.urllib.request, "urlopen",
                        lambda req, timeout=0: _Resp(_json.dumps({"ok": True, "name": "x"}).encode()))
    assert c.probe_health("1.2.3.4", 8765, 0.1) is None


def test_contract_output_shape() -> None:
    """probe() live output must satisfy the declared out-schema (no network needed)."""
    import importlib.util, sys
    sys.path.insert(0, "/home/tom/github/if-uri/urirun-contract")
    from urirun_connectors_toolkit.contract_gate import validate_output
    spec = importlib.util.spec_from_file_location(
        "contracts_netscan",
        "/home/tom/github/if-uri/urirun-connector-netscan/urirun_connector_netscan/contracts.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # probe an unreachable host — isNode=False, no network timeout (0.05s)
    result = c.probe(host="127.0.0.1", port=19999, timeout=0.05)
    validate_output(mod.CONTRACTS["host/query/probe"], result)
