(function(){
  "use strict";

  /* Glossar: Daten aus content/glossar.json.
     1. baut den Glossar-Bereich (#glossar) mit Suche und Kategorie-Filter
     2. markiert Fachbegriffe in den Kapiteln und zeigt beim Zeigen/Antippen einen Tooltip */

  var KAPITEL = {
    A:['thema-projekt','Agiles Arbeiten'],
    B:['thema-crispdm','Theoretischer Unterbau'],
    C:['thema-e','Infrastruktur'],
    D:['thema-b','Datenerhebung'],
    E:['thema-d','Kommunikation'],
    F:['thema-c','Datenhaltung und -analyse'],
    G:['thema-ml','Machine Learning'],
    H:['thema-a','Agentensysteme']
  };

  /* Hier wird nicht markiert: Links, Bedienelemente, Code, Überschriften, Diagramme,
     das Glossar selbst und das Quiz (Tooltips würden dort Antworten verraten). */
  var NICHT_MARKIEREN = 'a,button,code,pre,script,style,svg,textarea,select,option,input,label,' +
    'h1,h2,h3,h4,.eyebrow,.theme-letter,.gl-term,#glossar,#quiz,#chatConsolePanel,[data-kein-glossar]';

  function el(tag, cls, text){
    var e = document.createElement(tag);
    if(cls) e.className = cls;
    if(text != null) e.textContent = text;
    return e;
  }

  function escapeRegex(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  fetch('content/glossar.json')
    .then(function(res){
      if(!res.ok) throw new Error('content/glossar.json: '+res.status);
      return res.json();
    })
    .then(function(daten){
      var begriffe = daten.begriffe.slice().sort(function(a,b){
        return a.begriff.localeCompare(b.begriff, 'de');
      });
      var nachId = {};
      begriffe.forEach(function(b){ nachId[b.id] = b; });
      baueGlossar(begriffe, daten.kategorien, nachId);
      markiereBegriffe(begriffe, nachId);
      springeZuHash();
    })
    .catch(function(err){
      var liste = document.getElementById('glossarListe');
      if(liste) liste.textContent = 'Glossar konnte nicht geladen werden: '+err.message;
    });

  /* ---------------- Glossar-Bereich ---------------- */
  function baueGlossar(begriffe, kategorien, nachId){
    var liste = document.getElementById('glossarListe');
    var suche = document.getElementById('glossarSuche');
    var filterEl = document.getElementById('glossarFilter');
    var anzahl = document.getElementById('glossarAnzahl');
    if(!liste) return;

    var karten = begriffe.map(function(b){
      var karte = el('article', 'gl-card');
      karte.id = 'glossar-'+b.id;
      var kopf = el('div', 'gl-card-head');
      kopf.appendChild(el('h3', 'gl-card-title', b.begriff));
      kopf.appendChild(el('span', 'gl-card-cat', b.kategorie));
      karte.appendChild(kopf);
      karte.appendChild(el('p', 'gl-card-kurz', b.kurz));
      if(b.datenkrake){
        var dk = el('p', 'gl-card-dk');
        dk.appendChild(el('b', null, 'Bei der Datenkrake: '));
        dk.appendChild(document.createTextNode(b.datenkrake));
        karte.appendChild(dk);
      }
      var fuss = el('div', 'gl-card-foot');
      (b.kapitel || []).forEach(function(k){
        if(!KAPITEL[k]) return;
        var a = el('a', 'gl-kap', k+' · '+KAPITEL[k][1]);
        a.href = '#'+KAPITEL[k][0];
        fuss.appendChild(a);
      });
      (b.siehe || []).forEach(function(id){
        if(!nachId[id]) return;
        var a = el('a', 'gl-siehe', '→ '+nachId[id].begriff);
        a.href = '#glossar-'+id;
        a.addEventListener('click', function(e){ e.preventDefault(); zeigeEintrag(id); });
        fuss.appendChild(a);
      });
      if(fuss.childNodes.length) karte.appendChild(fuss);
      liste.appendChild(karte);
      return {
        el: karte,
        kategorie: b.kategorie,
        text: [b.begriff, b.kurz, b.datenkrake || ''].concat(b.treffer || []).join(' ').toLowerCase()
      };
    });

    var aktiveKategorie = '';
    function filtern(){
      var q = (suche.value || '').trim().toLowerCase();
      var sichtbar = 0;
      karten.forEach(function(k){
        var ok = (!aktiveKategorie || k.kategorie === aktiveKategorie) && (!q || k.text.indexOf(q) !== -1);
        k.el.hidden = !ok;
        if(ok) sichtbar++;
      });
      anzahl.textContent = sichtbar === karten.length
        ? karten.length+' Begriffe'
        : sichtbar+' von '+karten.length+' Begriffen';
    }

    ['Alle'].concat(kategorien).forEach(function(kat, i){
      var chip = el('button', 'gl-chip'+(i === 0 ? ' active' : ''), kat);
      chip.type = 'button';
      chip.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
      chip.addEventListener('click', function(){
        aktiveKategorie = i === 0 ? '' : kat;
        filterEl.querySelectorAll('.gl-chip').forEach(function(c){
          c.classList.toggle('active', c === chip);
          c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
        });
        filtern();
      });
      filterEl.appendChild(chip);
    });
    suche.addEventListener('input', filtern);
    filtern();
  }

  function zeigeEintrag(id){
    var karte = document.getElementById('glossar-'+id);
    if(!karte) return;
    // Filter zurücksetzen, falls die Karte gerade ausgeblendet ist
    if(karte.hidden){
      var suche = document.getElementById('glossarSuche');
      suche.value = '';
      var alle = document.querySelector('#glossarFilter .gl-chip');
      if(alle) alle.click();
    }
    // offene Overlays schließen, sonst verdecken sie das Glossar
    document.querySelectorAll('[id$="Overlay"].open').forEach(function(o){ o.classList.remove('open'); });
    document.body.style.overflow = '';
    if(history.replaceState) history.replaceState(null, '', '#glossar-'+id);
    karte.scrollIntoView({behavior:'smooth', block:'center'});
    karte.classList.remove('gl-flash');
    void karte.offsetWidth;
    karte.classList.add('gl-flash');
  }

  function springeZuHash(){
    var m = /^#glossar-(.+)$/.exec(location.hash);
    if(m) zeigeEintrag(decodeURIComponent(m[1]));
  }
  window.addEventListener('hashchange', springeZuHash);

  /* ---------------- Begriffe in den Kapiteln markieren ---------------- */
  function markiereBegriffe(begriffe, nachId){
    var trefferZuId = {};
    var alleTreffer = [];
    begriffe.forEach(function(b){
      (b.treffer || []).forEach(function(t){
        if(!trefferZuId[t]){ trefferZuId[t] = b.id; alleTreffer.push(t); }
      });
    });
    if(!alleTreffer.length) return;
    // längste Schreibweise zuerst, damit „Anomalie-Poller“ vor „Anomalie“ greift
    alleTreffer.sort(function(a,b){ return b.length - a.length; });
    var muster = new RegExp('(^|[^\\p{L}\\p{N}_])(' + alleTreffer.map(escapeRegex).join('|') + ')(?![\\p{L}\\p{N}_])', 'gu');

    // pro Kapitel bzw. Overlay nur das erste Vorkommen markieren
    var bereits = new Map();
    function bereichVon(node){
      return node.closest('[id$="Overlay"]') || node.closest('main > section') || node.closest('#heroContent');
    }

    [document.getElementById('heroContent'), document.getElementById('mainContent')].forEach(function(wurzel){
      if(!wurzel) return;
      var walker = document.createTreeWalker(wurzel, NodeFilter.SHOW_TEXT, {
        acceptNode: function(n){
          if(!n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
          return n.parentElement.closest(NICHT_MARKIEREN) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
        }
      });
      var knoten = [];
      while(walker.nextNode()) knoten.push(walker.currentNode);

      knoten.forEach(function(textNode){
        var bereich = bereichVon(textNode.parentElement);
        if(!bereich) return;
        if(!bereits.has(bereich)) bereits.set(bereich, {});
        var schonDa = bereits.get(bereich);

        var text = textNode.nodeValue;
        var frag = null, letzte = 0, m;
        muster.lastIndex = 0;
        while((m = muster.exec(text))){
          var id = trefferZuId[m[2]];
          if(schonDa[id]) continue;
          schonDa[id] = true;
          var start = m.index + m[1].length;
          frag = frag || document.createDocumentFragment();
          frag.appendChild(document.createTextNode(text.slice(letzte, start)));
          var term = el('button', 'gl-term', m[2]);
          term.type = 'button';
          term.setAttribute('data-gl', id);
          term.setAttribute('aria-expanded', 'false');
          frag.appendChild(term);
          letzte = start + m[2].length;
        }
        if(frag){
          frag.appendChild(document.createTextNode(text.slice(letzte)));
          textNode.parentNode.replaceChild(frag, textNode);
        }
      });
    });

    richteTooltipEin(nachId);
  }

  /* ---------------- Tooltip ---------------- */
  function richteTooltipEin(nachId){
    var tip = el('div', 'gl-tip');
    tip.id = 'glTip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    var tipTitel = el('div', 'gl-tip-title');
    var tipText = el('div', 'gl-tip-text');
    var tipLink = el('a', 'gl-tip-link', 'Mehr im Glossar →');
    tip.appendChild(tipTitel);
    tip.appendChild(tipText);
    tip.appendChild(tipLink);
    document.body.appendChild(tip);

    var aktiv = null, fixiert = false, schliessTimer = null;

    function oeffnen(term, fix){
      clearTimeout(schliessTimer);
      var b = nachId[term.getAttribute('data-gl')];
      if(!b) return;
      if(aktiv && aktiv !== term) aktiv.setAttribute('aria-expanded', 'false');
      aktiv = term;
      fixiert = fix;
      tipTitel.textContent = b.begriff;
      tipText.textContent = b.kurz;
      tipLink.href = '#glossar-'+b.id;
      tipLink.onclick = function(e){ e.preventDefault(); schliessen(); zeigeEintrag(b.id); };
      term.setAttribute('aria-expanded', 'true');
      term.setAttribute('aria-describedby', 'glTip');
      tip.hidden = false;
      positionieren(term);
    }
    function schliessen(){
      clearTimeout(schliessTimer);
      if(aktiv){
        aktiv.setAttribute('aria-expanded', 'false');
        aktiv.removeAttribute('aria-describedby');
      }
      aktiv = null; fixiert = false;
      tip.hidden = true;
    }
    function spaeterSchliessen(){
      if(fixiert) return;
      clearTimeout(schliessTimer);
      schliessTimer = setTimeout(schliessen, 180);
    }
    function positionieren(term){
      var r = term.getBoundingClientRect();
      var rand = 16;
      tip.style.left = '0px'; tip.style.top = '0px';
      var w = tip.offsetWidth, h = tip.offsetHeight;
      var left = Math.min(Math.max(rand, r.left + r.width/2 - w/2), window.innerWidth - w - rand);
      var oben = r.top - h - 8;
      var top = oben >= rand ? oben : r.bottom + 8;
      tip.style.left = Math.max(rand, left)+'px';
      tip.style.top = top+'px';
    }

    document.addEventListener('mouseover', function(e){
      var term = e.target.closest && e.target.closest('.gl-term');
      if(term){ if(!fixiert || aktiv !== term) oeffnen(term, false); }
      else if(tip.contains(e.target)) clearTimeout(schliessTimer);
    });
    document.addEventListener('mouseout', function(e){
      var t = e.target.closest && (e.target.closest('.gl-term') || e.target.closest('.gl-tip'));
      if(t) spaeterSchliessen();
    });
    document.addEventListener('focusin', function(e){
      if(e.target.classList && e.target.classList.contains('gl-term')) oeffnen(e.target, false);
    });
    document.addEventListener('focusout', function(e){
      if(e.target.classList && e.target.classList.contains('gl-term') && !tip.contains(e.relatedTarget)) spaeterSchliessen();
    });
    document.addEventListener('click', function(e){
      var term = e.target.closest('.gl-term');
      if(term){
        if(aktiv === term && fixiert) schliessen();
        else oeffnen(term, true);
        return;
      }
      if(!tip.contains(e.target)) schliessen();
    });
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape' && aktiv){
        var t = aktiv;
        schliessen();
        t.focus();
        e.stopPropagation();
      }
    }, true);
    window.addEventListener('scroll', function(){ if(aktiv) schliessen(); }, true);
    window.addEventListener('resize', function(){ if(aktiv) schliessen(); });
  }
})();
