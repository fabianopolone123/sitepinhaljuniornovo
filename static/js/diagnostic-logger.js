(() => {
  const csrftokenName = "csrftoken";

  const getCookie = (name) => {
    const cookieString = document.cookie || "";
    const cookies = cookieString.split(";");
    for (const raw of cookies) {
      const cookie = raw.trim();
      if (!cookie) {
        continue;
      }
      const [key, ...rest] = cookie.split("=");
      if (key === name) {
        return decodeURIComponent(rest.join("="));
      }
    }
    return "";
  };

  const formatValue = (value) => {
    if (value instanceof Error) {
      return value.stack || value.message;
    }
    if (typeof value === "string") {
      return value;
    }
    try {
      const serialized = JSON.stringify(value);
      if (serialized === undefined) {
        return String(value);
      }
      return serialized;
    } catch (error) {
      return String(value);
    }
  };

  const sendEvent = (eventName, detail, level, options = {}) => {
    const url = window.EVENT_LOG_URL;
    if (!eventName || !url) {
      return;
    }
    const payload = {
      event: eventName,
      detail: detail || {},
      level: level || "info",
    };
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie(csrftokenName),
      },
      body: JSON.stringify(payload),
      keepalive: Boolean(options.keepalive),
    }).catch(() => {});
  };

  const consoleLevels = {
    log: "info",
    info: "info",
    warn: "warning",
    error: "error",
    debug: "debug",
  };

  const patchConsoleMethod = (method) => {
    const original = console[method];
    if (typeof original !== "function") {
      return;
    }
    console[method] = (...args) => {
      try {
        sendEvent(`console.${method}`, { args: args.map(formatValue) }, consoleLevels[method] || "info");
      } catch (error) {
        original.call(console, error);
      }
      original.apply(console, args);
    };
  };

  ["debug", "log", "info", "warn", "error"].forEach(patchConsoleMethod);

  const describeErrorEvent = (event) => ({
    message: event?.message,
    filename: event?.filename,
    lineno: event?.lineno,
    colno: event?.colno,
    stack: event?.error ? formatValue(event.error) : null,
  });

  const describeRejection = (event) => ({
    reason: formatValue(event?.reason),
  });

  window.addEventListener("error", (event) => {
    sendEvent("window.error", describeErrorEvent(event), "error", { keepalive: true });
  });

  window.addEventListener("unhandledrejection", (event) => {
    sendEvent("window.unhandledrejection", describeRejection(event), "error", { keepalive: true });
  });

  window.logProgramEvent = (eventName, detail = {}, level = "info") => {
    sendEvent(eventName, detail, level);
  };
})();
