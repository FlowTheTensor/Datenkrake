const status = document.querySelector("#status");

function element(tag, text, klasse) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (klasse) el.className = klasse;
  return el;
}

function hinweisListe(hinweise, liste) {
  liste.replaceChildren(...hinweise.map((text) => element("li", text)));
  liste.hidden = hinweise.length === 0;
  return liste;
}

function zeigeSzenario(szenario) {
  const karte = element("article");
  karte.append(element("h3", szenario.name));

  karte.append(element("h4", "Weg"));
  const weg = element("ol", undefined, "weg");
  weg.append(element("li", "START", "rand"));
  for (const schritt of szenario.weg) {
    if (schritt.knoten) {
      weg.append(element("li", schritt.knoten));
    } else {
      const antwort = schritt.antwort === null ? "keine Antwort" : `Antwort: ${schritt.antwort}`;
      weg.append(element("li", `Frage: ${schritt.frage} - ${antwort}`, "frage"));
    }
  }
  karte.append(weg);

  karte.append(hinweisListe(szenario.hinweise, element("ul", undefined, "hinweise")));

  karte.append(element("h4", "Endstatus"));
  const tabelle = element("dl", undefined, "endstatus");
  for (const [feld, wert] of Object.entries(szenario.status)) {
    tabelle.append(element("dt", feld));
    const text = typeof wert === "string" ? wert : JSON.stringify(wert);
    tabelle.append(element("dd", text === "" ? "(leer)" : text, text === "" ? "leer" : undefined));
  }
  karte.append(tabelle);
  return karte;
}

async function zeichneDiagramm(quelltext) {
  const diagramm = document.querySelector("#diagramm");
  const mermaid = await window.mermaidBereit;
  if (!mermaid) {
    diagramm.replaceChildren(
      element("p", "Die Diagramm-Bibliothek konnte nicht geladen werden (keine Internetverbindung?). Hier der Mermaid-Quelltext:", "hinweis-text"),
      element("pre", quelltext),
    );
    return;
  }
  const { svg } = await mermaid.render(`langgraph-${Date.now()}`, quelltext);
  diagramm.innerHTML = svg;
}

async function aktualisieren() {
  status.textContent = "Erzeuge Diagramm ...";
  const [quelleAntwort, datenAntwort] = await Promise.all([
    fetch("/api/quellcode"),
    fetch("/api/werkstatt"),
  ]);
  const quelle = await quelleAntwort.json();
  document.querySelector("#quellcode").textContent = quelle.code;
  const daten = await datenAntwort.json();
  const szenarien = document.querySelector("#szenarien");
  const hinweise = document.querySelector("#hinweise");
  if (!datenAntwort.ok) {
    document.querySelector("#diagramm").textContent = `Fehler im Python-Code: ${daten.fehler}`;
    szenarien.replaceChildren();
    hinweisListe([], hinweise);
    status.textContent = "Fehler";
    return;
  }

  await zeichneDiagramm(daten.mermaid);
  hinweisListe(daten.hinweise, hinweise);
  szenarien.replaceChildren(...daten.szenarien.map(zeigeSzenario));
  status.textContent = "Aktualisiert";
}

function starte() {
  aktualisieren().catch((error) => {
    status.textContent = "Fehler";
    document.querySelector("#diagramm").textContent = error.message;
  });
}

document.querySelector("#aktualisieren").addEventListener("click", starte);
starte();
