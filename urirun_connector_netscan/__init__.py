"""netscan:// connector — opt-in, read-only LAN discovery of urirun nodes (the mesh has no
auto-discovery by design). Sweeps the local /24 on the node port and returns the nodes that
answer GET /health, as candidates for the user to add."""
from .core import (NETSCAN, DEFAULT_NODE_PORT, local_ipv4, local_subnet24, hosts_in_subnet,
                   probe_health, scan_lan, scan_nodes, probe, main, urirun_bindings)

__all__ = ["NETSCAN", "DEFAULT_NODE_PORT", "local_ipv4", "local_subnet24", "hosts_in_subnet",
           "probe_health", "scan_lan", "scan_nodes", "probe", "main", "urirun_bindings"]
