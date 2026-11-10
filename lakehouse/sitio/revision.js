/* Review-host compatibility for an opaque CSP sandbox. Scientific JSON stays unchanged. */
(() => {
  'use strict';

  const reviewHost = window.location.hostname === 'anonymous.4open.science';
  const opaqueOrigin = window.origin === 'null';
  const currentScript = document.currentScript;
  const siteBase = new URL('.', currentScript && currentScript.src ? currentScript.src : window.location.href);

  if ((reviewHost || opaqueOrigin) && typeof window.fetch === 'function') {
    const originalFetch = window.fetch.bind(window);
    const cached = new Map();
    const pendingPaths = new Map();
    const maxAttempts = 2;
    const attemptTimeout = 30000;

    function relativePath(url) {
      if (url.origin !== siteBase.origin || !url.pathname.startsWith(siteBase.pathname)) return null;
      if (!/\.(?:json|geojson)$/i.test(url.pathname)) return null;
      try { return decodeURIComponent(url.pathname.slice(siteBase.pathname.length)); }
      catch (_) { return null; }
    }
    function abortReason(signal) {
      return signal && signal.reason !== undefined
        ? signal.reason : new DOMException('The operation was aborted.', 'AbortError');
    }
    function waitForCaller(shared, signal) {
      if (!signal) return shared;
      if (signal.aborted) return Promise.reject(abortReason(signal));
      return new Promise((resolve, reject) => {
        let complete = false;
        const clean = () => signal.removeEventListener('abort', aborted);
        const aborted = () => {
          if (complete) return;
          complete = true;
          clean();
          reject(abortReason(signal));
        };
        signal.addEventListener('abort', aborted, { once: true });
        shared.then(text => {
          if (complete) return;
          complete = true;
          clean();
          resolve(text);
        }, error => {
          if (complete) return;
          complete = true;
          clean();
          reject(error);
        });
      });
    }
    function loadText(url, relative) {
      const key = url.href;
      if (cached.has(key)) return cached.get(key);
      let resolveText, rejectText;
      const shared = new Promise((resolve, reject) => { resolveText = resolve; rejectText = reject; });
      cached.set(key, shared);
      let attempt = 0;
      let script = null;
      let timer = null;
      let settled = false;
      const pathWaiters = pendingPaths.get(relative) || new Set();
      pendingPaths.set(relative, pathWaiters);
      function removeAttempt() {
        if (timer !== null) window.clearTimeout(timer);
        timer = null;
        if (script) {
          script.onload = null;
          script.onerror = null;
          script.remove();
        }
        script = null;
      }
      function removeWaiter() {
        pathWaiters.delete(entry);
        if (!pathWaiters.size) pendingPaths.delete(relative);
      }
      const entry = {
        resolve(text) {
          if (settled) return;
          settled = true;
          removeAttempt();
          removeWaiter();
          resolveText(text);
        },
      };
      pathWaiters.add(entry);
      function failed(message) {
        if (settled) return;
        removeAttempt();
        if (attempt < maxAttempts) {
          timer = window.setTimeout(startAttempt, 250);
          return;
        }
        settled = true;
        removeWaiter();
        if (cached.get(key) === shared) cached.delete(key);
        rejectText(new Error(message + ': ' + relative));
      }
      function startAttempt() {
        if (settled) return;
        attempt += 1;
        const companion = new URL(url.href);
        companion.pathname += '.jsonp.js';
        script = document.createElement('script');
        script.async = true;
        // Classic scripts intentionally omit crossorigin for the opaque sandbox.
        script.src = companion.href;
        script.referrerPolicy = 'no-referrer';
        script.onerror = () => failed('Could not load review data');
        script.onload = () => { if (!settled) failed('Review data callback was missing'); };
        timer = window.setTimeout(() => failed('Review data request timed out'), attemptTimeout);
        (document.head || document.documentElement).appendChild(script);
      }
      startAttempt();
      return shared;
    }
    window.__reviewJsonpLoad__ = function (relative, text) {
      if (typeof relative !== 'string' || typeof text !== 'string') return;
      if (relative.startsWith('/') || relative.split('/').includes('..')) return;
      const waiters = pendingPaths.get(relative);
      if (waiters) Array.from(waiters).forEach(entry => entry.resolve(text));
    };
    window.fetch = function (input, options) {
      const method = options && options.method || input && input.method || 'GET';
      const raw = typeof input === 'string' || input instanceof URL ? input : input && input.url;
      let url;
      try { url = new URL(raw, document.baseURI || window.location.href); }
      catch (_) { return originalFetch(input, options); }
      const relative = String(method).toUpperCase() === 'GET' ? relativePath(url) : null;
      if (relative === null) return originalFetch(input, options);
      const signal = options && options.signal !== undefined ? options.signal : input && input.signal;
      if (signal && signal.aborted) return Promise.reject(abortReason(signal));
      url.hash = '';
      return waitForCaller(loadText(url, relative), signal).then(text => new Response(text, {
        status: 200, headers: { 'Content-Type': 'application/json; charset=utf-8' },
      }));
    };
  }

  function connectReviewRepository() {
    if (!reviewHost) return;
    const match = /^\/w\/([^/]+)\//.exec(window.location.pathname);
    if (!match || !/^[A-Za-z0-9_-]+$/.test(match[1])) return;
    const repository = 'https://anonymous.4open.science/r/' + encodeURIComponent(match[1]) + '/';
    document.querySelectorAll('a[data-t="nav.repo"], a.repo, a[href="materiales.html"], a[href="./materiales.html"]').forEach(link => {
      link.href = repository;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectReviewRepository, { once: true });
  } else {
    connectReviewRepository();
  }
})();
