#!/bin/bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo." >&2
  exit 1
fi

TARGET_USER=${SUDO_USER:-root}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/compose"
NEED_RELOGIN=0

log() {
  echo "[setup] $1"
}

install_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker engine via get.docker.com convenience script"
    curl -fsSL https://get.docker.com | sh
  else
    log "Docker already installed"
  fi

  if ! docker compose version >/dev/null 2>&1; then
    log "Installing docker compose plugin"
    apt-get update
    apt-get install -y docker-compose-plugin
  else
    log "Docker Compose plugin already installed"
  fi

  if [[ ${TARGET_USER} != "root" ]] && ! id -nG "${TARGET_USER}" | grep -qw docker; then
    log "Adding ${TARGET_USER} to docker group"
    usermod -aG docker "${TARGET_USER}"
    NEED_RELOGIN=1
  fi
}

prepare_directories() {
  log "Ensuring local volume directories exist"
  mkdir -p "${SCRIPT_DIR}/mosquitto/data"
  mkdir -p "${SCRIPT_DIR}/mosquitto/log"
  mkdir -p "${SCRIPT_DIR}/mosquitto/config"
  mkdir -p "${SCRIPT_DIR}/mariadb/data"
  mkdir -p "${SCRIPT_DIR}/mariadb/init"
  mkdir -p "${SCRIPT_DIR}/historian/data"
  mkdir -p "${SCRIPT_DIR}/nodered/data"

  if [[ ! -f "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf" ]] && [[ -f "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf.example" ]]; then
    cp "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf.example" "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf"
  fi

  # Node-RED läuft mit --userDir /data (Bind-Mount) - eine ins Image kopierte
  # flows.json würde davon überdeckt. Die Vorlage deshalb hier einmalig an
  # den tatsächlichen userDir-Pfad kopieren, wenn dort noch keine existiert.
  if [[ ! -f "${SCRIPT_DIR}/nodered/data/flows.json" ]] && [[ -f "${SCRIPT_DIR}/nodered/flows/flows.json" ]]; then
    cp "${SCRIPT_DIR}/nodered/flows/flows.json" "${SCRIPT_DIR}/nodered/data/flows.json"
  fi

  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/mosquitto"
  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/mariadb"
  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/historian"
  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/nodered"
}

build_and_start() {
  if [[ ! -d "${COMPOSE_DIR}" ]] || [[ ! -f "${COMPOSE_DIR}/docker-compose.yml" ]]; then
    log "Compose directory or file missing; aborting"
    exit 1
  fi

  log "Building container images"
  (cd "${COMPOSE_DIR}" && docker compose build)

  log "Starting services in detached mode"
  (cd "${COMPOSE_DIR}" && docker compose up -d)
}

post_install_notes() {
  echo
  echo "MQTT broker, database and web server are starting via docker compose."
  echo "Next steps:"
  echo "  - Verify containers with: (cd ${COMPOSE_DIR} && docker compose ps)"
  echo "  - Access the web interface at: http://localhost:8080"
  if [[ ${NEED_RELOGIN} -eq 1 ]]; then
    echo "  - Log out and back in so ${TARGET_USER} can use docker without sudo."
  fi
}

setup_systemd_service() {
  log "Setting up systemd service for automatic container startup"
  local service_file="/etc/systemd/system/iot-stack.service"
  local user_home
  user_home=$(eval echo "~${TARGET_USER}")

  cat > "${service_file}" << EOF
[Unit]
Description=IoT Stack (MQTT, DB, Web)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${user_home}/Datenkrake-Container/compose
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable iot-stack.service
  log "Systemd service enabled for automatic startup"
}

install_docker
prepare_directories
build_and_start
post_install_notes