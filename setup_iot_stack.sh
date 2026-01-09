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

  if ! command -v mosquitto_passwd >/dev/null 2>&1; then
    log "Installing Mosquitto clients for password management"
    apt-get install -y mosquitto-clients
  else
    log "Mosquitto clients already installed"
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

  if [[ ! -f "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf" ]] && [[ -f "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf.example" ]]; then
    cp "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf.example" "${SCRIPT_DIR}/mosquitto/config/mosquitto.conf"
  fi

  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/mosquitto"
  chown -R "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/mariadb"
}

create_mqtt_password() {
  if [[ ! -f "${SCRIPT_DIR}/mosquitto/config/passwd" ]]; then
    log "Creating MQTT password file"
    mkdir -p "${SCRIPT_DIR}/mosquitto/config"
    read -p "Enter MQTT username: " mqtt_user
    read -s -p "Enter MQTT password: " mqtt_pass
    echo
    mosquitto_passwd -b "${SCRIPT_DIR}/mosquitto/config/passwd" "${mqtt_user}" "${mqtt_pass}"
    chown "${TARGET_USER}:${TARGET_USER}" "${SCRIPT_DIR}/mosquitto/config/passwd"
  else
    log "MQTT password file already exists"
  fi
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

install_docker
prepare_directories
create_mqtt_password
build_and_start
post_install_notes