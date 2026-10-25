(function(){
  "use strict";

  /* Lernpfade: Daten aus content/lernpfade.json.
     Gewählter Pfad und erledigte Schritte bleiben im localStorage dieses Browsers,
     der Quiz-Stand kommt live aus index.js (Ereignis „quiz-stand“). */

  var KAPITEL = {
    A:['thema-projekt','Agiles Arbeiten'], B:['thema-crispdm','Theoretischer Unterbau'],
    C:['thema-e','Infrastruktur'], D:['thema-b','Datenerhebung'],
    E:['thema-d','Kommunikation'], F:['thema-c','Datenhaltung und -analyse'],
    G:['thema-ml','Machine Learning'], H:['thema-a','Agentensysteme']
  };
  var SPEICHER = 'datenkrake-lernpfade-v1';

  var pfade = [];
  var zustand = laden();

  function laden(){
    try {
      var z = JSON.parse(localStorage.getItem(SPEICHER) || 'null');
      if(z && typeof z === 'object') return { aktiv: z.aktiv || null, erledigt: z.erledigt || {} };
    } catch(e){}
    return { aktiv: null, erledigt: {} };
  }
  function speichern(){
    try { localStorage.setItem(SPEICHER, JSON.stringify(zustand)); } catch(e){}
  }

  function el(tag, cls, text){
    var e = document.createElement(tag);
    if(cls) e.className = cls;
    if(text != null) e.textContent = text;
    return e;
  }
  function erledigtVon(p){ return zustand.erledigt[p.id] || []; }
  function istFertig(p){ return erledigtVon(p).length >= p.schritte.length; }
  function pfadById(id){ return pfade.filter(function(p){ return p.id === id; })[0] || null; }

  fetch('content/lernpfade.json')
    .then(function(res){
      if(!res.ok) throw new Error('content/lernpfade.json: '+res.status);
      return res.json();
    })
    .then(function(daten){
      pfade = daten.pfade || [];
      if(zustand.aktiv && !pfadById(zustand.aktiv)) zustand.aktiv = null;
      alles();
    })
    .catch(function(err){
      var wahl = document.getElementById('lpWahl');
      if(wahl) wahl.textContent = 'Lernpfade konnten nicht geladen werden: '+err.message;
    });

  document.addEventListener('quiz-stand', function(){ zeigeQuiz(); });

  function alles(){
    baueWahl();
    bauePfad();
    baueAbzeichen();
    baueKapitelHinweise();
  }

  /* ---------------- Pfadauswahl ---------------- */
  function baueWahl(){
    var wahl = document.getElementById('lpWahl');
    if(!wahl) return;
    wahl.innerHTML = '';
    pfade.forEach(function(p){
      var karte = el('button', 'lp-karte');
      karte.type = 'button';
      karte.setAttribute('role', 'tab');
      karte.setAttribute('aria-selected', zustand.aktiv === p.id ? 'true' : 'false');
      karte.setAttribute('aria-controls', 'lpPfad');
      var kopf = el('div', 'lp-karte-kopf');
      kopf.appendChild(el('span', 'lp-icon', p.icon));
      kopf.appendChild(el('span', 'lp-karte-titel', p.titel));
      karte.appendChild(kopf);
      karte.appendChild(el('span', 'lp-karte-fuer', p.fuer));
      var fuss = el('span', 'lp-karte-fuss');
      var n = erledigtVon(p).length;
      fuss.appendChild(el('span', null, p.schritte.length+' Schritte · '+p.dauer));
      fuss.appendChild(el('span', 'lp-karte-stand' + (istFertig(p) ? ' fertig' : ''),
        istFertig(p) ? p.abzeichen.icon+' geschafft' : (n ? n+' / '+p.schritte.length : '')));
      karte.appendChild(fuss);
      karte.addEventListener('click', function(){
        zustand.aktiv = zustand.aktiv === p.id ? null : p.id;
        speichern();
        alles();
        if(zustand.aktiv) document.getElementById('lpPfad').scrollIntoView({behavior:'smooth', block:'start'});
      });
      wahl.appendChild(karte);
    });
  }

  /* ---------------- aktiver Pfad ---------------- */
  function bauePfad(){
    var box = document.getElementById('lpPfad');
    if(!box) return;
    var p = pfadById(zustand.aktiv);
    box.innerHTML = '';
    box.hidden = !p;
    if(!p) return;
    var erledigt = erledigtVon(p);

    var kopf = el('div', 'lp-pfad-kopf');
    kopf.appendChild(el('h3', null, p.icon+' '+p.titel));
    var verlassen = el('button', 'lp-klein', 'Pfad schließen');
    verlassen.type = 'button';
    verlassen.addEventListener('click', function(){ zustand.aktiv = null; speichern(); alles(); });
    kopf.appendChild(verlassen);
    box.appendChild(kopf);

    var balken = el('div', 'lp-balken');
    balken.setAttribute('role', 'progressbar');
    balken.setAttribute('aria-valuemin', '0');
    balken.setAttribute('aria-valuemax', String(p.schritte.length));
    balken.setAttribute('aria-valuenow', String(erledigt.length));
    balken.setAttribute('aria-label', 'Fortschritt im Pfad');
    var fuellung = el('div', 'lp-balken-fuellung');
    fuellung.style.width = Math.round(100 * erledigt.length / p.schritte.length)+'%';
    balken.appendChild(fuellung);
    box.appendChild(balken);
    box.appendChild(el('div', 'lp-stand', erledigt.length+' von '+p.schritte.length+' Schritten erledigt'));

    if(istFertig(p)){
      var ab = el('div', 'lp-geschafft');
      ab.appendChild(el('span', 'lp-geschafft-icon', p.abzeichen.icon));
      var t = el('div');
      t.appendChild(el('b', null, 'Abzeichen „'+p.abzeichen.name+'“'));
      t.appendChild(el('div', null, 'Ihr habt alle Schritte dieses Pfads geschafft. Wie wäre es mit einem zweiten Pfad?'));
      ab.appendChild(t);
      box.appendChild(ab);
    }

    var liste = el('ol', 'lp-schritte');
    var naechster = -1;
    p.schritte.forEach(function(s, i){
      var fertig = erledigt.indexOf(i) !== -1;
      if(!fertig && naechster === -1) naechster = i;
      var li = el('li', 'lp-schritt' + (fertig ? ' fertig' : '') + (i === naechster ? ' naechster' : ''));
      li.id = 'lp-schritt-'+(i+1);

      var check = el('input');
      check.type = 'checkbox';
      check.checked = fertig;
      check.id = 'lp-check-'+p.id+'-'+i;
      check.setAttribute('aria-label', 'Schritt '+(i+1)+' erledigt');
      check.addEventListener('change', function(){
        var liste = erledigtVon(p).filter(function(x){ return x !== i; });
        if(check.checked) liste.push(i);
        zustand.erledigt[p.id] = liste.sort(function(a,b){ return a-b; });
        speichern();
        alles();
        var neu = document.getElementById('lp-check-'+p.id+'-'+i);
        if(neu) neu.focus();
      });
      li.appendChild(check);

      var inhalt = el('div', 'lp-schritt-inhalt');
      var titel = el('div', 'lp-schritt-titel');
      titel.appendChild(el('span', 'lp-nr', String(i+1)));
      var lbl = el('label', null, s.titel);
      lbl.htmlFor = check.id;
      titel.appendChild(lbl);
      if(s.kapitel && KAPITEL[s.kapitel]){
        titel.appendChild(el('span', 'lp-kap', 'Kapitel '+s.kapitel+' · '+KAPITEL[s.kapitel][1]));
      }
      inhalt.appendChild(titel);
      inhalt.appendChild(el('p', 'lp-aufgabe', s.aufgabe));

      var aktionen = el('div', 'lp-aktionen');
      if(s.kapitel && KAPITEL[s.kapitel]){
        var zum = el('a', 'lp-btn', 'Zum Kapitel →');
        zum.href = '#'+KAPITEL[s.kapitel][0];
        zum.addEventListener('click', function(e){
          var ziel = zielVon(s);
          if(ziel){ e.preventDefault(); ziel.scrollIntoView({behavior:'smooth', block:'start'}); }
        });
        aktionen.appendChild(zum);
      }
      if(s.link){
        var l = el('a', 'lp-btn', (s.linkText || 'Öffnen')+' ↗');
        l.href = s.link;
        if(/^https?:/.test(s.link)){ l.target = '_blank'; l.rel = 'noopener'; }
        aktionen.appendChild(l);
      }
      if(s.aktion){
        if(s.aktion.klick){
          var b = el('button', 'lp-btn', s.aktion.text);
          b.type = 'button';
          b.addEventListener('click', function(){
            var knopf = document.getElementById(s.aktion.klick);
            if(knopf) knopf.click();
          });
          aktionen.appendChild(b);
        } else if(s.aktion.link){
          var a = el('a', 'lp-btn', s.aktion.text+' ↗');
          a.href = s.aktion.link;
          a.target = '_blank'; a.rel = 'noopener';
          aktionen.appendChild(a);
        }
      }
      if(s.kapitel && KAPITEL[s.kapitel]){
        var q = el('button', 'lp-btn lp-quiz');
        q.type = 'button';
        q.setAttribute('data-kap', s.kapitel);
        q.addEventListener('click', function(){
          var d = document.getElementById('quizTopic'+s.kapitel);
          if(!d) return;
          d.open = true;
          d.scrollIntoView({behavior:'smooth', block:'start'});
        });
        aktionen.appendChild(q);
      }
      inhalt.appendChild(aktionen);
      li.appendChild(inhalt);
      liste.appendChild(li);
    });
    box.appendChild(liste);

    var zurueck = el('button', 'lp-klein', 'Fortschritt dieses Pfads zurücksetzen');
    zurueck.type = 'button';
    zurueck.addEventListener('click', function(){
      if(!confirm('Alle Haken in „'+p.titel+'“ entfernen?')) return;
      delete zustand.erledigt[p.id];
      speichern();
      alles();
    });
    box.appendChild(zurueck);
    zeigeQuiz();
  }

  function zielVon(s){
    var sek = document.getElementById(KAPITEL[s.kapitel][0]);
    if(!s.anker) return sek;
    return document.getElementById(s.anker) || (sek && sek.querySelector('.'+s.anker)) || sek;
  }

  function zeigeQuiz(){
    var stand = window.datenkrakeQuizStand || {};
    document.querySelectorAll('.lp-quiz').forEach(function(b){
      var k = stand[b.getAttribute('data-kap')];
      if(k && k.beantwortet){
        b.textContent = '✎ Quiz '+b.getAttribute('data-kap')+': '+k.richtig+' von '+k.gesamt+' richtig';
        b.classList.toggle('gut', k.richtig >= Math.ceil(k.gesamt * 0.7));
      } else {
        b.textContent = '✎ Quiz zu Kapitel '+b.getAttribute('data-kap');
        b.classList.remove('gut');
      }
    });
  }

  /* ---------------- gesammelte Abzeichen ---------------- */
  function baueAbzeichen(){
    var box = document.getElementById('lpAbzeichen');
    if(!box) return;
    var fertige = pfade.filter(istFertig);
    box.innerHTML = '';
    box.hidden = !fertige.length;
    if(!fertige.length) return;
    box.appendChild(el('span', 'lp-abzeichen-lbl', 'Eure Abzeichen'));
    fertige.forEach(function(p){
      var a = el('span', 'lp-badge');
      a.appendChild(el('span', null, p.abzeichen.icon));
      a.appendChild(el('span', null, p.abzeichen.name));
      a.title = 'Lernpfad „'+p.titel+'“ geschafft';
      box.appendChild(a);
    });
  }

  /* ---------------- Hinweis im Kapitel ---------------- */
  function baueKapitelHinweise(){
    document.querySelectorAll('.lp-chip').forEach(function(c){ c.remove(); });
    var p = pfadById(zustand.aktiv);
    if(!p) return;
    var erledigt = erledigtVon(p);
    var proKapitel = {};
    p.schritte.forEach(function(s, i){
      if(!s.kapitel || !KAPITEL[s.kapitel]) return;
      (proKapitel[s.kapitel] = proKapitel[s.kapitel] || []).push(i);
    });
    Object.keys(proKapitel).forEach(function(k){
      var kopf = document.querySelector('#'+KAPITEL[k][0]+' .theme-head');
      if(!kopf) return;
      var nummern = proKapitel[k];
      var alleFertig = nummern.every(function(i){ return erledigt.indexOf(i) !== -1; });
      var offen = nummern.filter(function(i){ return erledigt.indexOf(i) === -1; })[0];
      var ziel = offen != null ? offen : nummern[0];
      var chip = el('a', 'lp-chip' + (alleFertig ? ' fertig' : ''),
        p.icon+' '+p.titel+' · '+(nummern.length > 1 ? 'Schritte ' : 'Schritt ')+
        nummern.map(function(i){ return i+1; }).join(', ')+' von '+p.schritte.length+(alleFertig ? ' ✓' : ''));
      chip.href = '#lp-schritt-'+(ziel+1);
      chip.title = p.schritte[ziel].titel+': '+p.schritte[ziel].aufgabe;
      kopf.appendChild(chip);
    });
  }
})();
