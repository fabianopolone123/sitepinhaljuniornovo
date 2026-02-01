(() => {
  function applyFilter(panel, lines) {
    const filterInput = panel.querySelector('[data-log-filter]');
    const content = panel.querySelector('[data-log-content]');
    const count = panel.querySelector('[data-log-count]');
    if (!content || !count) {
      return;
    }
    const term = (filterInput ? filterInput.value.trim().toLowerCase() : '');
    const filtered = term
      ? lines.filter((line) => line.toLowerCase().includes(term))
      : lines;
    content.textContent = filtered.length ? filtered.join('\n') : 'Nenhuma linha corresponde ao filtro.';
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

    if (filterInput) {
      filterInput.addEventListener('input', () => applyFilter(panel, lines));
    }
    if (clearButton) {
      clearButton.addEventListener('click', () => {
        if (filterInput) {
          filterInput.value = '';
        }
        applyFilter(panel, lines);
        if (filterInput) {
          filterInput.focus();
        }
      });
    }
  }

  function boot() {
    document.querySelectorAll('[data-log-panel]').forEach(initPanel);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
