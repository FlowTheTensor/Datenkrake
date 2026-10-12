const status = document.querySelector("#status");
const knopfStarten = document.querySelector("#starten");
const knopfNeuLaden = document.querySelector("#neu-laden");
let szenarien = [];
let mermaidQuelltext = "";
let threadId = null;
let letzterSchritt = null;

function element(tag, text, klasse) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (klasse) el.className = klasse;
  return el;
}

function neueId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

function beschaeftigt(ja) {
  knopfStarten.disabled = ja;
  knopfNeuLaden.disabled = ja;
}

// ---------- Diagramm ----------

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
  const { svg } = await mermaid.render(`live-${Date.now()}`, quelltext);
  diagramm.innerHTML = svg;
}

function knotenImDiagramm(name) {
  const muster = new RegExp(`flowchart-${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}-\\d+$`);
  return [...document.querySelectorAll("#diagramm g.node")].find((g) => muster.test(g.id));
}

// Mermaid setzt die Fuellfarbe inline mit !important, CSS kommt dagegen nicht an.
const FUELLFARBEN = { aktiv: "#f4b9a6", fertig: "#cfe5d6", wartet: "#fde7a9" };

function markiere(name, zustand) {
  const knoten = knotenImDiagramm(name);
  if (!knoten) return;
  knoten.classList.remove("knoten-aktiv", "knoten-fertig", "knoten-wartet");
  knoten.classList.add(`knoten-${zustand}`);
  knoten.querySelectorAll(".label-container").forEach((form) => {
    form.style.setProperty("fill", FUELLFARBEN[zustand], "important");
  });
}

// ---------- Anzeige ----------

function zeigeHinweise(hinweise) {
  const liste = document.querySelector("#hinweise");
  liste.replaceChildren(...hinweise.map((text) => element("li", text)));
  liste.hidden = hinweise.length === 0;
}

function zeigeZustand(snapshot) {
  const tabelle = document.querySelector("#zustand");
  tabelle.replaceChildren();
  for (const [feld, wert] of Object.entries(snapshot)) {
    const text = typeof wert === "string" ? wert : JSON.stringify(wert);
    tabelle.append(element("dt", feld));
    tabelle.append(element("dd", text === "" ? "(leer)" : text, text === "" ? "leer" : undefined));
  }
}

function zeigeNachricht(text, klasse) {
  const nachricht = document.querySelector("#nachricht");
  nachricht.textContent = text;
  nachricht.className = klasse ? `nachricht ${klasse}` : "nachricht";
  nachricht.hidden = false;
}

function protokolliere(ereignis) {
  const { type, ...rest } = ereignis;
  const zeile = element("li");
  const kategorie = type.split("_")[0].toLowerCase();
  zeile.append(element("span", type, `typ typ-${kategorie}`));
  if (Object.keys(rest).length) zeile.append(element("code", JSON.stringify(rest)));
  const protokoll = document.querySelector("#protokoll");
  protokoll.append(zeile);
  protokoll.scrollTop = protokoll.scrollHeight;
}

// ---------- Unterbrechung (Human in the loop) ----------

function zeigeFrage(unterbrechung) {
  const box = document.querySelector("#frage");
  document.querySelector("#frage-text").textContent = unterbrechung.message || "(ohne Text)";
  const antworten = document.querySelector("#frage-antworten");
  antworten.replaceChildren();

  const beantworte = (eintrag) => {
    box.hidden = true;
    lauf({ resume: [{ interruptId: unterbrechung.id, ...eintrag }] });
  };

  const optionen = unterbrechung.responseSchema?.enum;
  if (Array.isArray(optionen)) {
    for (const option of optionen) {
      const knopf = element("button", option);
      knopf.addEventListener("click", () => beantworte({ status: "resolved", payload: option }));
      antworten.append(knopf);
    }
  } else {
    const eingabe = element("input");
    eingabe.placeholder = "Antwort eingeben";
    const senden = element("button", "Senden");
    senden.addEventListener("click", () => beantworte({ status: "resolved", payload: eingabe.value }));
    antworten.append(eingabe, senden);
  }
  const abbrechen = element("button", "Abbrechen", "zweitrangig");
  abbrechen.addEventListener("click", () => beantworte({ status: "cancelled" }));
  antworten.append(abbrechen);
  box.hidden = false;
}

// ---------- AG-UI: Anfrage senden, Ereignisstrom lesen ----------

