#!/bin/bash
# Sichert alle Arbeitsstände des Datenkrake-Stacks auf einen USB-Stick mit der
# Bezeichnung DATENKRAKE (siehe README.md in diesem Ordner).
#
#   sudo ./Raspberry/backup/datensicherung.sh              Stick bleibt eingehängt
#   sudo ./Raspberry/backup/datensicherung.sh --auswerfen  danach sicher abziehbar
#
# Automatisch täglich um 17:00 über datenkrake-backup.timer
# (einrichten: sudo ./Raspberry/backup/install_datensicherung.sh).
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Bitte mit sudo ausführen." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RASPBERRY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_DIR="${RASPBERRY_DIR}/compose"
STICK_LABEL="${DATENKRAKE_STICK_LABEL:-DATENKRAKE}"
BEHALTEN="${DATENKRAKE_BACKUPS_BEHALTEN:-20}"
MIN_FREI_MB=2048
EIGENER_MOUNT=/mnt/datenkrake-backup
DB_ROOT_PASSWORT="${DATENKRAKE_DB_ROOT_PASSWORT:-changeMeRoot}"
INFLUX_TOKEN="${DATENKRAKE_INFLUX_TOKEN:-changeMeHistorianToken}"
# Benutzer, dem das Repo gehört (dort liegen ~/nodered-verlauf und ~/.config/datenkrake)
BENUTZER="$(stat -c %U "${RASPBERRY_DIR}")"
BENUTZER_HOME="$(getent passwd "${BENUTZER}" | cut -d: -f6)"

AUSWERFEN=0
for arg in "$@"; do
  case "${arg}" in
    --auswerfen) AUSWERFEN=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: ${arg}" >&2; exit 2 ;;
  esac
done

log() {
  echo "[datensicherung] $*"
}

compose() {
  (cd "${COMPOSE_DIR}" && docker compose "$@")
}

# Nur eine Sicherung gleichzeitig (manuell und Timer könnten sich treffen)
exec 9>/run/datenkrake-backup.lock
if ! flock -n 9; then
  echo "Es läuft bereits eine Datensicherung." >&2
  exit 1
fi

# --- USB-Stick finden und einhängen ---------------------------------------
GERAET="$(blkid -L "${STICK_LABEL}" 2>/dev/null || true)"
if [[ -z "${GERAET}" ]]; then
  echo "Kein USB-Stick mit der Bezeichnung ${STICK_LABEL} gefunden. Bitte einstecken." >&2
  exit 1
fi
SELBST_EINGEHAENGT=0
MOUNT="$(findmnt -n -o TARGET --source "${GERAET}" 2>/dev/null | head -n 1 || true)"
if [[ -z "${MOUNT}" ]]; then
  mkdir -p "${EIGENER_MOUNT}"
  mount "${GERAET}" "${EIGENER_MOUNT}"
  MOUNT="${EIGENER_MOUNT}"
  SELBST_EINGEHAENGT=1
fi
ZIEL_BASIS="${MOUNT}/datenkrake-backups"
mkdir -p "${ZIEL_BASIS}"

frei_mb() {
  df -Pm "${MOUNT}" | awk 'NR == 2 { print $4 }'
}

