#!/bin/bash
# Richtet die tägliche Datensicherung um 17:00 ein (systemd-Timer
# datenkrake-backup.timer). Wird von setup_iot_stack.sh und
# update_iot_stack.sh aufgerufen, kann aber auch einzeln laufen:
#   sudo ./Raspberry/backup/install_datensicherung.sh
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > /etc/systemd/system/datenkrake-backup.service <<EOF
[Unit]
Description=Datenkrake-Datensicherung auf USB-Stick
After=docker.service

[Service]
Type=oneshot
ExecStart=/bin/bash ${SCRIPT_DIR}/datensicherung.sh
EOF

# Persistent=false: War der Pi um 17:00 aus, wird die Sicherung nicht beim
# nächsten Start (womöglich mitten im Unterricht) nachgeholt.
cat > /etc/systemd/system/datenkrake-backup.timer <<EOF
[Unit]
Description=Datenkrake-Datensicherung täglich um 17:00

[Timer]
OnCalendar=*-*-* 17:00:00
Persistent=false

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now datenkrake-backup.timer
echo "[datensicherung] Täglich um 17:00 eingerichtet (Stick mit Bezeichnung DATENKRAKE)."
