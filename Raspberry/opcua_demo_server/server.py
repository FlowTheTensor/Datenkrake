"""
Simulierter OPC-UA-Server für den Unterricht, falls keine echte
S7-1500/ET200SP im Netz erreichbar ist. Bietet einen Tag
"Station1.Zykluszeit" an, der sich alle paar Sekunden ändert - passend
zum mitgelieferten Node-RED-Beispiel-Flow (../nodered/flows/flows.json).

Ersetzt KEINE echte SPS-Anbindung, sondern dient nur zum Testen der
Node-RED-Flow-Mechanik, bevor gegen eine echte Anlage gearbeitet wird.
"""
import asyncio
import logging
import random

from asyncua import Server, ua

logging.basicConfig(level=logging.WARNING)


async def main() -> None:
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("Datenkrake OPC-UA Demo-Server")

    uri = "http://datenkrake.local/opcua-demo"
    idx = await server.register_namespace(uri)

    station = await server.nodes.objects.add_object(idx, "Station1")
    zykluszeit = await station.add_variable(
        ua.NodeId("Station1.Zykluszeit", idx, ua.NodeIdType.String),
        "Zykluszeit",
        8.0,
        ua.VariantType.Double,
    )
    await zykluszeit.set_writable()

    print(f"Demo-OPC-UA-Server läuft auf {server.endpoint.geturl()}")
    print(f"Tag: ns={idx};s=Station1.Zykluszeit")

    async with server:
        while True:
            # Normale Schwankung um 8s, gelegentlich ein deutlicher
            # Ausreisser - zum Testen von Anomalie-Erkennung auf dieser
            # Datenquelle geeignet (analog zur Akustik-Anomalie).
            wert = round(random.gauss(8.0, 0.3), 2)
            if random.random() < 0.03:
                wert += random.uniform(4.0, 8.0)
            await zykluszeit.write_value(wert, ua.VariantType.Double)
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