function verarbeite(ereignis) {
  switch (ereignis.type) {
    case "RUN_STARTED":
      status.textContent = "Laeuft ...";
      break;
    case "STEP_STARTED":
      letzterSchritt = ereignis.stepName;
      markiere(ereignis.stepName, "aktiv");
      break;
    case "STEP_FINISHED":
      markiere(ereignis.stepName, "fertig");
      break;
    case "STATE_SNAPSHOT":
      zeigeZustand(ereignis.snapshot);
      break;
    case "TEXT_MESSAGE_START":
      zeigeNachricht("");
      break;
    case "TEXT_MESSAGE_CONTENT":
      document.querySelector("#nachricht").textContent += ereignis.delta;
      break;
    case "RUN_FINISHED": {
      const art = ereignis.outcome?.type;
      if (art === "interrupt") {
        if (letzterSchritt) markiere(letzterSchritt, "wartet");
        status.textContent = "Wartet auf Antwort";
        zeigeFrage(ereignis.outcome.interrupts[0]);
      } else {
        status.textContent = art === "cancelled" ? "Abgebrochen" : "Fertig";
      }
      break;
    }
    case "RUN_ERROR":
      status.textContent = "Fehler";
      zeigeNachricht(ereignis.message, "fehler");
      break;
  }
}

async function lauf({ state = {}, resume } = {}) {
  beschaeftigt(true);
  const anfrage = {
    threadId,
    runId: neueId(),
    state,
    messages: [],
    tools: [],
    context: [],
    forwardedProps: {},
  };
  if (resume) anfrage.resume = resume;

  try {
    const antwort = await fetch("/api/agui", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(anfrage),
    });
    if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`);

    // Server-Sent Events: jedes Ereignis ist eine Zeile "data: {...}" plus Leerzeile.
    const leser = antwort.body.pipeThrough(new TextDecoderStream()).getReader();
    let puffer = "";
    while (true) {
      const { value, done } = await leser.read();
      if (done) break;
      puffer += value;
      const bloecke = puffer.split("\n\n");
      puffer = bloecke.pop();
      for (const block of bloecke) {
        if (!block.startsWith("data: ")) continue;
        const ereignis = JSON.parse(block.slice(6));
        protokolliere(ereignis);
        verarbeite(ereignis);
      }
    }
  } catch (fehler) {
    status.textContent = "Fehler";
    zeigeNachricht(fehler.message, "fehler");
  } finally {
    beschaeftigt(false);
  }
}

async function starten() {
  const szenario = szenarien[document.querySelector("#szenario").value];
  threadId = neueId();
  letzterSchritt = null;
  await zeichneDiagramm(mermaidQuelltext); // frisch gezeichnet = ohne alte Markierungen
  document.querySelector("#frage").hidden = true;
  document.querySelector("#nachricht").hidden = true;
  document.querySelector("#zustand").replaceChildren();
  lauf({ state: szenario ? szenario.status : {} });
}

async function vorbereiten() {
  status.textContent = "Lade Graph ...";
  document.querySelector("#frage").hidden = true;
  document.querySelector("#nachricht").hidden = true;
  const antwort = await fetch("/api/live");
  const daten = await antwort.json();
  if (!antwort.ok) {
    document.querySelector("#diagramm").textContent = `Fehler im Python-Code: ${daten.fehler}`;
    knopfStarten.disabled = true;
    status.textContent = "Fehler";
    return;
  }
  szenarien = daten.szenarien;
  const auswahl = document.querySelector("#szenario");
  auswahl.replaceChildren(...szenarien.map((s, i) => {
    const option = element("option", s.name);
    option.value = i;
    return option;
  }));
  zeigeHinweise(daten.hinweise);
  mermaidQuelltext = daten.mermaid;
  await zeichneDiagramm(mermaidQuelltext);
  knopfStarten.disabled = false;
  status.textContent = "Bereit";
}

function mitFehleranzeige(aufgabe) {
  return () => aufgabe().catch((fehler) => {
    status.textContent = "Fehler";
    document.querySelector("#diagramm").textContent = fehler.message;
  });
}

knopfStarten.addEventListener("click", mitFehleranzeige(starten));
knopfNeuLaden.addEventListener("click", mitFehleranzeige(vorbereiten));
document.querySelector("#leeren").addEventListener("click", () => {
  document.querySelector("#protokoll").replaceChildren();
});
mitFehleranzeige(vorbereiten)();
