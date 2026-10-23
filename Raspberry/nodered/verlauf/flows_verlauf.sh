#!/bin/bash
# Sichert die aktive Node-RED-Flow-Datei bei jedem Deploy in einem eigenen,
# lokalen Git-Repo (Standard: ~/nodered-verlauf). Dieses Repo ist bewusst vom
# Datenkrake-Repo getrennt: Die Schüler ändern nur Flows, der Verlauf landet
# nie automatisch auf GitHub.
#
# Jeder Tab liegt als eigene Datei unter flows/ und bekommt eigene Commits,
# mit dem Tab-Namen als Autor (z. B. "Station 03 Rohlager Dosen"). So hat
# jedes Stationsteam seinen eigenen Verlauf, obwohl alle im selben Node-RED
# arbeiten.
#
# Ausgelöst von der systemd-Path-Unit nodered-verlauf.path, sobald Node-RED
# data/flows.json neu schreibt (also bei jedem Deploy im Editor).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${NODERED_DATA_DIR:-${SCRIPT_DIR}/../data}"
VERLAUF_DIR="${FLOWS_VERLAUF_DIR:-${HOME}/nodered-verlauf}"
QUELLE="${DATA_DIR}/flows.json"
TABS="${SCRIPT_DIR}/flows_tabs.py"

if [[ ! -f "${QUELLE}" ]]; then
  echo "Keine Flow-Datei gefunden: ${QUELLE}" >&2
  exit 1
fi

if [[ ! -d "${VERLAUF_DIR}/.git" ]]; then
  mkdir -p "${VERLAUF_DIR}"
  git -C "${VERLAUF_DIR}" init -q -b main
  git -C "${VERLAUF_DIR}" config user.name "Node-RED-Verlauf"
  git -C "${VERLAUF_DIR}" config user.email "nodered@datenkrake.local"
fi

# Node-RED schreibt beim Deploy flows.json und die Sicherungskopie kurz
# nacheinander - abwarten, bis der Schreibvorgang sicher abgeschlossen ist.
sleep 2

# Ältere Verläufe speicherten die ganze flows.json in einer Datei.
if git -C "${VERLAUF_DIR}" ls-files --error-unmatch flows.json >/dev/null 2>&1; then
  git -C "${VERLAUF_DIR}" rm -q flows.json
fi

# Als Variable statt Prozess-Substitution, damit ein Fehler (unlesbare
# flows.json) das Skript abbricht, bevor etwas committet wird.
tabliste="$(python3 "${TABS}" aufteilen "${QUELLE}" "${VERLAUF_DIR}/flows")"
declare -A LABEL
while IFS=$'\t' read -r datei label; do
  LABEL["flows/${datei}"]="${label}"
done <<< "${tabliste}"

git -C "${VERLAUF_DIR}" add -A flows
zeitpunkt="$(date '+%Y-%m-%d %H:%M:%S')"
alt="$(mktemp)"
trap 'rm -f "${alt}"' EXIT

# Ein Commit pro geändertem Tab, damit jeder Tab seinen eigenen Verlauf hat.
while IFS= read -r pfad; do
  [[ "${pfad}" == "flows/_konfiguration.json" ]] && continue
  label="${LABEL[${pfad}]:-$(basename "${pfad}" .json)}"
  autor_mail="$(basename "${pfad}" .json)@datenkrake.local"
  git -C "${VERLAUF_DIR}" show "HEAD:${pfad}" > "${alt}" 2>/dev/null || : > "${alt}"
  aenderung="$(python3 "${TABS}" vergleich "${alt}" "${VERLAUF_DIR}/${pfad}" || true)"
  git -C "${VERLAUF_DIR}" commit -q \
    --author "${label} <${autor_mail}>" \
    -m "${label}: Deploy ${zeitpunkt}" -m "${aenderung}" -- "${pfad}"
done < <(git -C "${VERLAUF_DIR}" diff --cached --name-only -- flows)

# Rest (Konfigurations-Nodes, Tab-Reihenfolge, entfernte flows.json)
if ! git -C "${VERLAUF_DIR}" diff --cached --quiet; then
  git -C "${VERLAUF_DIR}" commit -q -m "Konfiguration: Deploy ${zeitpunkt}"
fi

# Ist ein Remote "origin" eingerichtet (Forgejo-Repo datenkrake-projekt, siehe
# Raspberry/forgejo/README.md), dort veröffentlichen. Fehler brechen nichts ab.
if git -C "${VERLAUF_DIR}" remote get-url origin >/dev/null 2>&1; then
  git -C "${VERLAUF_DIR}" push -q origin HEAD:main \
    || echo "Push des Flow-Verlaufs fehlgeschlagen, lokal ist alles gesichert." >&2
fi
