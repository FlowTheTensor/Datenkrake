#!/bin/bash
# Richtet Forgejo für das agile Arbeiten im Unterricht ein. Auf dem Raspberry
# als normaler Benutzer mit Docker-Rechten ausführen (kein sudo).
#
#   ./forgejo_einrichten.sh lehrkraft <benutzer>
#       Admin-Konto für die Lehrkraft anlegen, das Passwort wird abgefragt.
#
#   ./forgejo_einrichten.sh projekt <lehrkraft>
#       Repo "datenkrake-projekt" anlegen (Backlog, Kanban-Board und
#       Node-RED-Deploy-Verlauf), Labels, Issue-Vorlagen und Branchschutz
#       einrichten und ~/nodered-verlauf damit verbinden.
#
#   ./forgejo_einrichten.sh schueler <datei> <lehrkraft>
#       Pro Zeile der Datei (ein Benutzername, # = Kommentar) ein Konto anlegen
#       und ins Projekt-Repo aufnehmen. Zugangsdaten: konten-<datum>.csv
#
# Alle Schritte können gefahrlos wiederholt werden.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API="http://localhost:3001/api/v1"
REPO="datenkrake-projekt"
VERLAUF_DIR="${FLOWS_VERLAUF_DIR:-${HOME}/nodered-verlauf}"
TOKEN_DATEI="${HOME}/.config/datenkrake/forgejo-token"

forgejo() {
  docker exec -u git forgejo forgejo "$@"
}

passwort() {
  head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | cut -c1-12
}

# Zugriffstoken der Lehrkraft für die API, wird einmalig erzeugt.
token() {
  local lehrkraft="$1"
  if [[ ! -s "${TOKEN_DATEI}" ]]; then
    mkdir -p "$(dirname "${TOKEN_DATEI}")"
    forgejo admin user generate-access-token \
      --username "${lehrkraft}" \
      --token-name "datenkrake-skripte-$(date +%s)" \
      --scopes "write:repository,write:issue,write:user" \
      --raw > "${TOKEN_DATEI}"
    chmod 600 "${TOKEN_DATEI}"
  fi
  cat "${TOKEN_DATEI}"
}

api() {
  curl -fsS -H "Authorization: token ${TOKEN}" -H "Content-Type: application/json" "$@"
}

