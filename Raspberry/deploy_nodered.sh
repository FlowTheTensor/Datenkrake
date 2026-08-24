#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Deploy-Skript fuer den Node-RED-Flow "flows_nodesauswahl.json"
#
# Zweck: Holt Aenderungen aus dem Git-Repo und kopiert die aktuelle
#        Flow-Datei in den Ordner, der tatsaechlich per Bind-Mount
#        (../nodered/data:/data) in den Container eingehaengt ist.
#        Ein reiner "git pull" oder "docker compose build" reicht NICHT,
#        weil Node-RED die Datei aus dem gemounteten Host-Ordner liest,
#        nicht aus dem, was im Image liegt.
#
# Ablageort: am besten direkt neben der docker-compose.yml, also z.B.
#            unter Raspberry/deploy_nodered.sh
#            (Pfade unten ggf. anpassen, falls die Struktur abweicht)
# ---------------------------------------------------------------------------

# --- Anpassbare Variablen -----------------------------------------------

# Ordner, in dem diese docker-compose.yml liegt (Skript wird von dort aus gedacht)
COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Name des Docker-Compose-Service (siehe docker-compose.yml: "nodered:")
SERVICE_NAME="nodered"

# Quelle: die "gepflegte" Flow-Datei im Repo
SRC_FLOW_FILE="${COMPOSE_DIR}/nodered/flows/flows_nodesauswahl.json"

# Ziel: die Datei, die Node-RED tatsaechlich aus /data laedt.
# WICHTIG: Dateiname muss zum "flowFile"-Eintrag in settings.js passen!
# Falls dort z.B. "flows.json" konfiguriert ist, hier entsprechend anpassen.
DEST_FLOW_FILE="${COMPOSE_DIR}/nodered/data/flows_nodesauswahl.json"

# --- Ablauf ---------------------------------------------------------------

echo "==> Wechsle ins Repo-Verzeichnis: ${COMPOSE_DIR}"
cd "${COMPOSE_DIR}"

echo "==> Hole Aenderungen aus Git"
git pull

if [ ! -f "${SRC_FLOW_FILE}" ]; then
    echo "FEHLER: Quelldatei nicht gefunden: ${SRC_FLOW_FILE}"
    echo "Bitte Pfad im Skript pruefen/anpassen."
    exit 1
fi

echo "==> Kopiere Flow-Datei nach data/"
echo "    ${SRC_FLOW_FILE}"
echo " -> ${DEST_FLOW_FILE}"
cp "${SRC_FLOW_FILE}" "${DEST_FLOW_FILE}"

echo "==> Starte Node-RED-Container neu"
docker compose restart "${SERVICE_NAME}"

echo "==> Fertig. Kurz warten und Logs pruefen:"
sleep 3
docker compose logs --tail 50 "${SERVICE_NAME}"