# Älteste Sicherungen löschen: höchstens BEHALTEN Stück und genug freier Platz
aufraeumen() {
  rm -rf "${ZIEL_BASIS}"/*.unvollstaendig
  mapfile -t vorhanden < <(find "${ZIEL_BASIS}" -mindepth 1 -maxdepth 1 -type d -name '20*' | sort)
  local i=0
  while (( ${#vorhanden[@]} - i > BEHALTEN )) || (( $(frei_mb) < MIN_FREI_MB && ${#vorhanden[@]} - i > 1 )); do
    log "Lösche alte Sicherung $(basename "${vorhanden[$i]}")"
    rm -rf "${vorhanden[$i]}"
    i=$((i + 1))
  done
}

aufraeumen
if (( $(frei_mb) < MIN_FREI_MB )); then
  log "Warnung: Nur noch $(frei_mb) MB frei auf dem Stick."
fi

NAME="$(date +%Y-%m-%d_%H%M)"
ZIEL="${ZIEL_BASIS}/${NAME}.unvollstaendig"
rm -rf "${ZIEL}"
mkdir -p "${ZIEL}"
FEHLER=()

# --- Einzelne Teile --------------------------------------------------------
sichere_mariadb() {
  compose exec -T db mariadb-dump --user=root --password="${DB_ROOT_PASSWORT}" \
    --single-transaction --routines --events --databases telemetry \
    | gzip > "${ZIEL}/mariadb-telemetry.sql.gz"
}

sichere_influxdb() {
  local container
  container="$(compose ps -q historian)"
  [[ -n "${container}" ]] || return 1
  docker exec "${container}" rm -rf /tmp/dk-backup
  # Optionen müssen beim influx-CLI vor dem Pfad stehen
  docker exec "${container}" influx backup -t "${INFLUX_TOKEN}" /tmp/dk-backup >/dev/null 2>&1 || return 1
  docker cp "${container}:/tmp/dk-backup" - | gzip > "${ZIEL}/influxdb.tar.gz" || return 1
  docker exec "${container}" rm -rf /tmp/dk-backup
}

# Forgejo und Grafana speichern in SQLite. Für eine konsistente Kopie kurz anhalten.
sichere_forgejo_grafana() {
  compose stop forgejo grafana >/dev/null 2>&1 || true
  local ok=0
  tar -czf "${ZIEL}/forgejo-data.tar.gz" -C "${RASPBERRY_DIR}/forgejo" data || ok=1
  tar -czf "${ZIEL}/grafana-data.tar.gz" -C "${RASPBERRY_DIR}/grafana" data || ok=1
  compose start forgejo grafana >/dev/null 2>&1 || true
  return "${ok}"
}

sichere_nodered() {
  tar -czf "${ZIEL}/nodered-data.tar.gz" -C "${RASPBERRY_DIR}/nodered" --exclude='data/.npm' data
}

sichere_verlauf() {
  local teile=()
  [[ -d "${BENUTZER_HOME}/nodered-verlauf" ]] && teile+=(nodered-verlauf)
  [[ -d "${BENUTZER_HOME}/.config/datenkrake" ]] && teile+=(.config/datenkrake)
  (( ${#teile[@]} )) || return 0
  tar -czf "${ZIEL}/verlauf-und-zugang.tar.gz" -C "${BENUTZER_HOME}" "${teile[@]}"
}

teil() {
  local name="$1"
  shift
  log "Sichere ${name} …"
  if ! "$@"; then
    log "FEHLER beim Sichern von ${name}"
    FEHLER+=("${name}")
  fi
}

# Falls das Skript abbricht: Forgejo und Grafana auf keinen Fall gestoppt lassen
trap 'compose start forgejo grafana >/dev/null 2>&1 || true' EXIT

teil "MariaDB (Messdaten)" sichere_mariadb
teil "InfluxDB (Historian)" sichere_influxdb
teil "Forgejo und Grafana" sichere_forgejo_grafana
teil "Node-RED-Daten" sichere_nodered
teil "Flow-Verlauf" sichere_verlauf

{
  echo "Datenkrake-Datensicherung ${NAME}"
  echo "Rechner:   $(hostname)"
  echo "Repo-Stand: $(sudo -u "${BENUTZER}" git -C "${RASPBERRY_DIR}" rev-parse --short HEAD 2>/dev/null || echo unbekannt)"
  echo "Benutzer:  ${BENUTZER}"
  if (( ${#FEHLER[@]} )); then
    echo "UNVOLLSTÄNDIG, Fehler bei: ${FEHLER[*]}"
  else
    echo "Vollständig"
  fi
  echo "Repo-Pfad: ${RASPBERRY_DIR%/Raspberry}"
  echo
  du -h "${ZIEL}"/*.gz 2>/dev/null | sed "s#${ZIEL}/##"
} > "${ZIEL}/info.txt"
(cd "${ZIEL}" && sha256sum ./*.gz > pruefsummen.sha256)

ENDNAME="${NAME}"
(( ${#FEHLER[@]} )) && ENDNAME="${NAME}_teilweise"
# Zwei Sicherungen in derselben Minute: Nummer anhängen statt hineinzuschieben
if [[ -e "${ZIEL_BASIS}/${ENDNAME}" ]]; then
  n=2
  while [[ -e "${ZIEL_BASIS}/${ENDNAME}-${n}" ]]; do n=$((n + 1)); done
  ENDNAME="${ENDNAME}-${n}"
fi
mv "${ZIEL}" "${ZIEL_BASIS}/${ENDNAME}"
sync
aufraeumen
log "Gesichert nach ${ZIEL_BASIS}/${ENDNAME} ($(du -sh "${ZIEL_BASIS}/${ENDNAME}" | cut -f1)), noch $(frei_mb) MB frei."

if (( AUSWERFEN )); then
  umount "${MOUNT}"
  log "Stick ausgehängt, er kann jetzt abgezogen werden."
elif (( SELBST_EINGEHAENGT )); then
  umount "${MOUNT}"
fi

if (( ${#FEHLER[@]} )); then
  log "Sicherung UNVOLLSTÄNDIG, Fehler bei: ${FEHLER[*]}"
  exit 1
fi
log "Sicherung vollständig."
