FROM nodered/node-red:3.1

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
RUN npm install node-red-contrib-opcua
