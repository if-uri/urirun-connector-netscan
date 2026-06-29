# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Route contracts for the netscan connector — LAN node discovery, read-only."""
from __future__ import annotations

from urirun_connectors_toolkit.contract_gate import Contract

_NODE_ITEM = {
    "url": "str",
    "host": "str",
    "port": "int",
    "name": "?str",
    "version": "?str",
    "routeCount": "?int",
    "execute": "?bool",
}

CONTRACTS: dict[str, Contract] = {
    "lan/query/nodes": Contract(
        version="v1",
        effect="query",
        reversible=False,
        inp={"port": "?int", "subnet": "?str", "timeout": "?num", "concurrency": "?int"},
        out={"ok": "bool", "subnet": "str", "port": "int",
             "scanned": "int", "found": "int", "nodes": [_NODE_ITEM]},
        errors=("precondition-unmet",),
        examples=(
            {
                "payload": {"port": 8765},
                "result": {
                    "ok": True,
                    "connector": "netscan",
                    "kind": "node-scan",
                    "live": False,
                    "subnet": "192.168.1.0/24",
                    "port": 8765,
                    "scanned": 254,
                    "found": 1,
                    "nodes": [{"url": "http://192.168.1.10:8765", "host": "192.168.1.10",
                                "port": 8765, "name": None, "version": "0.4.0",
                                "routeCount": 12, "execute": True}],
                },
            },
        ),
    ),
    "host/query/probe": Contract(
        version="v1",
        effect="query",
        reversible=False,
        inp={"host": "str", "port": "?int", "timeout": "?num"},
        out={"ok": "bool", "host": "?str", "port": "?int", "isNode": "?bool",
             "node": "?obj", "error": "?str"},
        errors=("precondition-unmet",),
        examples=(
            {
                "payload": {"host": "192.168.1.10", "port": 8765},
                "result": {
                    "ok": True,
                    "connector": "netscan",
                    "kind": "node-probe",
                    "live": False,
                    "host": "192.168.1.10",
                    "port": 8765,
                    "isNode": True,
                    "node": {"url": "http://192.168.1.10:8765", "host": "192.168.1.10",
                              "port": 8765, "name": None, "version": "0.4.0",
                              "routeCount": 12, "execute": True},
                },
            },
        ),
    ),
}
