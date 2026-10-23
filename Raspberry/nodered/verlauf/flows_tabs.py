"""Zerlegt eine Node-RED-flows.json in eine Datei pro Tab und setzt sie wieder
zusammen. Grundlage für den Flow-Verlauf: Jeder Stations-Tab bekommt so seine
eigene Datei und eigene Commits.

  python3 flows_tabs.py aufteilen <flows.json> <ordner>
      schreibt <ordner>/<tab>.json pro Tab bzw. Subflow und
      <ordner>/_konfiguration.json (Konfigurations-Nodes + Tab-Reihenfolge),
      entfernt Dateien gelöschter Tabs. Ausgabe pro Datei: <datei> TAB <label>
  python3 flows_tabs.py vergleich <alt.json> <neu.json>
      Zusammenfassung "+neu / -gelöscht / ~geändert Nodes" für eine Tab-Datei
  python3 flows_tabs.py zusammensetzen <ordner>
      gibt die vollständige flows.json auf stdout aus
  python3 flows_tabs.py ersetzen <flows.json> <tab.json>
      ersetzt einen Tab in flows.json durch den Stand aus <tab.json>
"""
import json
import re
import sys
from pathlib import Path

KONFIG = "_konfiguration.json"


def laden(pfad):
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def speichern(pfad, daten):
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)
        f.write("\n")


def dateiname(label, vergeben):
    name = label.lower()
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        name = name.replace(alt, neu)
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "tab"
    kandidat, i = name, 2
    while kandidat in vergeben:
        kandidat, i = f"{name}-{i}", i + 1
    vergeben.add(kandidat)
    return kandidat + ".json"


def aufteilen(flows_datei, ordner):
    flows = laden(flows_datei)
    if not isinstance(flows, list):
        # Nie auf Basis einer unlesbaren Datei alle Tabs als gelöscht verbuchen
        sys.exit(f"{flows_datei} ist keine gültige Flow-Datei")
    ordner = Path(ordner)
    ordner.mkdir(parents=True, exist_ok=True)

    behaelter = [n for n in flows if n.get("type") in ("tab", "subflow")]
    ids = {n["id"] for n in behaelter}
    gruppen = {n["id"]: [n] for n in behaelter}
    konfig = []
    for n in flows:
        if n.get("type") in ("tab", "subflow"):
            continue
        if n.get("z") in ids:
            gruppen[n["z"]].append(n)
        else:
            konfig.append(n)

    vergeben, geschrieben = set(), {KONFIG}
    for b in behaelter:
        datei = dateiname(b.get("label") or b.get("name") or b["id"], vergeben)
        speichern(ordner / datei, gruppen[b["id"]])
        geschrieben.add(datei)
        print(f"{datei}\t{b.get('label') or b.get('name') or b['id']}")
    speichern(ordner / KONFIG, {"reihenfolge": [b["id"] for b in behaelter], "nodes": konfig})
    print(f"{KONFIG}\tKonfiguration")

    for alt in ordner.glob("*.json"):
        if alt.name not in geschrieben:
            alt.unlink()


def vergleich(alt_datei, neu_datei):
    def nodes(pfad):
        daten = laden(pfad)
        if isinstance(daten, dict):
            daten = daten.get("nodes", [])
        return {n["id"]: n for n in daten or []}

    a, n = nodes(alt_datei), nodes(neu_datei)
    if not a:
        print(f"neu ({len(n)} Nodes)")
    elif not n:
        print("gelöscht")
    else:
        geaendert = sum(1 for k in n.keys() & a.keys() if n[k] != a[k])
        print(f"+{len(n.keys() - a.keys())} / -{len(a.keys() - n.keys())} / ~{geaendert} Nodes")


def zusammensetzen(ordner):
    ordner = Path(ordner)
    konfig = laden(ordner / KONFIG) or {"reihenfolge": [], "nodes": []}
    gruppen = {}
    for datei in sorted(ordner.glob("*.json")):
        if datei.name != KONFIG:
            daten = laden(datei) or []
            if daten:
                gruppen[daten[0]["id"]] = daten
    flows = []
    for tab_id in konfig["reihenfolge"] + [i for i in gruppen if i not in konfig["reihenfolge"]]:
        flows += [n for n in gruppen.get(tab_id, []) if n.get("type") in ("tab", "subflow")]
    for tab_id in gruppen:
        flows += [n for n in gruppen[tab_id] if n.get("type") not in ("tab", "subflow")]
    flows += konfig["nodes"]
    json.dump(flows, sys.stdout, indent=4, ensure_ascii=False)


def ersetzen(flows_datei, tab_datei):
    flows, tab = laden(flows_datei), laden(tab_datei)
    if not isinstance(flows, list) or not isinstance(tab, list) or not tab:
        sys.exit("Flow- oder Tab-Datei ist ungültig, nichts geändert")
    tab_id = tab[0]["id"]
    tabs = [n for n in flows if n.get("type") in ("tab", "subflow")]
    if any(n["id"] == tab_id for n in tabs):
        tabs = [tab[0] if n["id"] == tab_id else n for n in tabs]
    else:
        tabs.append(tab[0])
    rest = [n for n in flows if n.get("type") not in ("tab", "subflow") and n.get("z") != tab_id]
    json.dump(tabs + rest + tab[1:], sys.stdout, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # flows.json ist UTF-8, unabhängig vom Gebietsschema (z. B. unter systemd)
    sys.stdout.reconfigure(encoding="utf-8")
    befehle = {"aufteilen": aufteilen, "vergleich": vergleich,
               "zusammensetzen": zusammensetzen, "ersetzen": ersetzen}
    if len(sys.argv) < 3 or sys.argv[1] not in befehle:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    befehle[sys.argv[1]](*sys.argv[2:])
