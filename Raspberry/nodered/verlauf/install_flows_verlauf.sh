#!/bin/bash
# Richtet die automatische Flow-Versionierung ein (systemd-Path-Unit, die bei
# jeder Änderung an nodered/data/flows.json flows_verlauf.sh startet).
# Wird von setup_iot_stack.sh und update_iot_stack.sh aufgerufen, kann aber
# auch einzeln laufen: sudo ./install_flows_verlauf.sh
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo." >&2
  exit 1
fi

TARGET_USER=${SUDO_USER:-root}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "${SCRIPT_DIR}/../data" && pwd)"
USER_HOME=$(eval echo "~${TARGET_USER}")
VERLAUF_DIR="${USER_HOME}/nodered-verlauf"

cat > /etc/systemd/system/nodered-verlauf.service <<EOF
[Unit]
Description=Node-RED-Flows im Verlauf sichern

[Service]
Type=oneshot
User=${TARGET_USER}
Environment=NODERED_DATA_DIR=${DATA_DIR}
Environment=FLOWS_VERLAUF_DIR=${VERLAUF_DIR}
ExecStart=/bin/bash ${SCRIPT_DIR}/flows_verlauf.sh
EOF

cat > /etc/systemd/system/nodered-verlauf.path <<EOF
[Unit]
Description=Node-RED-Deploys beobachten (flows.json)

[Path]
PathChanged=${DATA_DIR}/flows.json
Unit=nodered-verlauf.service

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now nodered-verlauf.path

# Ausgangsstand sofort sichern, damit der erste Schüler-Deploy einen
# Vergleich hat.
systemctl start nodered-verlauf.service
echo "[flows-verlauf] Aktiv, Verlauf liegt in ${VERLAUF_DIR}"
