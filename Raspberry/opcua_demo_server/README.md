<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# OPC-UA-Demo-Server

Simuliert eine minimale OPC-UA-Gegenstelle für den Unterricht, falls keine
echte S7-1500/ET200SP im Netz erreichbar ist. Bietet genau einen Tag an:

- **Node-ID:** `ns=2;s=Station1.Zykluszeit`
- **Wert:** schwankt alle 3 Sekunden um 8.0 (Normalverteilung), springt in
  ca. 3 % der Fälle deutlich nach oben - gut geeignet, um dieselbe
  Anomalie-Erkennungslogik wie beim Akustik-Signal zu testen.

Läuft unter `opc.tcp://opcua-demo-server:4840/freeopcua/server/` im
Docker-Netz, von außerhalb unter `opc.tcp://datenkrake.local:4840/...`.

## Testen

Mit einem beliebigen OPC-UA-Client (z. B. dem kostenlosen
[UAExpert](https://www.unified-automation.com/products/development-tools/uaexpert.html))
verbinden und die Node-ID browsen, oder direkt mit Python:

```python
import asyncio
from asyncua import Client

async def main():
    async with Client(url="opc.tcp://datenkrake.local:4840/freeopcua/server/") as client:
        node = client.get_node("ns=2;s=Station1.Zykluszeit")
        print(await node.read_value())

asyncio.run(main())
```

## Ersetzt keine echte SPS-Anbindung

Dieser Server dient ausschließlich zum Testen der Node-RED-Flow-Mechanik
(`../nodered/`). Für den Anschluss an eine echte S7-1500/ET200SP diesen
Container einfach nicht starten und im Node-RED-Flow den Endpoint-Node
auf die reale Adresse umstellen.
