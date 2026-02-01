(() => {
  const panelState = new Map();
  const panels = Array.from(document.querySelectorAll('[data-log-panel]'));

  function applyFilter(panel) {
    const state = panelState.get(panel);
    if (!state) {
      return;
    }
    const { content, count, filterInput, lines } = state;
    const term = (filterInput ? filterInput.value.trim().toLowerCase() : '');
    const filtered = term
      ? lines.filter((line) => line.toLowerCase().includes(term))
      : lines;
    content.textContent = filtered.length
      ? filtered.join('\n')
      : 'Nenhuma linha corresponde ao filtro.';
    count.textContent = ${filtered.length} linha;
  }

  function initPanel(panel) {
    const content = panel.querySelector('[data-log-content]');
    if (!content) {
      return;
    }
    const lines = content.textContent.split(/\r?\n/);
    const filterInput = panel.querySelector('[data-log-filter]');
    const clearButton = panel.querySelector('[data-log-clear]');
    const count = panel.querySelector('[data-log-count]');
    panelState.set(panel, { content, count, filterInput, lines });

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