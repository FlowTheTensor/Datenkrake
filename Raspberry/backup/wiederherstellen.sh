#!/bin/bash
# Spielt eine Datensicherung vom USB-Stick (Bezeichnung DATENKRAKE) zurück.
#
#   sudo ./Raspberry/backup/wiederherstellen.sh
#       Sicherungen auf dem Stick auflisten
#   sudo ./Raspberry/backup/wiederherstellen.sh <sicherung> [teil ...]
#       zurückspielen, z. B. 2026-10-24_1700, ohne Teil-Angabe alles.
#       Teile: mariadb influxdb forgejo grafana nodered verlauf
#
# Ordner (Forgejo, Grafana, Node-RED, Flow-Verlauf) werden vorher nicht
# gelöscht, sondern in <ordner>.vor-wiederherstellung-<zeit> umbenannt.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Bitte mit sudo ausführen." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RASPBERRY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_DIR="${RASPBERRY_DIR}/compose"
STICK_LABEL="${DATENKRAKE_STICK_LABEL:-DATENKRAKE}"
EIGENER_MOUNT=/mnt/datenkrake-backup
DB_ROOT_PASSWORT="${DATENKRAKE_DB_ROOT_PASSWORT:-changeMeRoot}"
INFLUX_TOKEN="${DATENKRAKE_INFLUX_TOKEN:-changeMeHistorianToken}"
BENUTZER="$(stat -c %U "${RASPBERRY_DIR}")"
BENUTZER_HOME="$(getent passwd "${BENUTZER}" | cut -d: -f6)"
ALLE_TEILE=(mariadb influxdb forgejo grafana nodered verlauf)
ZEIT="$(date +%Y%m%d-%H%M%S)"

log() {
  echo "[wiederherstellen] $*"
}

compose() {
  (cd "${COMPOSE_DIR}" && docker compose "$@")
}

GERAET="$(blkid -L "${STICK_LABEL}" 2>/dev/null || true)"
if [[ -z "${GERAET}" ]]; then
  echo "Kein USB-Stick mit der Bezeichnung ${STICK_LABEL} gefunden." >&2
  exit 1
fi
MOUNT="$(findmnt -n -o TARGET --source "${GERAET}" 2>/dev/null | head -n 1 || true)"
if [[ -z "${MOUNT}" ]]; then
  mkdir -p "${EIGENER_MOUNT}"
  mount "${GERAET}" "${EIGENER_MOUNT}"
  MOUNT="${EIGENER_MOUNT}"
  trap 'umount "${EIGENER_MOUNT}" 2>/dev/null || true' EXIT
fi
BASIS="${MOUNT}/datenkrake-backups"

if [[ $# -eq 0 ]]; then
  echo "Sicherungen auf dem Stick (neueste zuletzt):"
  for d in "${BASIS}"/20*; do
    [[ -d "${d}" ]] || continue
    echo "  $(basename "${d}")  $(sed -n 5p "${d}/info.txt" 2>/dev/null)"
  done
  echo
  echo "Zurückspielen: sudo $0 <sicherung> [${ALLE_TEILE[*]}]"
  exit 0
fi

QUELLE="${BASIS}/$1"
shift
if [[ ! -d "${QUELLE}" ]]; then
  echo "Sicherung nicht gefunden: ${QUELLE}" >&2
  exit 1
fi
TEILE=("$@")
(( ${#TEILE[@]} )) || TEILE=("${ALLE_TEILE[@]}")
for t in "${TEILE[@]}"; do
  [[ " ${ALLE_TEILE[*]} " == *" ${t} "* ]] || { echo "Unbekannter Teil: ${t}" >&2; exit 2; }
done

log "Prüfe die Prüfsummen …"
(cd "${QUELLE}" && sha256sum --quiet -c pruefsummen.sha256)
sed -n '1,5p' "${QUELLE}/info.txt"
echo
echo "Zurückgespielt wird: ${TEILE[*]}"
echo "Die aktuellen Daten dieser Teile werden ersetzt."
if [[ "${DATENKRAKE_OHNE_RUECKFRAGE:-0}" != 1 ]]; then
  read -rp "Fortfahren? Zum Bestätigen 'ja' eingeben: " antwort
  [[ "${antwort}" == "ja" ]] || { echo "Abgebrochen."; exit 1; }
fi

datei() {
  local f="${QUELLE}/$1"
  [[ -f "${f}" ]] || { echo "In dieser Sicherung fehlt $1" >&2; return 1; }
  echo "${f}"
}

# Ordner beiseitelegen und aus dem Archiv neu anlegen
ordner_ersetzen() {
  local basis="$1" ordner="$2" archiv="$3"
  if [[ -e "${basis}/${ordner}" ]]; then
    mv "${basis}/${ordner}" "${basis}/${ordner}.vor-wiederherstellung-${ZEIT}"
    log "Bisheriger Stand: ${basis}/${ordner}.vor-wiederherstellung-${ZEIT}"
  fi
  tar -xzf "${archiv}" -C "${basis}"
}

# Läuft in einem if, dort greift set -e nicht: jeder Schritt bricht explizit ab.
fuer_teil() {
  local t="$1" f container ok=0
  case "${t}" in
    mariadb)
      f="$(datei mariadb-telemetry.sql.gz)" || return 1
      gunzip -c "${f}" | compose exec -T db mariadb --user=root --password="${DB_ROOT_PASSWORT}"
      ;;
    influxdb)
      f="$(datei influxdb.tar.gz)" || return 1
      container="$(compose ps -q historian)"
      [[ -n "${container}" ]] || return 1
      docker exec "${container}" rm -rf /tmp/dk-backup
      gunzip -c "${f}" | docker cp - "${container}:/tmp/" || return 1
      # Optionen müssen beim influx-CLI vor dem Pfad stehen
      docker exec "${container}" influx restore --full -t "${INFLUX_TOKEN}" /tmp/dk-backup || ok=1
      docker exec "${container}" rm -rf /tmp/dk-backup
      compose restart historian historian_bridge >/dev/null
      return "${ok}"
      ;;
    forgejo|grafana|nodered)
      f="$(datei "${t}-data.tar.gz")" || return 1
      compose stop "${t}" >/dev/null 2>&1 || true
      ordner_ersetzen "${RASPBERRY_DIR}/${t}" data "${f}" || ok=1
      compose start "${t}" >/dev/null || ok=1
      return "${ok}"
      ;;
    verlauf)
      f="$(datei verlauf-und-zugang.tar.gz)" || return 1
      ordner_ersetzen "${BENUTZER_HOME}" nodered-verlauf "${f}" || return 1
      chown -R "${BENUTZER}:${BENUTZER}" "${BENUTZER_HOME}/nodered-verlauf" "${BENUTZER_HOME}/.config/datenkrake" 2>/dev/null || true
      ;;
  esac
}

FEHLER=()
for t in "${TEILE[@]}"; do
  log "Spiele ${t} zurück …"
  if ! fuer_teil "${t}"; then
    log "FEHLER bei ${t}"
    FEHLER+=("${t}")
  fi
done

if (( ${#FEHLER[@]} )); then
  log "Fertig mit Fehlern bei: ${FEHLER[*]}"
  exit 1
fi
log "Fertig. Bitte Weboberflächen prüfen (siehe README.md, Abschnitt Kontrolle)."
