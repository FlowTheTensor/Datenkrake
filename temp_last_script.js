<script>
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
    var themaA = document.getElementById('thema-a');
    var themaB = document.getElementById('thema-b');
    var themaC = document.getElementById('thema-c');
    var themaD = document.getElementById('thema-d');
    var themaE = document.getElementById('thema-e');
    var themaML = document.getElementById('thema-ml');
    var quiz = document.getElementById('quiz');
    var chatPanel = document.getElementById('chatConsolePanel');
    if(!main || !themaA || !themaB || !themaC || !themaD || !themaE || !themaML || !quiz) return;

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
  wireKiLink('akustikUrl','akustikOpen');
  wireKiLink('orangeUrl','orangeOpen');
  wireKiLink('jupyterMlUrl','jupyterMlOpen');
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
    {cat:'E', color:'#C81E3A', q:'Was verbindet MCP typischerweise?',
     options:['Zwei Agenten miteinander','Ein Sprachmodell mit Werkzeugen/Daten','Zwei Datenbanken miteinander','Einen Menschen mit einem anderen Menschen'],
     correct:1, exp:'MCP ist die "vertikale" Kante: ein Modell greift auf Tools/Resources/Prompts eines Servers zu — z.B. Claude Desktop auf mcpserver.py.'},
    {cat:'E', color:'#C81E3A', q:'Wodurch entdeckt ein A2A-Agent die Fähigkeiten eines anderen Agenten?',
     options:['Über eine feste IP-Adressliste','Über ein MQTT-Topic','Über eine Agent Card unter /.well-known/agent-card.json','Über eine SQL-Abfrage'],
     correct:2, exp:'Die Agent Card ist das öffentliche "Türschild" eines A2A-Agenten mit seinen Skills.'},
    {cat:'E', color:'#C81E3A', q:'Wozu dient der Safety-Fence-Mechanismus in LAP?',
     options:['Er verschlüsselt die Verbindung','Er holt vor gefährlichen/irreversiblen Aktionen eine Bestätigung ein','Er reserviert Speicherplatz','Er startet den Container neu'],
     correct:1, exp:'Bevor eine als gefährlich markierte Aktion ausgeführt wird, muss sie explizit bestätigt werden — siehe Wartungs-Agent.'},
    {cat:'E', color:'#C81E3A', q:'Was macht ein "Agent Harness" konkret?',
     options:['Er trainiert das neuronale Netz','Er speichert Messwerte in der Datenbank','Er verschickt MQTT-Nachrichten','Er wechselt zwischen LLM-Aufruf und Tool-Ausführung ab, bis das Modell fertig ist'],
     correct:3, exp:'Genau diese Schleife macht aus einem rohen Sprachmodell etwas, das selbstständig Werkzeuge nutzen kann.'},

    {cat:'B', color:'#B87A1C', q:'Womit trainiert der Arduino UNO Q sein Klassifikationsmodell?',
     options:['Nur mit dem Label','Mit Label und vollständigem FFT-Spektrum aus der MariaDB','Mit Daten aus InfluxDB','Mit zufällig erzeugten Daten'],
     correct:1, exp:'Der Historian speichert das Spektrum bewusst nicht — nur die MariaDB hat die vollständigen Trainingsdaten.'},
    {cat:'B', color:'#B87A1C', q:'Was macht Nessie im Data-Lake-Stack besonders?',
     options:['Es ist ein Objektspeicher','Es ersetzt MariaDB','Es bietet Git-artige Versionierung (Branches, Commits) für Tabellen','Es ist ein Backup-Programm'],
     correct:2, exp:'Tabellen lassen sich branchen, committen und zusammenführen — "Git für Daten".'},
    {cat:'B', color:'#B87A1C', q:'Ist die YOLO-Anbindung im aktuellen Projektstand schon vollständig umgesetzt?',
     options:['Ja, vollständig','Nein, sie ist bewusst als "geplant" markiert','Nur auf dem Data-Lake-Rechner','Nur in der Simulation'],
     correct:1, exp:'Ehrlich im Dashboard gekennzeichnet, um nichts vorzugaukeln, was noch nicht existiert.'},
    {cat:'B', color:'#B87A1C', q:'Warum läuft der Data-Lake-Stack NICHT auf dem Raspberry Pi?',
     options:['Kein Netzwerkzugang','Spark/Jupyter sind zu ressourcenhungrig für den Pi','MinIO läuft nur auf x86','Der Pi unterstützt kein Docker'],
     correct:1, exp:'Deshalb läuft der Stack als eigener Compose-Stack auf einem separaten, stärkeren Rechner.'},

    {cat:'D', color:'#2F6B4F', q:'Was speichert der Operational Historian (InfluxDB) bewusst NICHT?',
     options:['Den Zeitstempel','Das vollständige FFT-Spektrum-Array','Den peak_db-Wert','Das Label'],
     correct:1, exp:'Zeitreihen-Datenbanken sind für skalare Werte optimiert, nicht für große verschachtelte Strukturen.'},
    {cat:'D', color:'#2F6B4F', q:'Wie nennt man das Prinzip, bewusst mehrere Datenbanktypen parallel einzusetzen?',
     options:['Sharding','Normalisierung','Replikation','Polyglot Persistence'],
     correct:3, exp:'Ein etabliertes Architekturprinzip, kein Sonderfall dieses Projekts.'},
    {cat:'D', color:'#2F6B4F', q:'Welche Datenbank bleibt die einzige VOLLSTÄNDIGE Quelle für Trainingsdaten?',
     options:['InfluxDB','MinIO','MariaDB','Nessie'],
     correct:2, exp:'Nur dort liegen Label UND vollständiges Spektrum zusammen.'},
    {cat:'D', color:'#2F6B4F', q:'Ab wann lohnt sich ein Operational Historian laut Projekt-Einschätzung wirklich?',
     options:['Sofort, unabhängig von der Anlagengröße','Erst bei mehreren Sensoren/Stationen, hoher Frequenz oder Bedarf an Datenalterung','Nie, er ist überflüssig','Nur ohne SQL-Datenbank'],
     correct:1, exp:'Für einen einzelnen Sensor ist er aktuell eher Lerninhalt als operative Notwendigkeit.'},

    {cat:'C', color:'#2A5F8A', q:'Welches Kommunikationsmuster nutzt MQTT?',
     options:['Publish/Subscribe','Request/Response','Peer-to-Peer-Streaming','Broadcast ohne Empfänger'],
     correct:0, exp:'Der Sender weiß nicht, wer (oder ob überhaupt jemand) mithört.'},
    {cat:'C', color:'#2A5F8A', q:'Was macht Node-RED in diesem Projekt?',
     options:['Es trainiert neuronale Netze','Es liest OPC-UA-Tags und veröffentlicht sie per MQTT','Es ist die Hauptdatenbank','Es ersetzt Mosquitto'],
     correct:1, exp:'Eine Low-Code-Brücke zwischen SPS-Welt (OPC-UA) und IoT-Welt (MQTT).'},
    {cat:'C', color:'#2A5F8A', q:'Welches Protokoll ist der klassische Industriestandard für Maschinenkommunikation?',
     options:['MQTT','HTTP','OPC-UA','FTP'],
     correct:2, exp:'S7-1500/ET200SP & Co. sprechen typischerweise OPC-UA.'},
    {cat:'C', color:'#2A5F8A', q:'Auf welchem MQTT-Topic-Namensraum landen die aus OPC-UA gelesenen SPS-Werte?',
     options:['audio/spectrum','sensor/data','opcua/raw','plc/<station>/<tag>'],
     correct:3, exp:'Bewusst getrennt vom bestehenden audio/spectrum-Topic.'},

    {cat:'A', color:'#5B5852', q:'Warum laufen die Dienste dieses Projekts in Docker-Containern?',
     options:['Pflicht unter Raspberry Pi OS','Für Isolation und reproduzierbare Installation','Weil Python das erfordert','Um Strom zu sparen'],
     correct:1, exp:'Jeder Dienst läuft unabhängig vom restlichen System — leicht neu aufsetzbar.'},
    {cat:'A', color:'#5B5852', q:'Was ist die Besonderheit des Arduino UNO Q gegenüber einem klassischen Arduino?',
     options:['Mehr USB-Ports','Er hat einen Linux-Teil und kann selbst KI-Inferenz rechnen','Nur für Audio gebaut','Er braucht kein Netzwerk'],
     correct:1, exp:'Genau das macht ihn zum Beispiel für Edge AI in diesem Projekt.'},
    {cat:'A', color:'#5B5852', q:'Welche Rolle spielt der Raspberry Pi in der Gesamtarchitektur?',
     options:['Nur ein Backup-Gerät','Der zentrale Edge-Server (Broker, DB, Historian, Webserver)','Er trainiert das neuronale Netz','Er ersetzt Claude Desktop'],
     correct:1, exp:'Die "Datenkrake" bündelt hier alle zentralen Dienste an einer Stelle.'},

    {cat:'E', color:'#C81E3A', q:'Was ist die Aufgabe des Orchestrator-Agenten?',
     options:['Er misst die Temperatur','Er verteilt Aufgaben an passende Fachagenten','Er ersetzt die Datenbank','Er rendert das Dashboard'],
     correct:1, exp:'Der Orchestrator nimmt eine Anfrage entgegen und delegiert sie an den zuständigen Agenten.'},
    {cat:'B', color:'#B87A1C', q:'Was ist ein Label bei überwachtem Lernen?',
     options:['Die erwartete Klasse oder Zielausgabe eines Trainingsbeispiels','Der Name des MQTT-Brokers','Ein Datenbankpasswort','Die IP-Adresse des Sensors'],
     correct:0, exp:'Das Label beschreibt, was das Modell für die Eingabedaten lernen soll.'},
    {cat:'D', color:'#2F6B4F', q:'Warum werden Messdaten in unterschiedlichen Datenbanken gespeichert?',
     options:['Weil jede Datenbank zufällig ausgewählt wird','Weil verschiedene Zugriffsmuster unterschiedliche Speicherlösungen verlangen','Damit Daten doppelt verloren gehen können','Weil SQL keine Messwerte speichern kann'],
     correct:1, exp:'Die Architektur nutzt je nach Aufgabe die passende Stärke von MariaDB, InfluxDB und dem Data Lake.'},
    {cat:'C', color:'#2A5F8A', q:'Was ist der Vorteil von OPC UA gegenüber einer einfachen Rohdatenverbindung?',
     options:['Es liefert nur Binärwerte','Es bringt ein standardisiertes, beschreibbares Informationsmodell mit','Es benötigt keinen Server','Es funktioniert nur ohne Netzwerk'],
     correct:1, exp:'OPC UA beschreibt neben Werten auch Typen, Metadaten und die Struktur der Anlage.'},
    {cat:'A', color:'#5B5852', q:'Warum werden Container für die einzelnen Dienste getrennt?',
     options:['Damit jeder Dienst unabhängig aktualisiert und betrieben werden kann','Damit alle Dienste dieselben Dateien überschreiben','Damit kein Netzwerk nötig ist','Damit Hardware überflüssig wird'],
     correct:0, exp:'Getrennte Container begrenzen Abhängigkeiten und machen Betrieb sowie Wartung reproduzierbarer.'},
    {cat:'F', color:'#7A4E2D', q:'Was ist der Zweck eines Historian-Systems?',
     options:['Historische Messwerte zeitbezogen zu speichern und abfragbar zu machen','Agenten zu trainieren, ohne Daten zu speichern','OPC-UA-Geräte zu programmieren','Container-Images zu bauen'],
     correct:0, exp:'Ein Historian bewahrt Zeitreihen auf, damit Verläufe, Zustände und Trends später analysiert werden können.'}
  ];

  var QUIZ_TOPICS = {
    E:'Agentensysteme & KI-Integration',
    F:'Datenerhebung',
    B:'Machine Learning',
    D:'Datenhaltung und -analyse',
    C:'Kommunikation & Industrie 4.0',
    A:'Infrastruktur & Hardware'
  };

  function renderQuiz(){
    var container = document.getElementById('quizList');
    container.innerHTML = '';
    var topicOrder = ['E','F','B','D','C','A'];
    topicOrder.forEach(function(cat){
      var topic = document.createElement('section');
      topic.className = 'quiz-topic';
      topic.dataset.cat = cat;
      topic.innerHTML = '<div class="quiz-topic-head">'+
        '<h3 class="quiz-topic-title quiz-cat-'+cat.toLowerCase()+'">'+QUIZ_TOPICS[cat]+'</h3>'+
        '<span class="quiz-topic-score" id="quizTopicScore'+cat+'">0 von 0 richtig</span></div>'+
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
          '<div class="quiz-cat quiz-cat-'+item.cat.toLowerCase()+'">Thema '+item.cat+'</div>'+
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
    });

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

  /* ---------------- Technologie-Übersicht ---------------- */
  var TECH = [
    { group:'Protokolle & Kommunikation', items:[
      ['MCP','Verbindet ein KI-Modell mit externen Werkzeugen und Daten — Tools, Resources, Prompts. Die "vertikale" Kante.'],
      ['JSON-RPC','Leichtgewichtiges Aufrufprotokoll über JSON — technische Basis von MCP und A2A.'],
      ['A2A','Verbindet mehrere eigenständige Agenten über Agent Cards, Skills und Tasks. Die "horizontale" Kante.'],
      ['LAP','Verbindet einen Agenten mit einem physischen Gerät — Reservation, Safety-Fence, MeasurementResult.'],
      ['MQTT','Publish/Subscribe-Protokoll für IoT-Geräte — verbindet Arduino und Raspberry Pi.']
    ]},
    { group:'Daten & KI', items:[
      ['Neuronale Netze','Lernen aus Beispieldaten (z. B. Audiospektren), um Muster wie Anomalien zu erkennen.'],
      ['YOLO','Echtzeit-Objekterkennung auf Kamerabildern, hier zur Erkennung des Werkstückträger-Durchlaufs.'],
      ['SQL','Abfragesprache für relationale Datenbanken wie die MariaDB der Datenkrake.'],
      ['Operational Historian','Spezialisierte Zeitreihen-Datenbank für Prozess- und Sensordaten.'],
      ['Kafka','Verteiltes Streaming-System für hohe Datenmengen in Echtzeit.'],
      ['MinIO','S3-kompatibler Objektspeicher, z. B. für Rohdaten oder Modelldateien.'],
      ['Nessie','Git-artige Versionierung für Data-Lake-Tabellen.'],
      ['Spark','Verteiltes Framework für die Verarbeitung großer Datenmengen.']
    ]},
    { group:'Hardware & Infrastruktur', items:[
      ['RFID','Funkbasierte Kennzeichnung, hier zur Rückverfolgung der Werkstückträger.'],
      ['Docker','Containerisierung — jeder Dienst läuft isoliert und reproduzierbar.'],
      ['Arduino UNO Q','Mikrocontroller mit Linux-Anteil, erfasst hier Audio und rechnet KI-Inferenz.'],
      ['Raspberry Pi','Kleincomputer, hier als "Datenkrake" — sammelt und speichert Sensordaten.'],
      ['IoT','Vernetzte Sensoren und Geräte, die Daten automatisiert austauschen.']
    ]},
    { group:'Sprachmodelle & Zugriff', items:[
      ['Lokale LLMs (LM Studio)','Sprachmodelle, die auf eigener Hardware laufen statt in der Cloud.'],
      ['API-Key','Geheimer Schlüssel zur Authentifizierung gegenüber einer Schnittstelle.']
    ]}
  ];
  var techEl = document.getElementById('techGroups');
  TECH.forEach(function(g){
    var wrap = document.createElement('div');
    wrap.className = 'tech-group';
    var grid = g.items.map(function(it){
      return '<div class="tech-card"><div class="t">'+it[0]+'</div><div class="d">'+it[1]+'</div></div>';
    }).join('');
    wrap.innerHTML = '<h3>'+g.group+'</h3><div class="tech-grid">'+grid+'</div>';
    techEl.appendChild(wrap);
  });

})();
</script>
</body>
</html>
