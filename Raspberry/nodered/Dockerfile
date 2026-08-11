FROM nodered/node-red:5.0.4

# node-red-contrib-opcua bringt die OPC-UA-Client-Nodes mit, die den
# eigentlichen Client stellt (S7-1500/ET200SP oder opcua_demo_server
# als Server). MQTT-Publish nutzt die in Node-RED eingebauten mqtt-Nodes,
# braucht kein zusätzliches Paket.
#
# WICHTIG: Node-RED läuft mit --userDir /data (siehe offizielles
# node-red-docker-Repo). Da /data in docker-compose.yml als Bind-Mount
# vom Host eingebunden ist, würde eine hier per COPY ins Image gelegte
# flows.json beim Start vom leeren Host-Ordner überdeckt und nie geladen.
# Die Vorlage liegt deshalb NICHT hier im Image, sondern wird von
# setup_iot_stack.sh einmalig nach ../nodered/data/flows.json kopiert -
# genau wie mosquitto.conf.example dort bereits gehandhabt wird.
# node-opcua-debug verwendet intern noch CommonJS require() auf hexy.
# Neuere hexy-Versionen sind ESM-only und brechen mit ERR_REQUIRE_ESM.
# Deshalb hexy per npm override auf eine CJS-kompatible Version festpinnen.
RUN npm pkg set overrides.hexy=0.3.3 \
 && npm install --no-audit --no-fund node-red-contrib-opcua@0.2.354
