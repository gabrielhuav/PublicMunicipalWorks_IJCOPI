/* Review-only navigation. Does not modify scientific data or source attribution. */
(() => {
  'use strict';

  function connectReviewRepository() {
    if (window.location.hostname !== 'anonymous.4open.science') return;
    const match = /^\/w\/([^/]+)\//.exec(window.location.pathname);
    if (!match || !/^[A-Za-z0-9_-]+$/.test(match[1])) return;
    const repository = 'https://anonymous.4open.science/r/' + encodeURIComponent(match[1]) + '/';
    document.querySelectorAll('a.repo, a[href="materiales.html"], a[href="./materiales.html"]').forEach(link => {
      link.href = repository;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectReviewRepository, { once: true });
  } else {
    connectReviewRepository();
  }
})();
