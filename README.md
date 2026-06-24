# urirun-connector-netscan

**LAN scan for urirun nodes** — connector ekosystemu [ifURI / urirun](https://github.com/if-uri/urirun).
Schemat URI: `netscan://`

Opcjonalne, **read-only** wykrywanie węzłów urirun w sieci lokalnej. Mesh **świadomie nie wykrywa węzłów automatycznie** (`discover_mesh` tylko odświeża już skonfigurowane/enrolled węzły — bez mDNS/broadcast/sweepu, ze względów bezpieczeństwa i determinizmu). Ten connector to **jawny, wyzwalany przez użytkownika** skan: sonduje `GET /health` po lokalnej podsieci `/24` na porcie węzła i zwraca te hosty, które odpowiadają jako węzeł urirun — jako **kandydatów do dodania**. Nigdy nie łączy się, nie enrolluje ani nie ufa wykrytemu węzłowi.

## Trasy

- `netscan://host/lan/query/nodes` — skan lokalnej `/24` (lub `subnet`) na `port` (domyślnie 8765); zwraca `{subnet, scanned, found, nodes:[{url,host,name,version,routeCount}]}`. Otagowane `kind=node-scan, live=False` (zamrożony snapshot).
- `netscan://host/host/query/probe?host=192.168.188.201` — sprawdza jeden host.

Parametry skanu: `port` (8765), `subnet` (auto z IP hosta), `timeout` (0.6s/host), `concurrency` (64). Skan jest **ograniczony** (krótki timeout na host + limit wątków).

### Użycie

```bash
urirun-netscan nodes --port 8765
urirun-netscan probe --host 192.168.188.201
# albo przez URI (host dashboard reużywa tego przez /api/uri/invoke):
urirun run "netscan://host/lan/query/nodes"
```

W dashboardzie hosta: widok **Nodes → „🔎 Skanuj sieć (LAN)"** listuje wykryte węzły z przyciskiem **„dodaj"**, który wpina je w blok dodawania node'a; potem [urifix](https://github.com/if-uri/urirun-connector-urifix) rozwiązuje `node_url`.

## Wymagania

- **python:** `urirun`

## Instalacja (dev)

```bash
pip install -e .
pytest -q
```

## Powiązane

- Rdzeń: [if-uri/urirun](https://github.com/if-uri/urirun)
- Naprawa łańcuchów URI: [if-uri/urirun-connector-urifix](https://github.com/if-uri/urirun-connector-urifix)
- Hub connectorów: [connect.ifuri.com](https://connect.ifuri.com)

---
Kategoria: Networking · Słowa kluczowe: netscan, lan, scan, discovery, node, mesh · Wydawca: if-uri
