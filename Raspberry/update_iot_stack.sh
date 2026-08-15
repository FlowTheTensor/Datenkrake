#!/bin/bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo." >&2
  exit 1
fi

TARGET_USER=${SUDO_USER:-root}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/compose"
BACKUP_DIR="${SCRIPT_DIR}/backups/$(date +%Y%m%d-%H%M%S)"
SYNC_NODERED_FLOW=0

log() {
  echo "[update] $1"
}

usage() {
  cat <<EOF
Usage: sudo $0 [--sync-nodered-flow]

Updates container images, applies repeatable MariaDB schema updates and
refreshes the Node-RED input list. Existing data and active Node-RED flows
are preserved by default.

  --sync-nodered-flow  activate the repository's flows_nodesauswahl.json
                       after backing up the current Node-RED data directory
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sync-nodered-flow) SYNC_NODERED_FLOW=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [[ ! -f "${COMPOSE_DIR}/docker-compose.yml" ]]; then
  echo "Compose directory or file missing: ${COMPOSE_DIR}" >&2
  exit 1
fi

compose() {
  (cd "${COMPOSE_DIR}" && docker compose "$@")
}

backup_database() {
  mkdir -p "${BACKUP_DIR}"
  log "Creating MariaDB backup in ${BACKUP_DIR}"
  compose exec -T db mariadb-dump \
    --user=root --password=changeMeRoot \
    --single-transaction --routines --events --databases telemetry \
    > "${BACKUP_DIR}/telemetry.sql"
}

wait_for_database() {
  log "Waiting for MariaDB"
  for _ in {1..60}; do
    if compose exec -T db mariadb-admin \
      --user=root --password=changeMeRoot ping >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  echo "MariaDB did not become ready in time." >&2
  exit 1
}

apply_schema_updates() {
  log "Applying MariaDB schema updates"
  for migration in \
    "${SCRIPT_DIR}/mariadb/init/01-agentensystem.sql" \
    "${SCRIPT_DIR}/mariadb/init/02-plc-telemetry.sql"; do
    log "Applying $(basename "${migration}")"
    compose exec -T db mariadb \
      --user=root --password=changeMeRoot telemetry < "${migration}"
  done
}

backup_nodered_data() {
  mkdir -p "${BACKUP_DIR}"
  tar -C "${SCRIPT_DIR}/nodered" -czf "${BACKUP_DIR}/nodered-data.tar.gz" data
}

sync_nodered() {
  mkdir -p "${SCRIPT_DIR}/nodered/data"
  backup_nodered_data

  if [[ ${SYNC_NODERED_FLOW} -eq 1 ]]; then
    log "Replacing the active Node-RED flow"
    cp "${SCRIPT_DIR}/nodered/flows/flows_nodesauswahl.json" \
      "${SCRIPT_DIR}/nodered/data/flows.json"
  else
    log "Preserving the active Node-RED flow (use --sync-nodered-flow to replace it)"
  fi

  cp "${SCRIPT_DIR}/../UAExpertExport/NodesAuswahl.txt" \
    "${SCRIPT_DIR}/nodered/data/NodesAuswahl.txt"
  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/nodered"
}

log "Pulling/rebuilding images and recreating services"
compose pull historian grafana orange3
compose build --pull
compose up -d
wait_for_database
backup_database
apply_schema_updates
sync_nodered
compose restart nodered subscriber historian_bridge web

log "Update complete"
echo "Backup: ${BACKUP_DIR}"
echo "Check services with: cd ${COMPOSE_DIR} && docker compose ps"