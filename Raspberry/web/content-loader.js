(async function loadPageContent() {
  'use strict';

  const fragments = [
    ['heroContent', 'content/hero.html'],
    ['mainContent', 'content/lernpfade.html'],
    ['mainContent', 'content/thema-projekt.html'],
    ['mainContent', 'content/thema-crispdm.html'],
    ['mainContent', 'content/chat.html'],
    ['mainContent', 'content/thema-a.html'],
    ['mainContent', 'content/thema-b.html'],
    ['mainContent', 'content/thema-ml.html'],
    ['mainContent', 'content/thema-c.html'],
    ['mainContent', 'content/thema-d.html'],
    ['mainContent', 'content/thema-e.html'],
    ['mainContent', 'content/quiz.html'],
    ['mainContent', 'content/glossar.html']
  ];

  try {
    for (const [targetId, path] of fragments) {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`${path}: ${response.status}`);
      }
      document.getElementById(targetId).insertAdjacentHTML('beforeend', await response.text());
    }

    const script = document.createElement('script');
    script.src = 'index.js';
    document.body.appendChild(script);

    const glossar = document.createElement('script');
    glossar.src = 'glossar.js';
    document.body.appendChild(glossar);

    const lernpfade = document.createElement('script');
    lernpfade.src = 'lernpfade.js';
    document.body.appendChild(lernpfade);
  } catch (error) {
    document.body.insertAdjacentHTML(
      'beforeend', `<p class="content-error">Seiteninhalte konnten nicht geladen werden: ${error.message}</p>`
    );
  }
})();
