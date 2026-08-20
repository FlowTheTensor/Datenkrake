const status = document.querySelector("#status");

async function aktualisieren() {
  status.textContent = "Erzeuge Diagramm ...";
  const [quelleAntwort, datenAntwort] = await Promise.all([
    fetch("/api/quellcode"),
    fetch("/api/werkstatt"),
  ]);
  const quelle = await quelleAntwort.json();
  document.querySelector("#quellcode").textContent = quelle.code;
  const daten = await datenAntwort.json();
  if (!datenAntwort.ok) {
    document.querySelector("#diagramm").textContent = `Fehler im Python-Code: ${daten.fehler}`;
    status.textContent = "Fehler";
    return;
  }

  const diagramm = document.querySelector("#diagramm");
  const id = `langgraph-${Date.now()}`;
  const { svg } = await window.mermaid.render(id, daten.mermaid);
  diagramm.innerHTML = svg;
  document.querySelector("#freigabe").textContent = daten.freigabe.report;
  document.querySelector("#ablehnung").textContent = daten.ablehnung.report;
  status.textContent = "Aktualisiert";
}

document.querySelector("#aktualisieren").addEventListener("click", aktualisieren);
aktualisieren().catch((error) => {
  status.textContent = "Fehler";
  document.querySelector("#diagramm").textContent = error.message;
});