# Mosquitto

Mosquitto ist der MQTT-Broker des IoT-Stacks. Er verteilt Audio- und PLC-Nachrichten an Subscriber und Historian Bridge.

Der Dienst wird ueber Docker Compose gestartet und verwendet die Ports `1883` sowie WebSockets auf `9001`.