# Die Lehrkraft wählt ihr Passwort selbst. Ein erzwungener Passwortwechsel
# würde die API für die weiteren Schritte sperren, bis man sich im Browser
# angemeldet hat.
lehrkraft_anlegen() {
  local name="$1" pw pw2
  read -rsp "Passwort für ${name} (mind. 8 Zeichen): " pw; echo
  read -rsp "Passwort wiederholen: " pw2; echo
  if [[ "${pw}" != "${pw2}" || ${#pw} -lt 8 ]]; then
    echo "Passwörter stimmen nicht überein oder sind zu kurz." >&2
    exit 1
  fi
  forgejo admin user create --admin \
    --username "${name}" --email "${name}@datenkrake.local" \
    --password "${pw}" --must-change-password=false
  echo "Konto ${name} angelegt: http://datenkrake.local:3001"
}

labels_anlegen() {
  local lehrkraft="$1" vorhanden
  vorhanden="$(api "${API}/repos/${lehrkraft}/${REPO}/labels?limit=50")"
  while IFS=';' read -r name farbe beschreibung; do
    if grep -q "\"name\":\"${name}\"" <<< "${vorhanden}"; then
      continue
    fi
    # Labels mit "/" sind exklusiv: Ein Issue gehört zu genau einer Station.
    local exklusiv=false
    [[ "${name}" == */* ]] && exklusiv=true
    api -X POST "${API}/repos/${lehrkraft}/${REPO}/labels" \
      -d "{\"name\":\"${name}\",\"color\":\"#${farbe}\",\"description\":\"${beschreibung}\",\"exclusive\":${exklusiv}}" >/dev/null
    echo "Label ${name} angelegt"
  done <<'EOF'
story;2a5f8a;Neue Funktion aus Sicht der Nutzer
bug;c81e3a;Etwas funktioniert nicht wie erwartet
opc-ua;6b4e71;OPC-UA-Abfrage der SPS-Stationen
node-red;b87a1c;Flows im Node-RED-Editor
grafana;2f6b4f;Dashboards und Auswertung
doku;5b5852;Dokumentation und Erklärungen
blockiert;e0a100;Team kommt ohne Hilfe nicht weiter
station/01-leitstand;2b7a78;Stationsteam 01 Leitstand
station/02-palettenlager1;2b7a78;Stationsteam 02 Palettenlager1
station/03-rohlager-dosen;2b7a78;Stationsteam 03 Rohlager Dosen
station/04-abfuellen;2b7a78;Stationsteam 04 Abfüllen
station/05-qualitaet-kamera;2b7a78;Stationsteam 05 Qualität Kamera
station/06-handling-saugarm;2b7a78;Stationsteam 06 Handling Saugarm
station/07-presse;2b7a78;Stationsteam 07 Presse
station/08-palettenlager2;2b7a78;Stationsteam 08 Palettenlager2
station/09-transfersystem-roboter;2b7a78;Stationsteam 09 Transfersystem Roboter
EOF
}

projekt_anlegen() {
  local lehrkraft="$1"
  TOKEN="$(token "${lehrkraft}")"

  if ! api "${API}/repos/${lehrkraft}/${REPO}" >/dev/null 2>&1; then
    api -X POST "${API}/user/repos" -d "{\"name\":\"${REPO}\",\"private\":true,\"default_branch\":\"main\",\"description\":\"Backlog, Kanban-Board und Node-RED-Deploy-Verlauf\"}" >/dev/null
    echo "Repo ${lehrkraft}/${REPO} angelegt"
  fi
  labels_anlegen "${lehrkraft}"

  if [[ ! -d "${VERLAUF_DIR}/.git" ]]; then
    echo "Kein Flow-Verlauf unter ${VERLAUF_DIR}." >&2
    echo "Zuerst: sudo ./Raspberry/nodered/verlauf/install_flows_verlauf.sh" >&2
    exit 1
  fi

  # Issue-Vorlagen liegen im Verlauf-Repo, damit Forgejo sie anbietet.
  mkdir -p "${VERLAUF_DIR}/.forgejo/issue_template"
  cp "${SCRIPT_DIR}"/vorlagen/issue_template/*.md "${VERLAUF_DIR}/.forgejo/issue_template/"
  git -C "${VERLAUF_DIR}" add .forgejo
  if ! git -C "${VERLAUF_DIR}" diff --cached --quiet; then
    git -C "${VERLAUF_DIR}" commit -q -m "Issue-Vorlagen aktualisiert"
  fi

  local url="http://${lehrkraft}:${TOKEN}@localhost:3001/${lehrkraft}/${REPO}.git"
  if git -C "${VERLAUF_DIR}" remote get-url origin >/dev/null 2>&1; then
    git -C "${VERLAUF_DIR}" remote set-url origin "${url}"
  else
    git -C "${VERLAUF_DIR}" remote add origin "${url}"
  fi
  git -C "${VERLAUF_DIR}" push -q origin HEAD:main
  echo "Flow-Verlauf nach ${REPO} übertragen"

  # Nur der Verlauf-Dienst (mit dem Token der Lehrkraft) darf auf main pushen,
  # Schüler arbeiten ausschließlich mit Issues und Board.
  if ! api "${API}/repos/${lehrkraft}/${REPO}/branch_protections/main" >/dev/null 2>&1; then
    api -X POST "${API}/repos/${lehrkraft}/${REPO}/branch_protections" \
      -d "{\"rule_name\":\"main\",\"enable_push\":true,\"enable_push_whitelist\":true,\"push_whitelist_usernames\":[\"${lehrkraft}\"]}" >/dev/null
    echo "Branchschutz für main eingerichtet"
  fi
  echo "Fertig: http://datenkrake.local:3001/${lehrkraft}/${REPO}"
}

schueler_anlegen() {
  local datei="$1" lehrkraft="$2" csv name pw ausgabe
  TOKEN="$(token "${lehrkraft}")"
  csv="${SCRIPT_DIR}/konten-$(date +%Y%m%d-%H%M%S).csv"
  echo "benutzer;startpasswort" > "${csv}"
  chmod 600 "${csv}"

  while read -r name || [[ -n "${name}" ]]; do
    name="$(tr -d '\r' <<< "${name}" | tr '[:upper:]' '[:lower:]')"
    [[ -z "${name}" || "${name}" == \#* ]] && continue
    if [[ ! "${name}" =~ ^[a-z0-9._-]+$ ]]; then
      echo "Übersprungen (nur a-z, 0-9, . _ - erlaubt): ${name}" >&2
      continue
    fi

    pw="$(passwort)"
    if ausgabe="$(forgejo admin user create --username "${name}" \
        --email "${name}@schueler.datenkrake.local" \
        --password "${pw}" --must-change-password 2>&1)"; then
      echo "${name};${pw}" >> "${csv}"
      echo "Konto ${name} angelegt"
    elif grep -qi "already exists" <<< "${ausgabe}"; then
      echo "Konto ${name} existiert bereits, Passwort unverändert"
    else
      echo "Konto ${name} nicht angelegt: ${ausgabe}" >&2
      continue
    fi

    api -X PUT "${API}/repos/${lehrkraft}/${REPO}/collaborators/${name}" \
      -d '{"permission":"write"}' >/dev/null
  done < "${datei}"

  if [[ $(wc -l < "${csv}") -le 1 ]]; then
    rm -f "${csv}"
    echo "Keine neuen Konten angelegt."
  else
    echo "Zugangsdaten: ${csv} (ausdrucken/verteilen, danach löschen)"
  fi
}

case "${1:-}" in
  lehrkraft) [[ $# -eq 2 ]] || { sed -n '2,20p' "$0"; exit 2; }; lehrkraft_anlegen "$2" ;;
  projekt)   [[ $# -eq 2 ]] || { sed -n '2,20p' "$0"; exit 2; }; projekt_anlegen "$2" ;;
  schueler)  [[ $# -eq 3 ]] || { sed -n '2,20p' "$0"; exit 2; }; schueler_anlegen "$2" "$3" ;;
  *) sed -n '2,20p' "$0"; exit 2 ;;
esac
