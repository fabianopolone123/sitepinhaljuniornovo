(() => {
  if (window.__CLIENT_LOGGER__INSTALLED) {
    return;
  }
  window.__CLIENT_LOGGER__INSTALLED = true;

  const options = window.__CLIENT_LOGGER_OPTIONS || {};
  const endpoint = options.endpoint;
  if (!endpoint) {
    return;
  }

  const meta = document.querySelector('meta[name="client-log-request-id"]');
  const requestId = options.requestId || (meta && meta.getAttribute('content'));
  const sessionStorageKey = 'client-logger-session-id';
  let sessionId;
  try {
    sessionId = window.localStorage.getItem(sessionStorageKey);
    if (!sessionId) {
      sessionId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      window.localStorage.setItem(sessionStorageKey, sessionId);
    }
  } catch (error) {
    sessionId = `fallback-${Date.now()}`;
  }

  const queue = [];
  const BATCH_SIZE = 25;
  const FLUSH_INTERVAL_MS = 2200;

  const logger = {
    capture(type, detail) {
      queue.push({
        type,
        detail,
        timestamp: new Date().toISOString(),
      });
      if (queue.length >= BATCH_SIZE) {
        flush();
      }
    },
  };

  function normalizePayload(value) {
    if (typeof value === 'string') {
      const trimmed = value.replace(/\s+/g, ' ').trim();
      return trimmed.length > 1024 ? `${trimmed.slice(0, 1020)}…` : trimmed;
    }
    if (typeof value === 'number' || typeof value === 'boolean') {
      return value;
    }
    try {
      return JSON.stringify(value);
    } catch (_error) {
      return String(value);
    }
  }

  function flush() {
    if (!queue.length) {
      return;
    }

    const events = queue.splice(0, BATCH_SIZE);
    const payload = JSON.stringify({
      request_id: requestId,
      session_id: sessionId,
      events,
    });

    if (navigator.sendBeacon) {
      navigator.sendBeacon(endpoint, new Blob([payload], { type: 'application/json' }));
      return;
    }

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true,
      credentials: 'same-origin',
    }).catch(() => {});
  }

  const flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);
  window.addEventListener('beforeunload', () => {
    flush();
    clearInterval(flushTimer);
  });

  const originalConsole = {};
  ['log', 'info', 'warn', 'error'].forEach((method) => {
    if (typeof console[method] !== 'function') {
      return;
    }
    originalConsole[method] = console[method].bind(console);
    console[method] = (...args) => {
      logger.capture(`console.${method}`, args.map(normalizePayload));
      originalConsole[method](...args);
    };
  });

  window.addEventListener('error', (event) => {
    logger.capture('error', {
      message: normalizePayload(event.message),
      filename: normalizePayload(event.filename),
      lineno: event.lineno,
      colno: event.colno,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    logger.capture('unhandledrejection', {
      reason: normalizePayload(event.reason),
    });
  });

  if (window.fetch) {
    const originalFetch = window.fetch;
    window.fetch = (...args) => {
      const start = performance.now();
      return originalFetch(...args)
        .then((response) => {
          logger.capture('fetch', {
            url: args[0],
            duration: Math.round(performance.now() - start),
            status: response.status,
          });
          return response;
        })
        .catch((error) => {
          logger.capture('fetch.error', {
            url: args[0],
            message: normalizePayload(error && error.message),
          });
          throw error;
        });
    };
  }

  flush();
})();
