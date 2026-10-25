(function(){
  "use strict";

  /* ---------------- Signatur-Leiste (Punkte/Striche) ---------------- */
  var rail = document.getElementById('sigRail');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var shapes = ['dot','dot','dash'];
  for (var i=0; i<26; i++){
    var el = document.createElement('span');
    el.className = shapes[i % shapes.length];
    if(!reduceMotion){
      el.style.animationDelay = (Math.random()*2.6).toFixed(2)+'s';
    }
    rail.appendChild(el);
  }

  /* ---------------- Settings drawer ---------------- */
  var toggle = document.getElementById('settingsToggle');
  var drawer = document.getElementById('settingsDrawer');
  toggle.addEventListener('click', function(){
    var open = drawer.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });

  /* ---------------- Overlays (Architektur + OPC-UA-Dokumentation) ---------------- */
  function setupOverlay(btnId, overlayId, closeId){
    var btn = document.getElementById(btnId);
    var overlay = document.getElementById(overlayId);
    var close = document.getElementById(closeId);
    if(!btn || !overlay || !close) return;
    function open(){
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
      close.focus();
    }
    function shut(){
      overlay.classList.remove('open');
      document.body.style.overflow = '';
      btn.focus();
    }
    btn.addEventListener('click', open);
    close.addEventListener('click', shut);
    overlay.addEventListener('click', function(e){
      if (e.target === overlay) shut();
    });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape' && overlay.classList.contains('open')) shut();
    });
  }
  setupOverlay('archOverlayBtn', 'archOverlay', 'archOverlayClose');
  setupOverlay('uaxOverlayBtn', 'uaxOverlay', 'uaxOverlayClose');
  setupOverlay('pollerOverlayBtn', 'pollerOverlay', 'pollerOverlayClose');

  function urlOf(fieldId){ return document.getElementById(fieldId).value.replace(/\/$/,''); }

  /* ---------------- Reihenfolge der Themenblöcke ---------------- */
  (function reorderThemeSections(){
    var main = document.querySelector('main');
    var themaCrispDm = document.getElementById('thema-crispdm');
    var themaA = document.getElementById('thema-a');
    var themaB = document.getElementById('thema-b');
    var themaC = document.getElementById('thema-c');
    var themaD = document.getElementById('thema-d');
    var themaE = document.getElementById('thema-e');
    var themaML = document.getElementById('thema-ml');
    var quiz = document.getElementById('quiz');
    var chatPanel = document.getElementById('chatConsolePanel');
    if(!main || !themaCrispDm || !themaA || !themaB || !themaC || !themaD || !themaE || !themaML || !quiz) return;

    if(chatPanel){
      var infoA = themaA.querySelector('.info-box');
      if(infoA){
        infoA.insertAdjacentElement('afterend', chatPanel);
      }
    }

    var archPanel = themaA.querySelector('section[aria-labelledby="archHeading"]');
    var netPanel = themaE.querySelector('.panel');
    if(archPanel && netPanel){
      themaE.insertBefore(archPanel, netPanel);
    }

    main.insertBefore(themaCrispDm, quiz);
    main.insertBefore(themaE, quiz);
    main.insertBefore(themaB, quiz);
    main.insertBefore(themaD, quiz);
    main.insertBefore(themaC, quiz);
    main.insertBefore(themaML, quiz);
    main.insertBefore(themaA, quiz);
  })();

  /* ---------------- KI-System links ---------------- */
  function wireKiLink(inputId, linkId){
    var input = document.getElementById(inputId);
    var link = document.getElementById(linkId);
    if(!input || !link) return;
    function update(){ link.href = input.value || '#'; }
    input.addEventListener('input', update);
    update();
  }
  wireKiLink('forgejoUrl','forgejoOpen');
  wireKiLink('noderedProjektUrl','noderedProjektOpen');
  wireKiLink('akustikUrl','akustikOpen');
  wireKiLink('historianUrl','historianOpen');
  wireKiLink('grafanaUrl','grafanaOpen');
  wireKiLink('noderedUrl','noderedOpen');
  wireKiLink('minioUrl','minioOpen');
  wireKiLink('jupyterUrl','jupyterOpen');

  /* ---------------- Agent / Instrument Cards ---------------- */
  var CARD_DEFS = [
    { kind:'A2A-AGENT', field:'urlOrchestrator', path:'/.well-known/agent-card.json',
      fallback:{ name:'Orchestrator-Agent', description:'Überwacht die Datenkrake und delegiert Wartung per LAP.',
                 skills:[{name:'wartungsstatus_melden'}] } },
    { kind:'A2A-AGENT', field:'urlDb', path:'/.well-known/agent-card.json',
      fallback:{ name:'DB-Agent (Datenkrake)', description:'Liest Akustik-Telemetrie und Anomalien aus der MariaDB.',
                 skills:[{name:'telemetrie_abfragen'}] } },
    { kind:'A2A-AGENT', field:'urlReport', path:'/.well-known/agent-card.json',
      fallback:{ name:'Report-Agent', description:'Formuliert Meldungen zu Wartungs- und Nachschubereignissen.',
                 skills:[{name:'bericht_erstellen'}] } },
    { kind:'LAP-INSTRUMENT', field:'urlWartung', path:'/.well-known/instrument-card.json',
      fallback:{ name:'Wartungsgeraet-Akustik', description:'Mobiles Diagnose- und Schmiergerät für den überwachten Motor.',
                 capabilities:['diagnosefahrt','schmierzyklus'] } }
  ];

  async function fetchWithTimeout(url, ms){
    var ctrl = new AbortController();
    var t = setTimeout(function(){ ctrl.abort(); }, ms);
    try{
      var res = await fetch(url, {signal: ctrl.signal});
      if(!res.ok) throw new Error('HTTP '+res.status);
      return await res.json();
    } finally { clearTimeout(t); }
  }

  function renderCard(def, data, isLive){
    var card = document.createElement('div');
    card.className = 'card';
    var tags = (data.skills || (data.capabilities||[]).map(function(c){return {name:c};}) || [])
      .map(function(s){ return '<span class="tag">'+ (s.name||s) +'</span>'; }).join('');
    card.innerHTML =
      '<div class="card-top">'+
        '<div><div class="kind">'+def.kind+'</div><div class="name">'+(data.name||'—')+'</div></div>'+
        '<span class="badge '+(isLive?'live':'')+'"><span class="d"></span>'+(isLive?'live':'demo')+'</span>'+
      '</div>'+
      '<div class="desc">'+(data.description||'')+'</div>'+
      '<div class="tags">'+tags+'</div>'+
      '<div class="url">'+urlOf(def.field)+def.path+'</div>';
    return card;
  }

  /* ---------------- Quiz ---------------- */
  var QUIZ = [
    {cat:'H', color:'#C81E3A', q:'Was verbindet MCP typischerweise?',
     options:['Zwei Agenten miteinander','Ein Sprachmodell mit Werkzeugen/Daten','Zwei Datenbanken miteinander','Einen Menschen mit einem anderen Menschen'],
     correct:1, exp:'MCP ist die "vertikale" Kante: ein Modell greift auf Tools/Resources/Prompts eines Servers zu — z.B. Claude Desktop auf mcpserver.py.'},
    {cat:'H', color:'#C81E3A', q:'Wodurch entdeckt ein A2A-Agent die Fähigkeiten eines anderen Agenten?',
     options:['Über eine feste IP-Adressliste','Über ein MQTT-Topic','Über eine Agent Card unter /.well-known/agent-card.json','Über eine SQL-Abfrage'],
     correct:2, exp:'Die Agent Card ist das öffentliche "Türschild" eines A2A-Agenten mit seinen Skills.'},
    {cat:'H', color:'#C81E3A', q:'Wozu dient der Safety-Fence-Mechanismus in LAP?',
     options:['Er verschlüsselt die Verbindung','Er holt vor gefährlichen/irreversiblen Aktionen eine Bestätigung ein','Er reserviert Speicherplatz','Er startet den Container neu'],
     correct:1, exp:'Bevor eine als gefährlich markierte Aktion ausgeführt wird, muss sie explizit bestätigt werden — siehe Wartungs-Agent.'},
    {cat:'H', color:'#C81E3A', q:'Was macht der "Harness" eines Agenten konkret?',
     options:['Er trainiert das neuronale Netz','Er speichert Messwerte in der Datenbank','Er verschickt MQTT-Nachrichten','Er wechselt zwischen LLM-Aufruf und Tool-Ausführung ab, bis das Modell fertig ist'],
     correct:3, exp:'Genau diese Schleife macht aus einem rohen Sprachmodell etwas, das selbstständig Werkzeuge nutzen kann.'},

    {cat:'G', color:'#C81E3A', q:'Womit trainiert der Arduino UNO Q sein Klassifikationsmodell?',
     options:['Nur mit dem Label','Mit Label und vollständigem FFT-Spektrum aus der MariaDB','Mit Daten aus InfluxDB','Mit zufällig erzeugten Daten'],
     correct:1, exp:'Der Historian speichert das Spektrum bewusst nicht — nur die MariaDB hat die vollständigen Trainingsdaten.'},
    {cat:'G', color:'#C81E3A', q:'Was macht Nessie im Data-Lake-Stack besonders?',
     options:['Es ist ein Objektspeicher','Es ersetzt MariaDB','Es bietet Git-artige Versionierung (Branches, Commits) für Tabellen','Es ist ein Backup-Programm'],
     correct:2, exp:'Tabellen lassen sich branchen, committen und zusammenführen — "Git für Daten".'},
    {cat:'G', color:'#C81E3A', q:'Ist die YOLO-Anbindung im aktuellen Projektstand schon vollständig umgesetzt?',
     options:['Ja, vollständig','Nein, sie ist bewusst als "geplant" markiert','Nur auf dem Data-Lake-Rechner','Nur in der Simulation'],
     correct:1, exp:'Ehrlich im Dashboard gekennzeichnet, um nichts vorzugaukeln, was noch nicht existiert.'},
    {cat:'G', color:'#C81E3A', q:'Warum läuft der Data-Lake-Stack NICHT auf dem Raspberry Pi?',
     options:['Kein Netzwerkzugang','Spark/Jupyter sind zu ressourcenhungrig für den Pi','MinIO läuft nur auf x86','Der Pi unterstützt kein Docker'],
     correct:1, exp:'Deshalb läuft der Stack als eigener Compose-Stack auf einem separaten, stärkeren Rechner.'},

    {cat:'F', color:'#2F6B4F', q:'Was speichert der Operational Historian (InfluxDB) bewusst NICHT?',
     options:['Den Zeitstempel','Das vollständige FFT-Spektrum-Array','Den peak_db-Wert','Das Label'],
     correct:1, exp:'Zeitreihen-Datenbanken sind für skalare Werte optimiert, nicht für große verschachtelte Strukturen.'},
    {cat:'F', color:'#2F6B4F', q:'Wie nennt man das Prinzip, bewusst mehrere Datenbanktypen parallel einzusetzen?',
     options:['Sharding','Normalisierung','Replikation','Polyglot Persistence'],
     correct:3, exp:'Ein etabliertes Architekturprinzip, kein Sonderfall dieses Projekts.'},
    {cat:'F', color:'#2F6B4F', q:'Welche Datenbank bleibt die einzige VOLLSTÄNDIGE Quelle für Trainingsdaten?',
     options:['InfluxDB','MinIO','MariaDB','Nessie'],
     correct:2, exp:'Nur dort liegen Label UND vollständiges Spektrum zusammen.'},
    {cat:'F', color:'#2F6B4F', q:'Ab wann lohnt sich ein Operational Historian laut Projekt-Einschätzung wirklich?',
     options:['Sofort, unabhängig von der Anlagengröße','Erst bei mehreren Sensoren/Stationen, hoher Frequenz oder Bedarf an Datenalterung','Nie, er ist überflüssig','Nur ohne SQL-Datenbank'],
     correct:1, exp:'Für einen einzelnen Sensor ist er aktuell eher Lerninhalt als operative Notwendigkeit.'},

    {cat:'E', color:'#2A5F8A', q:'Welches Kommunikationsmuster nutzt MQTT?',
     options:['Publish/Subscribe','Request/Response','Peer-to-Peer-Streaming','Broadcast ohne Empfänger'],
     correct:0, exp:'Der Sender weiß nicht, wer (oder ob überhaupt jemand) mithört.'},
    {cat:'E', color:'#2A5F8A', q:'Was macht Node-RED in diesem Projekt?',
     options:['Es trainiert neuronale Netze','Es liest OPC-UA-Tags und veröffentlicht sie per MQTT','Es ist die Hauptdatenbank','Es ersetzt Mosquitto'],
     correct:1, exp:'Eine Low-Code-Brücke zwischen SPS-Welt (OPC-UA) und IoT-Welt (MQTT).'},
    {cat:'E', color:'#2A5F8A', q:'Welches Protokoll ist der klassische Industriestandard für Maschinenkommunikation?',
     options:['MQTT','HTTP','OPC-UA','FTP'],
     correct:2, exp:'S7-1500/ET200SP & Co. sprechen typischerweise OPC-UA.'},
    {cat:'E', color:'#2A5F8A', q:'Auf welchem MQTT-Topic-Namensraum landen die aus OPC-UA gelesenen SPS-Werte?',
     options:['audio/spectrum','sensor/data','opcua/raw','plc/<station>/<tag>'],
     correct:3, exp:'Bewusst getrennt vom bestehenden audio/spectrum-Topic.'},

    {cat:'C', color:'#5B5852', q:'Warum laufen die Dienste dieses Projekts in Docker-Containern?',
     options:['Pflicht unter Raspberry Pi OS','Für Isolation und reproduzierbare Installation','Weil Python das erfordert','Um Strom zu sparen'],
     correct:1, exp:'Jeder Dienst läuft unabhängig vom restlichen System — leicht neu aufsetzbar.'},
    {cat:'C', color:'#5B5852', q:'Was ist die Besonderheit des Arduino UNO Q gegenüber einem klassischen Arduino?',
     options:['Mehr USB-Ports','Er hat einen Linux-Teil und kann selbst KI-Inferenz rechnen','Nur für Audio gebaut','Er braucht kein Netzwerk'],
     correct:1, exp:'Genau das macht ihn zum Beispiel für Edge AI in diesem Projekt.'},
    {cat:'C', color:'#5B5852', q:'Welche Rolle spielt der Raspberry Pi in der Gesamtarchitektur?',
     options:['Nur ein Backup-Gerät','Der zentrale Edge-Server (Broker, DB, Historian, Webserver)','Er trainiert das neuronale Netz','Er ersetzt Claude Desktop'],
     correct:1, exp:'Die "Datenkrake" bündelt hier alle zentralen Dienste an einer Stelle.'},

    {cat:'H', color:'#C81E3A', q:'Was ist die Aufgabe des Orchestrator-Agenten?',
     options:['Er misst die Temperatur','Er verteilt Aufgaben an passende Fachagenten','Er ersetzt die Datenbank','Er rendert das Dashboard'],
     correct:1, exp:'Der Orchestrator nimmt eine Anfrage entgegen und delegiert sie an den zuständigen Agenten.'},
    {cat:'G', color:'#C81E3A', q:'Was ist ein Label bei überwachtem Lernen?',
     options:['Die erwartete Klasse oder Zielausgabe eines Trainingsbeispiels','Der Name des MQTT-Brokers','Ein Datenbankpasswort','Die IP-Adresse des Sensors'],
     correct:0, exp:'Das Label beschreibt, was das Modell für die Eingabedaten lernen soll.'},
    {cat:'F', color:'#2F6B4F', q:'Warum werden Messdaten in unterschiedlichen Datenbanken gespeichert?',
     options:['Weil jede Datenbank zufällig ausgewählt wird','Weil verschiedene Zugriffsmuster unterschiedliche Speicherlösungen verlangen','Damit Daten doppelt verloren gehen können','Weil SQL keine Messwerte speichern kann'],
     correct:1, exp:'Die Architektur nutzt je nach Aufgabe die passende Stärke von MariaDB, InfluxDB und dem Data Lake.'},
    {cat:'E', color:'#2A5F8A', q:'Was ist der Vorteil von OPC UA gegenüber einer einfachen Rohdatenverbindung?',
     options:['Es liefert nur Binärwerte','Es bringt ein standardisiertes, beschreibbares Informationsmodell mit','Es benötigt keinen Server','Es funktioniert nur ohne Netzwerk'],
     correct:1, exp:'OPC UA beschreibt neben Werten auch Typen, Metadaten und die Struktur der Anlage.'},
    {cat:'C', color:'#5B5852', q:'Warum werden Container für die einzelnen Dienste getrennt?',
     options:['Damit jeder Dienst unabhängig aktualisiert und betrieben werden kann','Damit alle Dienste dieselben Dateien überschreiben','Damit kein Netzwerk nötig ist','Damit Hardware überflüssig wird'],
     correct:0, exp:'Getrennte Container begrenzen Abhängigkeiten und machen Betrieb sowie Wartung reproduzierbarer.'},
    {cat:'D', color:'#B87A1C', q:'Was ist der Zweck eines Historian-Systems?',
     options:['Historische Messwerte zeitbezogen zu speichern und abfragbar zu machen','Agenten zu trainieren, ohne Daten zu speichern','OPC-UA-Geräte zu programmieren','Container-Images zu bauen'],
      correct:0, exp:'Ein Historian bewahrt Zeitreihen auf, damit Verläufe, Zustände und Trends später analysiert werden können.'},

     {cat:'H', color:'#C81E3A', q:'Was ist ein Tool bei einem MCP-Server?',
      options:['Eine vom Modell aufrufbare Funktion','Ein passives Bildformat','Ein MQTT-Broker','Ein Datenbankindex'],
      correct:0, exp:'Tools stellen ausführbare Funktionen bereit, zum Beispiel Abfragen oder Aktionen.'},
     {cat:'H', color:'#C81E3A', q:'Welche Information enthält eine Agent Card?',
      options:['Nur das Passwort des Agenten','Fähigkeiten, Endpunkte und Metadaten des Agenten','Die vollständige Datenbank','Das Docker-Image'],
      correct:1, exp:'Die Agent Card beschreibt, was ein Agent kann und wie andere Agenten ihn erreichen.'},
     {cat:'H', color:'#C81E3A', q:'Warum braucht der Harness eines Agenten einen Werkzeugaufruf-Zyklus?',
      options:['Damit das Modell Ergebnisse von Tools verarbeiten und weitere Schritte planen kann','Damit die CPU langsamer läuft','Damit Antworten verschlüsselt werden','Damit MQTT Topics anlegt'],
      correct:0, exp:'Der Zyklus verbindet Modellentscheidung, Werkzeugausführung und die nächste Modellantwort.'},
     {cat:'H', color:'#C81E3A', q:'Was bedeutet Human-in-the-loop bei einem Wartungs-Agenten?',
      options:['Ein Mensch bestätigt kritische Aktionen','Ein Mensch ersetzt alle Sensoren','Ein Agent arbeitet ohne Rückmeldung','Ein Modell wird manuell trainiert'],
      correct:0, exp:'Kritische oder irreversible Aktionen werden erst nach menschlicher Freigabe ausgeführt.'},
     {cat:'H', color:'#C81E3A', q:'Was ist eine Ressource im MCP-Kontext?',
      options:['Abrufbare Information oder Datenquelle','Ein Linux-Benutzerkonto','Ein Hardwarebauteil','Eine CSS-Klasse'],
      correct:0, exp:'Resources stellen Kontext oder Daten bereit, die ein Modell lesen kann.'},

     {cat:'G', color:'#C81E3A', q:'Was beschreibt eine Trainingsinstanz?',
      options:['Ein Eingabebeispiel mit zugehörigem Zielwert','Nur der Name eines Modells','Eine Netzwerkverbindung','Ein Container-Volume'],
      correct:0, exp:'Eine Trainingsinstanz besteht typischerweise aus Merkmalen und dem erwarteten Label.'},
     {cat:'G', color:'#C81E3A', q:'Warum wird ein FFT-Spektrum für die Klassifikation genutzt?',
      options:['Es macht Frequenzanteile eines Signals sichtbar','Es ersetzt jedes Label','Es verschlüsselt Messwerte','Es startet den Historian'],
      correct:0, exp:'Frequenzmerkmale können charakteristische Muster von Zuständen oder Fehlern sichtbar machen.'},
     {cat:'G', color:'#C81E3A', q:'Was ist Inferenz?',
      options:['Die Anwendung eines trainierten Modells auf neue Daten','Das Löschen aller Trainingsdaten','Das Erstellen eines MQTT-Brokers','Das Committen einer Tabelle'],
      correct:0, exp:'Bei der Inferenz erzeugt das Modell eine Vorhersage für bisher ungesehene Eingaben.'},
     {cat:'G', color:'#C81E3A', q:'Wozu dient ein Testdatensatz?',
      options:['Zur Bewertung des Modells mit Daten, die nicht zum Training verwendet wurden','Zum Speichern von Passwörtern','Zum Starten von Docker','Zur OPC-UA-Adressierung'],
      correct:0, exp:'Testdaten zeigen, wie gut das Modell auf unbekannte Beispiele generalisiert.'},
     {cat:'G', color:'#C81E3A', q:'Was bedeutet Edge AI?',
      options:['KI-Auswertung nahe an der Datenquelle','Training ausschließlich in der Cloud','Ein Netzwerk ohne Sensoren','Eine Datenbank ohne Tabellen'],
      correct:0, exp:'Bei Edge AI werden Daten direkt am Gerät oder in dessen Nähe verarbeitet.'},

     {cat:'F', color:'#2F6B4F', q:'Wofür eignet sich MariaDB in diesem Projekt besonders?',
      options:['Für strukturierte relationale Daten und vollständige Trainingsdatensätze','Nur für Videostreams','Nur für MQTT-Nachrichten','Als Betriebssystem'],
      correct:0, exp:'MariaDB hält strukturierte Datensätze mit Beziehungen, Labels und vollständigen Spektren.'},
     {cat:'F', color:'#2F6B4F', q:'Welche Stärke hat InfluxDB?',
      options:['Zeitreihen effizient zu speichern und abzufragen','Agent Cards zu veröffentlichen','Container zu bauen','Bilder zu klassifizieren'],
      correct:0, exp:'InfluxDB ist auf zeitbezogene Messwerte und schnelle Zeitreihenabfragen optimiert.'},
     {cat:'F', color:'#2F6B4F', q:'Was ist MinIO im Data-Lake-Stack?',
      options:['Ein S3-kompatibler Objektspeicher','Ein OPC-UA-Client','Ein LLM','Ein SPS-Programm'],
      correct:0, exp:'MinIO speichert Objekte und bildet die Speicherbasis für den Data-Lake-Stack.'},
     {cat:'F', color:'#2F6B4F', q:'Was ermöglicht ein Tabellen-Branch in Nessie?',
      options:['Eine isolierte Version einer Tabellenhistorie','Eine neue IP-Adresse','Einen zusätzlichen Sensor','Einen schnelleren MQTT-Broker'],
      correct:0, exp:'Branches erlauben es, Änderungen an Tabellen getrennt vorzubereiten und später zusammenzuführen.'},
     {cat:'F', color:'#2F6B4F', q:'Warum werden FFT-Arrays nicht vollständig in InfluxDB geschrieben?',
      options:['Weil InfluxDB für skalare Zeitreihenwerte gedacht ist','Weil Arrays keine Daten sind','Weil MariaDB keine Arrays speichern kann','Weil MQTT das verbietet'],
      correct:0, exp:'Der Historian speichert kompakte Kennwerte; das vollständige Array bleibt in der Trainingsdatenquelle.'},

     {cat:'E', color:'#2A5F8A', q:'Welche Rolle hat Mosquitto?',
      options:['MQTT-Broker für die Weiterleitung von Nachrichten','SQL-Datenbank für Trainingsdaten','OPC-UA-SPS','Webbrowser'],
      correct:0, exp:'Mosquitto empfängt MQTT-Nachrichten und verteilt sie an abonnierte Clients.'},
     {cat:'E', color:'#2A5F8A', q:'Was ist ein MQTT-Topic?',
      options:['Hierarchischer Namensraum für Nachrichten','Ein Datenbankpasswort','Ein Docker-Container','Ein neuronales Netz'],
      correct:0, exp:'Topics strukturieren Nachrichten und bestimmen, worauf Clients abonnieren können.'},
     {cat:'E', color:'#2A5F8A', q:'Was macht ein MQTT-Subscriber?',
      options:['Er abonniert Topics und empfängt passende Nachrichten','Er trainiert ein Modell','Er erzeugt OPC-UA-Nodes','Er erstellt Tabellenbranches'],
      correct:0, exp:'Subscriber melden sich für Topics an und verarbeiten die dort veröffentlichten Werte.'},
     {cat:'E', color:'#2A5F8A', q:'Was ist die Aufgabe eines OPC-UA-Clients?',
      options:['Er liest Werte von einem OPC-UA-Server','Er speichert Docker-Images','Er erstellt Agent Cards','Er ersetzt den MQTT-Broker'],
      correct:0, exp:'Der Client verbindet sich mit dem Server und liest die benötigten Nodes oder Tags.'},
     {cat:'E', color:'#2A5F8A', q:'Warum trennt ein Topic-Namensraum Audio- und SPS-Daten?',
      options:['Damit Datenquellen klar unterscheidbar und gezielt abonnierbar bleiben','Damit Nachrichten verschlüsselt werden','Damit OPC UA entfällt','Damit alle Daten doppelt gesendet werden'],
      correct:0, exp:'Klare Namensräume verhindern Verwechslungen und vereinfachen Filter sowie Weiterverarbeitung.'},

     {cat:'C', color:'#5B5852', q:'Was übernimmt Docker Compose?',
      options:['Es beschreibt und startet mehrere zusammengehörige Container','Es trainiert Klassifikatoren','Es liest SPS-Tags','Es ersetzt Linux'],
      correct:0, exp:'Compose bündelt Dienste, Netzwerke, Volumes und ihre Konfiguration in einer deklarativen Datei.'},
     {cat:'C', color:'#5B5852', q:'Warum läuft der Webserver auf dem Raspberry Pi?',
      options:['Er stellt das Leitstand- und Dashboard-Angebot im lokalen Netz bereit','Er ersetzt alle Agenten','Er trainiert YOLO','Er speichert nur FFT-Arrays'],
      correct:0, exp:'Der Pi bündelt die lokalen Dienste und kann die Benutzeroberfläche im Anlagen-Netz ausliefern.'},
     {cat:'C', color:'#5B5852', q:'Was ist ein Container-Volume?',
      options:['Dauerhafter Speicher außerhalb des flüchtigen Container-Dateisystems','Ein MQTT-Topic','Ein Modell-Label','Ein OPC-UA-Tag'],
      correct:0, exp:'Volumes bewahren Daten auch dann, wenn ein Container neu erstellt oder ersetzt wird.'},
     {cat:'C', color:'#5B5852', q:'Welche Aufgabe hat ein Dockerfile?',
      options:['Es beschreibt, wie ein Container-Image gebaut wird','Es definiert SPS-Variablen','Es speichert Zeitreihen','Es beantwortet LLM-Fragen'],
      correct:0, exp:'Ein Dockerfile legt Basisimage, Abhängigkeiten und Startbefehl eines Images fest.'},
     {cat:'C', color:'#5B5852', q:'Warum ist der Raspberry Pi ein Edge-Server?',
      options:['Er verarbeitet und verteilt Daten direkt nahe an der Anlage','Er ist ausschließlich ein Cloud-Rechner','Er arbeitet ohne Netzwerk','Er dient nur als USB-Stick'],
      correct:0, exp:'Die lokale Verarbeitung reduziert Abhängigkeit von externen Diensten und hält Daten im Anlagen-Netz.'},
     {cat:'C', color:'#5B5852', q:'Was ist ein Vorteil reproduzierbarer Container-Images?',
      options:['Dienste können auf verschiedenen Systemen konsistent eingerichtet werden','Sensoren benötigen keine Stromversorgung','Datenbanken werden überflüssig','OPC UA wird zu MQTT'],
      correct:0, exp:'Ein fest beschriebenes Image bringt Anwendung und Abhängigkeiten zuverlässig gemeinsam auf das Zielsystem.'},

     {cat:'D', color:'#B87A1C', q:'Was ist ein Sensorwert?',
      options:['Eine vom Sensor erfasste Messgröße','Ein Docker-Befehl','Ein Agentenname','Ein SQL-Schema'],
      correct:0, exp:'Sensorwerte bilden die beobachteten Zustände der Anlage ab, zum Beispiel Temperatur oder Schalldruck.'},
     {cat:'D', color:'#B87A1C', q:'Warum werden Zeitstempel mit Messwerten gespeichert?',
      options:['Damit Entwicklungen und Ereignisse zeitlich eingeordnet werden können','Damit MQTT Topics verschlüsselt werden','Damit Container kleiner werden','Damit Labels entfallen'],
      correct:0, exp:'Ohne Zeitbezug lassen sich Verläufe, Korrelationen und Wartungsereignisse nicht zuverlässig analysieren.'},
     {cat:'D', color:'#B87A1C', q:'Was ist Telemetrie?',
      options:['Das Erfassen und Übertragen von Zustands- und Messdaten','Das Bauen eines Docker-Images','Das Trainieren eines LLM','Das Versionieren von Tabellen'],
      correct:0, exp:'Telemetrie liefert laufend Informationen über Zustand und Verhalten eines Systems.'},
     {cat:'D', color:'#B87A1C', q:'Welche Aufgabe hat der Historian-Bridge-Dienst?',
      options:['Er überführt eingehende Messdaten in die Historian-Datenbank','Er erstellt Agent Cards','Er programmiert den Arduino','Er ersetzt den Webserver'],
      correct:0, exp:'Die Bridge nimmt die eingehenden Daten auf und schreibt geeignete Zeitreihenwerte in InfluxDB.'},
     {cat:'D', color:'#B87A1C', q:'Warum sollten Messwerte Einheiten und Datentypen besitzen?',
      options:['Damit Werte korrekt interpretiert und verglichen werden können','Damit kein Netzwerk nötig ist','Damit Fragen automatisch richtig sind','Damit Topics gelöscht werden'],
      correct:0, exp:'Einheit und Datentyp verhindern Fehlinterpretationen, etwa zwischen Celsius, Prozent und booleschen Zuständen.'},
     {cat:'D', color:'#B87A1C', q:'Was bedeutet Samplingrate?',
      options:['Wie häufig ein Signal pro Zeit erfasst wird','Wie viele Container laufen','Wie viele Agenten antworten','Wie groß ein Dockerfile ist'],
      correct:0, exp:'Die Samplingrate legt fest, in welchen zeitlichen Abständen neue Messpunkte entstehen.'},
     {cat:'D', color:'#B87A1C', q:'Was ist eine Anomalie in der Telemetrie?',
      options:['Ein ungewöhnlich vom erwarteten Muster abweichender Zustand','Ein korrektes Datenbank-Backup','Ein neues MQTT Topic','Ein Docker-Label'],
      correct:0, exp:'Anomalien können auf Fehler, Verschleiß oder veränderte Betriebsbedingungen hinweisen.'},
     {cat:'D', color:'#B87A1C', q:'Warum werden Messdaten vor der Speicherung normalisiert?',
      options:['Damit Formate, Namen und Wertebereiche einheitlich sind','Damit alle Daten gelöscht werden','Damit der Broker ausfällt','Damit Labels zufällig werden'],
      correct:0, exp:'Einheitliche Daten erleichtern Speicherung, Abfragen und spätere Auswertung.'},
     {cat:'D', color:'#B87A1C', q:'Was sollte bei einem Sensorausfall erkennbar sein?',
      options:['Ob ein Wert fehlt, ungültig ist oder außerhalb des erwarteten Bereichs liegt','Nur die Farbe des Dashboards','Das Passwort des Brokers','Die Version des Browsers'],
      correct:0, exp:'Datenqualität und Ausfallzustände müssen von gültigen Messwerten unterscheidbar sein.'},

     {cat:'B', color:'#6B4E71', q:'Was ist CRISP-DM?',
      options:['Ein Vorgehensmodell für Data-Mining-Projekte in sechs Phasen','Ein MQTT-Broker','Ein Datenbankschema für PLC-Daten','Ein Agentenprotokoll wie MCP oder A2A'],
      correct:0, exp:'CRISP-DM steht für Cross-Industry Standard Process for Data Mining und beschreibt einen wiederholbaren Ablauf.'},
     {cat:'B', color:'#6B4E71', q:'In welcher Phase wird geklärt, warum überhaupt Akustik- und SPS-Daten überwacht werden?',
      options:['Business Understanding','Data Preparation','Deployment','Evaluation'],
      correct:0, exp:'Business Understanding klärt Ziel und Nutzen, bevor überhaupt Daten betrachtet werden.'},
     {cat:'B', color:'#6B4E71', q:'Welche Phase entspricht dem Sichten von audio_spectrum und plc_telemetry?',
      options:['Modeling','Data Understanding','Deployment','Business Understanding'],
      correct:1, exp:'Data Understanding bedeutet, die vorhandenen Rohdaten zu sichten und ihre Qualität einzuschätzen.'},
     {cat:'B', color:'#6B4E71', q:'Was passiert typischerweise in der Data-Preparation-Phase dieses Projekts?',
      options:['Messwerte werden bereinigt, normalisiert und in MariaDB/Historian abgelegt','Der Orchestrator-Agent wird gestartet','Ein Quiz wird erzeugt','Ein neuer Docker-Container wird gebaut'],
      correct:0, exp:'Erst nach Bereinigung und Ablage sind die Daten für Modellierung und Analyse nutzbar.'},
     {cat:'B', color:'#6B4E71', q:'Welche Phase vergleicht unterschiedliche ML-Verfahren auf den Akustikdaten?',
      options:['Modeling','Deployment','Business Understanding','Data Preparation'],
      correct:0, exp:'In der Modeling-Phase werden verschiedene Modelle trainiert und miteinander verglichen.'},
     {cat:'B', color:'#6B4E71', q:'Wozu dient die Evaluation-Phase im Projekt?',
      options:['Um zu prüfen, ob der Anomalie-Detektor auf echten Messwerten zuverlässig funktioniert','Um Docker-Images zu bauen','Um MQTT-Topics zu benennen','Um die Datenbank zu löschen'],
      correct:0, exp:'Evaluation prüft, ob das Modell die gesteckten Ziele tatsächlich erreicht, bevor es produktiv genutzt wird.'},
     {cat:'B', color:'#6B4E71', q:'Was entspricht im Projekt der Deployment-Phase?',
      options:['Der Orchestrator-Agent delegiert Ergebnisse per LAP an den Wartungs-Agent','Das Sichten roher OPC-UA-Werte','Das Definieren des Projektziels','Das Trainieren des ersten Modells'],
      correct:0, exp:'Deployment bedeutet, ein Ergebnis tatsächlich in einem laufenden System wirksam werden zu lassen.'},
     {cat:'B', color:'#6B4E71', q:'Warum ist CRISP-DM ein Kreislauf und keine Einbahnstraße?',
      options:['Weil Erkenntnisse aus Evaluation und Deployment ins Business bzw. Data Understanding zurückfließen können','Weil jede Phase nur einmal durchlaufen werden darf','Weil MQTT das so vorschreibt','Weil Docker-Container neu gestartet werden müssen'],
      correct:0, exp:'Neue Erkenntnisse aus späteren Phasen führen häufig dazu, frühere Phasen erneut zu durchlaufen.'},
     {cat:'B', color:'#6B4E71', q:'Welche zwei Datenquellen stehen im Zentrum des CRISP-DM-Kreislaufs dieses Projekts?',
      options:['audio_spectrum und plc_telemetry','Agent Cards und MQTT-Broker','Docker-Images und Volumes','Grafana-Dashboards und InfluxDB-Token'],
      correct:0, exp:'Beide Tabellen liefern die Rohdaten, auf die sich alle sechs CRISP-DM-Phasen beziehen.'},
     {cat:'B', color:'#6B4E71', q:'Warum eignet sich CRISP-DM besonders gut, um dieses Projekt zu erklären?',
      options:['Weil es Business-Ziel, Daten, Modellierung und Betrieb an einem realen Beispiel zusammenführt','Weil es nur für SQL-Datenbanken gilt','Weil es MQTT ersetzt','Weil es ausschließlich für neuronale Netze entwickelt wurde'],
      correct:0, exp:'CRISP-DM verbindet fachliche Ziele mit Daten, Modellierung und Betrieb - genau das zeigt die Datenkrake praktisch.'},
     {cat:'A', color:'#2B7A78', q:'Wer übernimmt im Unterricht die Rolle des Product Owners?',
      options:['Die Lehrkraft','Der Scrum Master','Das Team, das am schnellsten ist','Forgejo'],
      correct:0, exp:'Der Product Owner pflegt und priorisiert das Backlog und nimmt Ergebnisse ab – im Unterricht ist das die Lehrkraft.'},
     {cat:'A', color:'#2B7A78', q:'Was ist das Backlog?',
      options:['Ein Ordner mit Datenbank-Backups','Die priorisierte Liste aller Aufgaben, Ideen und Fehler','Das Log-File von Node-RED','Der Verlauf der Deploys'],
      correct:1, exp:'Im Backlog stehen alle Issues. Der Product Owner sortiert es nach Wichtigkeit, im Sprint Planning werden daraus Aufgaben für den Sprint gewählt.'},
     {cat:'A', color:'#2B7A78', q:'Wozu dient das WIP-Limit „höchstens ein Issue pro Team in ‚In Arbeit‘“?',
      options:['Damit der Raspberry nicht überlastet wird','Damit niemand neue Issues anlegen kann','Damit Aufgaben fertig werden, statt dass viele gleichzeitig halb erledigt liegen bleiben','Damit der Product Owner weniger zu tun hat'],
      correct:2, exp:'WIP heißt Work in Progress. Ein Limit zwingt dazu, erst abzuschließen und dann Neues zu beginnen – das Board zeigt Engpässe sofort.'},
     {cat:'A', color:'#2B7A78', q:'Was beschreibt die Definition of Done?',
      options:['Gemeinsam vereinbarte Kriterien, wann ein Issue wirklich fertig ist','Den Termin, an dem der Sprint endet','Die Liste aller erledigten Issues','Die Aufgabenbeschreibung eines Issues'],
      correct:0, exp:'Bei uns: deployt und Deploy-Commit verlinkt, Akzeptanzkriterien abgehakt, von einem anderen Team getestet, dokumentiert, vom Product Owner abgenommen.'},
     {cat:'A', color:'#2B7A78', q:'Was passiert im täglichen Stand-up zu Beginn eines Unterrichtsblocks?',
      options:['Die Lehrkraft verteilt Noten','Jedes Team sagt kurz: Was haben wir geschafft, was machen wir heute, wo hängen wir?','Alle Issues werden neu geschätzt','Der Sprint wird beendet'],
      correct:1, exp:'Das Stand-up dauert nur 5–10 Minuten am Board. Blockaden werden sichtbar gemacht (Label „blockiert“), gelöst werden sie danach.'},
     {cat:'A', color:'#2B7A78', q:'Welche Aufgabe hat der Scrum Master?',
      options:['Er schreibt den meisten Code','Er entscheidet, welche Issues wichtig sind','Er nimmt Ergebnisse ab','Er moderiert Stand-up und Retro, hält das Board aktuell und meldet Blockaden'],
      correct:3, exp:'Der Scrum Master sorgt dafür, dass der Prozess funktioniert. Die Priorität legt der Product Owner fest.'},
     {cat:'A', color:'#2B7A78', q:'Wie ist eine User Story aufgebaut?',
      options:['„Als <Rolle> möchte ich <was>, damit <Nutzen>“ plus Akzeptanzkriterien','Nur eine Fehlermeldung mit Screenshot','Eine Liste von Node-IDs','Ein Commit mit Beschreibung'],
      correct:0, exp:'Die Story beschreibt den Nutzen aus Sicht einer Rolle, die Akzeptanzkriterien machen prüfbar, wann sie erfüllt ist.'},
     {cat:'A', color:'#2B7A78', q:'Was passiert in der Retrospektive am Ende eines Sprints?',
      options:['Die Ergebnisse werden an der Anlage vorgeführt','Das Team überlegt, wie es seine Zusammenarbeit verbessern kann (Start / Stop / Continue)','Alle Flows werden zurückgesetzt','Neue Schülerkonten werden angelegt'],
      correct:1, exp:'Die Vorführung ist das Sprint Review. Die Retro schaut auf den Arbeitsprozess selbst.'},
     {cat:'A', color:'#2B7A78', q:'Was geschieht automatisch, wenn ein Team im Node-RED-Editor auf „Deploy“ klickt?',
      options:['Die Änderung wird nach GitHub gepusht','Das Issue wird geschlossen','Der Flow-Stand wird als Commit gesichert und erscheint in Forgejo','Alle anderen Teams werden abgemeldet'],
      correct:2, exp:'Ein systemd-Dienst beobachtet flows.json und sichert jeden Deploy als Commit im Repo datenkrake-projekt. Nach GitHub geht nichts automatisch.'},
     {cat:'A', color:'#2B7A78', q:'Warum ist Kanban gut für die Arbeit in Unterrichtsblöcken geeignet?',
      options:['Weil es feste Arbeitszeiten von 8 Stunden vorschreibt','Weil es ohne Aufgabenliste auskommt','Weil nur die Lehrkraft das Board sehen darf','Weil der Stand jeder Aufgabe auch nach mehreren Tagen Pause auf einen Blick sichtbar ist'],
      correct:3, exp:'Zwischen den Blöcken liegen oft Tage. Das Board ist das gemeinsame Gedächtnis: wer macht was, was ist fertig, was hängt.'},
  ];

  // Buchstaben = Kapitel der Hauptseite (Navigation/Hero)
  var QUIZ_TOPICS = {
    A:'Agiles Arbeiten (Scrum light & Kanban)',
    B:'CRISP-DM',
    C:'Infrastruktur & Hardware',
    D:'Datenerhebung',
    E:'Kommunikation & Industrie 4.0',
    F:'Datenhaltung und -analyse',
    G:'Machine Learning',
    H:'Agentensysteme & KI-Integration'
  };

  function renderQuiz(){
    var container = document.getElementById('quizList');
    container.innerHTML = '';
    var topicOrder = ['A','B','C','D','E','F','G','H'];
    topicOrder.forEach(function(cat){
      var topic = document.createElement('details');
      topic.className = 'quiz-topic';
      topic.id = 'quizTopic'+cat;
      topic.dataset.cat = cat;
      topic.innerHTML = '<summary>'+ 
        '<h3 class="quiz-topic-title quiz-cat-'+cat.toLowerCase()+'">'+QUIZ_TOPICS[cat]+'</h3>'+
        '<span class="quiz-topic-score" id="quizTopicScore'+cat+'">0 von 0 richtig</span></summary>'+ 
        '<div class="quiz-topic-list"></div>';
      var topicList = topic.querySelector('.quiz-topic-list');
      QUIZ.forEach(function(item, qi){
        if (item.cat !== cat) return;
        var card = document.createElement('div');
        card.className = 'quiz-card quiz-border-'+item.cat.toLowerCase();
        var optsHtml = item.options.map(function(opt, oi){
          return '<label class="quiz-opt" data-qi="'+qi+'">'+
            '<input type="radio" name="q'+qi+'" value="'+oi+'"> <span>'+opt+'</span></label>';
        }).join('');
        card.innerHTML =
          '<div class="quiz-q">'+item.q+'</div>'+
          '<div class="quiz-opts">'+optsHtml+'</div>'+
          '<div class="quiz-exp" id="exp'+qi+'" hidden></div>';
        topicList.appendChild(card);
      });
      container.appendChild(topic);
    });
    container.querySelectorAll('input[type=radio]').forEach(function(input){
      input.addEventListener('change', function(){
        var qi = parseInt(input.closest('.quiz-opt').dataset.qi, 10);
        var oi = parseInt(input.value, 10);
        answerQuestion(qi, oi);
      });
    });
  }

  var quizState = {};

  function answerQuestion(qi, oi){
    if (quizState[qi] !== undefined) return;
    quizState[qi] = oi;
    var item = QUIZ[qi];
    var cardEls = document.querySelectorAll('.quiz-card');
    var card = cardEls[qi];
    var labels = card.querySelectorAll('.quiz-opt');
    labels.forEach(function(label, idx){
      label.querySelector('input').disabled = true;
      if (idx === item.correct) label.classList.add('correct');
      else if (idx === oi) label.classList.add('wrong');
    });
    var exp = document.getElementById('exp'+qi);
    exp.hidden = false;
    exp.textContent = (oi === item.correct ? '\u2713 Richtig. ' : '\u2717 Nicht ganz. ') + item.exp;
    updateQuizScore();
  }

  function updateQuizScore(){
    var answered = Object.keys(quizState).length;
    var correct = 0;
    Object.keys(quizState).forEach(function(qi){
      if (quizState[qi] === QUIZ[qi].correct) correct++;
    });
    var total = QUIZ.length;
    var fertig = answered === total;

    document.getElementById('quizScore').textContent =
      correct+' von '+answered+' richtig ('+total+' Fragen insgesamt)';

    // Stand pro Kapitel, auch für die Lernpfade (lernpfade.js)
    var stand = {};
    Object.keys(QUIZ_TOPICS).forEach(function(cat){
      var topicQuestions = QUIZ.filter(function(item){ return item.cat === cat; });
      var topicAnswered = 0;
      var topicCorrect = 0;
      topicQuestions.forEach(function(item){
        var qi = QUIZ.indexOf(item);
        if (quizState[qi] !== undefined){
          topicAnswered++;
          if (quizState[qi] === item.correct) topicCorrect++;
        }
      });
      document.getElementById('quizTopicScore'+cat).textContent =
        topicCorrect+' von '+topicAnswered+' richtig ('+topicQuestions.length+' Fragen)';
      stand[cat] = { richtig: topicCorrect, beantwortet: topicAnswered, gesamt: topicQuestions.length };
    });
    window.datenkrakeQuizStand = stand;
    document.dispatchEvent(new CustomEvent('quiz-stand', { detail: stand }));

    var floatScore = document.getElementById('quizFloatScore');
    var floatSub = document.getElementById('quizFloatSub');
    var floatLabel = document.getElementById('quizFloatLabel');
    var floatBox = document.getElementById('quizFloat');
    floatScore.textContent = correct+' / '+total;
    floatBox.classList.toggle('done', fertig);
    if (fertig){
      var prozent = Math.round((correct/total)*100);
      floatLabel.textContent = 'Quiz fertig!';
      floatSub.textContent = prozent+'% richtig';
    } else {
      floatLabel.textContent = 'Quiz-Punkte';
      floatSub.textContent = answered+' von '+total+' beantwortet';
    }
  }

  // Schwebende Punktzahl nur einblenden, während der Quiz-Bereich im
  // Sichtbereich ist - folgt beim Scrollen mit (position: fixed + CSS-Klasse).
  var quizFloatEl = document.getElementById('quizFloat');
  var quizSection = document.getElementById('quiz');
  if ('IntersectionObserver' in window){
    var quizObserver = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        quizFloatEl.classList.toggle('visible', entry.isIntersecting);
      });
    }, {threshold: 0.1});
    quizObserver.observe(quizSection);
  } else {
    // Fallback ohne IntersectionObserver: immer sichtbar sobald Quiz gerendert ist
    quizFloatEl.classList.add('visible');
  }

  document.getElementById('quizReset').addEventListener('click', function(){
    quizState = {};
    renderQuiz();
    updateQuizScore();
  });

  renderQuiz();
  updateQuizScore();
  async function loadCards(){
    var row = document.getElementById('cardsRow');
    row.innerHTML = '';
    var liveCount = 0;
    for (var i=0;i<CARD_DEFS.length;i++){
      var def = CARD_DEFS[i];
      var base = urlOf(def.field);
      try{
        var data = await fetchWithTimeout(base+def.path, 2000);
        row.appendChild(renderCard(def, data, true));
        liveCount++;
      } catch(e){
        row.appendChild(renderCard(def, def.fallback, false));
      }
    }
    var dot = document.getElementById('statusDot');
    var text = document.getElementById('statusText');
    dot.classList.toggle('live', liveCount>0);
    if(liveCount===0){
      text.textContent = 'keine Agenten erreichbar — zeige Demo-Daten';
    } else if (liveCount < CARD_DEFS.length){
      text.textContent = liveCount+' von '+CARD_DEFS.length+' Agenten live';
    } else {
      text.textContent = 'alle '+CARD_DEFS.length+' Agenten live';
    }
  }
  loadCards();
  ['urlOrchestrator','urlDb','urlReport','urlWartung'].forEach(function(id){
    document.getElementById(id).addEventListener('change', loadCards);
  });

  /* ---------------- Tabs ---------------- */
  document.querySelectorAll('.tab-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active');});
      document.querySelectorAll('.tab-panel').forEach(function(p){p.classList.remove('active');});
      btn.classList.add('active');
      document.getElementById('tab-'+btn.dataset.tab).classList.add('active');
    });
  });

  /* ---------------- LLM-Chat (LM Studio, OpenAI-kompatibel) ---------------- */
  var llmHistory = [];
  function addMsg(logEl, role, text){
    var div = document.createElement('div');
    div.className = 'msg '+role;
    div.textContent = text;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  async function sendLlm(){
    var input = document.getElementById('llmInput');
    var text = input.value.trim();
    if(!text) return;
    var log = document.getElementById('llmLog');
    addMsg(log, 'user', text);
    input.value = '';
    llmHistory.push({role:'user', content:text});
    var btn = document.getElementById('llmSend');
    btn.disabled = true;
    try{
      var endpoint = urlOf('urlLmStudio') + '/v1/chat/completions';
      var headers = {'Content-Type':'application/json'};
      var key = document.getElementById('lmKey').value.trim();
      if(key) headers['Authorization'] = 'Bearer '+key;
      var model = document.getElementById('lmModel').value.trim() || 'local-model';
      var res = await fetch(endpoint, {
        method:'POST', headers:headers,
        body: JSON.stringify({
          model: model,
          messages: [{role:'system', content:'Du hilfst beim Betrieb des Datenkrake-Agentensystems (MCP/A2A/LAP) an einer Berufsschule. Antworte kurz und konkret.'}]
            .concat(llmHistory),
          temperature:0.6
        })
      });
      if(!res.ok) throw new Error('HTTP '+res.status);
      var data = await res.json();
      var reply = data.choices && data.choices[0] && data.choices[0].message
        ? data.choices[0].message.content : '(keine Antwort erhalten)';
      addMsg(log, 'bot', reply);
      llmHistory.push({role:'assistant', content:reply});
    } catch(e){
      addMsg(log, 'sys', 'Fehler: '+e.message+' — läuft der LM-Studio-Server unter '+urlOf('urlLmStudio')+' ?');
    } finally {
      btn.disabled = false;
    }
  }
  document.getElementById('llmSend').addEventListener('click', sendLlm);
  document.getElementById('llmInput').addEventListener('keydown', function(e){ if(e.key==='Enter') sendLlm(); });

  /* ---------------- Agenten-Konsole (A2A best effort) ---------------- */
  async function sendAgent(){
    var select = document.getElementById('agentSelect');
    var input = document.getElementById('agentInput');
    var text = input.value.trim();
    if(!text) return;
    var log = document.getElementById('agentLog');
    addMsg(log, 'user', text);
    input.value = '';
    var btn = document.getElementById('agentSend');
    btn.disabled = true;
    try{
      var base = urlOf(select.value);
      var payload = {
        jsonrpc:'2.0',
        id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
        method:'message/send',
        params:{ message:{ role:'user', parts:[{type:'text', text:text}], messageId: String(Date.now()) } }
      };
      var res = await fetch(base+'/', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
      });
      var data = await res.json();
      addMsg(log, 'bot', JSON.stringify(data, null, 2));
    } catch(e){
      addMsg(log, 'sys', 'Fehler: '+e.message+' — RPC-Pfad/Format ggf. an eure a2a-sdk-Version anpassen.');
    } finally {
      btn.disabled = false;
    }
  }
  document.getElementById('agentSend').addEventListener('click', sendAgent);
  document.getElementById('agentInput').addEventListener('keydown', function(e){ if(e.key==='Enter') sendAgent(); });

  /* ---------------- Agenten-Graphen (LangGraph, Mermaid-Live-Abruf) ---------------- */
  if (window.mermaid) { mermaid.initialize({ startOnLoad: false, theme: 'neutral' }); }

  async function ladeAgentGraph(){
    var select = document.getElementById('graphSelect');
    var container = document.getElementById('graphContainer');
    var btn = document.getElementById('graphLoad');
    btn.disabled = true;
    container.innerHTML = '<div class="msg sys">Lade Graph…</div>';
    try{
      var base = urlOf(select.value);
      var res = await fetch(base+'/graph/mermaid');
      if(!res.ok) throw new Error('HTTP '+res.status);
      var mermaidText = await res.text();
      if(!window.mermaid) throw new Error('mermaid.js konnte nicht geladen werden');
      var render = await mermaid.render('agentGraph'+Date.now(), mermaidText);
      container.innerHTML = render.svg;
    } catch(e){
      container.innerHTML = '<div class="msg sys">Fehler: '+e.message+' — läuft der Agent unter '+urlOf(select.value)+' und erlaubt er CORS?</div>';
    } finally {
      btn.disabled = false;
    }
  }
  document.getElementById('graphLoad').addEventListener('click', ladeAgentGraph);
})();
