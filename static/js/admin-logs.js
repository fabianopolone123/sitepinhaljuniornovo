(() => {
  const panelState = new Map();
  const panels = Array.from(document.querySelectorAll('[data-log-panel]'));

  function formatLineCount(value) {
    return `${value} ${value === 1 ? 'linha' : 'linhas'}`;
  }

  function applyFilter(panel) {
    const state = panelState.get(panel);
    if (!state) {
      return;
    }
    const { lines, count, filterInput, emptyMessage } = state;
    const term = filterInput ? filterInput.value.trim().toLowerCase() : '';
    let visible = 0;
    lines.forEach((line) => {
      const matches = !term || line.textContent.toLowerCase().includes(term);
      line.hidden = !matches;
      if (matches) {
        visible += 1;
      }
    });
    if (count) {
      count.textContent = formatLineCount(visible);
    }
    if (emptyMessage) {
      emptyMessage.hidden = visible > 0;
    }
  }

  function initPanel(panel) {
    const filterInput = panel.querySelector('[data-log-filter]');
    const clearButton = panel.querySelector('[data-log-clear]');
    const count = panel.querySelector('[data-log-count]');
    const emptyMessage = panel.querySelector('[data-log-empty]');
    const lines = Array.from(panel.querySelectorAll('[data-log-line]'));
    panelState.set(panel, { lines, count, filterInput, emptyMessage });

    if (filterInput) {
      filterInput.addEventListener('input', () => applyFilter(panel));
    }
    if (clearButton) {
      clearButton.addEventListener('click', () => {
        if (filterInput) {
          filterInput.value = '';
        }
        applyFilter(panel);
        if (filterInput) {
          filterInput.focus();
        }
      });
    }

    applyFilter(panel);
  }

  function setActivePanel(key) {
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.logKey !== key;
    });
  }

  function boot() {
    panels.forEach(initPanel);
    const select = document.getElementById('log-file-select');
    if (!select) {
      return;
    }
    select.addEventListener('change', (event) => {
      setActivePanel(event.target.value);
    });
    setActivePanel(select.value);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
