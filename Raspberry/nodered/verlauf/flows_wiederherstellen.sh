#!/bin/bash
# Zeigt den Flow-Verlauf oder spielt einen älteren Stand zurück.
#
#   ./flows_wiederherstellen.sh                    letzte 30 Deploys anzeigen
#   ./flows_wiederherstellen.sh <tab-datei>        Verlauf eines Tabs anzeigen
#   ./flows_wiederherstellen.sh <commit>           alle Tabs auf diesen Stand
#   ./flows_wiederherstellen.sh <commit> <tab-datei>
#                                                  nur diesen Tab zurücksetzen,
#                                                  alle anderen bleiben, wie sie sind
#
# <tab-datei> ist der Dateiname unter flows/, z. B. station-03-rohlager-dosen.json
# (Liste: ls ~/nodered-verlauf/flows). Zurückspielen überschreibt nichts
# endgültig: Der wiederhergestellte Stand wird als neuer Commit gesichert.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${NODERED_DATA_DIR:-${SCRIPT_DIR}/../data}"
VERLAUF_DIR="${FLOWS_VERLAUF_DIR:-${HOME}/nodered-verlauf}"
TABS="${SCRIPT_DIR}/flows_tabs.py"
ZIEL="${DATA_DIR}/flows.json"

if [[ ! -d "${VERLAUF_DIR}/.git" ]]; then
  echo "Kein Flow-Verlauf gefunden unter ${VERLAUF_DIR}" >&2
  exit 1
fi

log() {
  git -C "${VERLAUF_DIR}" log -n 30 --format='%h  %an  %ad%n    %b' --date=format:'%d.%m. %H:%M' "$@"
}

aktivieren() {
  mv "${ZIEL}.tmp" "${ZIEL}"
  docker restart nodered >/dev/null
  echo "$1 aktiviert, Node-RED neu gestartet."
}

if [[ $# -eq 0 ]]; then
  log
  echo "Zurückspielen mit: $0 <commit> [tab-datei]"
  exit 0
fi

if [[ $# -eq 1 && "$1" == *.json ]]; then
  log -- "flows/$1"
  exit 0
fi

stand="$1"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

if [[ $# -eq 2 ]]; then
  git -C "${VERLAUF_DIR}" show "${stand}:flows/$2" > "${tmp}/tab.json"
  python3 "${TABS}" ersetzen "${ZIEL}" "${tmp}/tab.json" > "${ZIEL}.tmp"
  aktivieren "Tab $2 im Stand ${stand}"
  exit 0
fi

if git -C "${VERLAUF_DIR}" cat-file -e "${stand}:flows" 2>/dev/null; then
  git -C "${VERLAUF_DIR}" archive "${stand}" flows | tar -x -C "${tmp}"
  python3 "${TABS}" zusammensetzen "${tmp}/flows" > "${ZIEL}.tmp"
else
  # Stand aus der Zeit, als flows.json noch als Ganzes gesichert wurde
  git -C "${VERLAUF_DIR}" show "${stand}:flows.json" > "${ZIEL}.tmp"
fi
aktivieren "Stand ${stand}"
