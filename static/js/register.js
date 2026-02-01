(() => {
  const dateFields = {
    day: { min: 1, max: 31 },
    month: { min: 1, max: 12 },
    year: { min: new Date().getFullYear() - 18, max: new Date().getFullYear() },
  };

  function buildOptions(container, start, end, pad = false) {
    for (let value = start; value <= end; value += 1) {
      const option = document.createElement('option');
      const label = pad && value < 10 ? `0${value}` : String(value);
      option.value = String(value);
      option.textContent = label;
      container.appendChild(option);
    }
  }

  function hydrateDateSelectors() {
    const daySelects = document.querySelectorAll('[data-date-field="day"]');
    const monthSelects = document.querySelectorAll('[data-date-field="month"]');
    const yearSelects = document.querySelectorAll('[data-date-field="year"]');
    daySelects.forEach((select) => {
      if (select.options.length === 0) {
        buildOptions(select, dateFields.day.min, dateFields.day.max, true);
      }
    });
    monthSelects.forEach((select) => {
      if (select.options.length === 0) {
        buildOptions(select, dateFields.month.min, dateFields.month.max, true);
      }
    });
    yearSelects.forEach((select) => {
      if (select.options.length === 0) {
        buildOptions(select, dateFields.year.min, dateFields.year.max);
      }
    });

    const today = new Date();
    daySelects.forEach((select) => {
      select.value = String(today.getDate());
    });
    monthSelects.forEach((select) => {
      select.value = String(today.getMonth() + 1);
    });
    yearSelects.forEach((select) => {
      select.value = String(today.getFullYear());
    });

    const todayInputs = document.querySelectorAll('[data-today-date]');
    todayInputs.forEach((input) => {
      input.value = today.toLocaleDateString('pt-BR');
    });
  }

  function initPhotoPreview() {
    const input =
      document.querySelector('[data-photo-input]') || document.querySelector('[name="aventureiro_foto"]');
    const preview = document.querySelector('[data-photo-preview]');
    const helper = document.querySelector('[data-photo-helper]');
    if (!input || !preview) {
      return;
    }
    const placeholderMarkup = preview.innerHTML;
    const STORAGE_KEY = 'register_photo_preview';
    const STORAGE_TTL = 5 * 60 * 1000;

    function readStoredPhoto() {
      try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        if (!raw) {
          return null;
        }
        const stored = JSON.parse(raw);
        if (!stored?.data) {
          sessionStorage.removeItem(STORAGE_KEY);
          return null;
        }
        if (Date.now() - stored.ts > STORAGE_TTL) {
          sessionStorage.removeItem(STORAGE_KEY);
          return null;
        }
        return stored.data;
      } catch {
        return null;
      }
    }

    function storePhoto(dataUrl) {
      try {
        sessionStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ data: dataUrl, ts: Date.now() }),
        );
      } catch {
        // ignore sessionStorage errors
      }
    }

    function clearStoredPhoto() {
      try {
        sessionStorage.removeItem(STORAGE_KEY);
      } catch {
        // ignore
      }
    }

    function updateHelper(show) {
      if (!helper) {
        return;
      }
      helper.hidden = !show;
    }

    function resetPreview() {
      preview.innerHTML = placeholderMarkup;
      preview.classList.remove('has-image');
      updateHelper(false);
      clearStoredPhoto();
    }

    function renderPreview(dataUrl) {
      preview.innerHTML = '';
      const img = document.createElement('img');
      img.alt = 'Pré-visualização 3x4';
      img.src = dataUrl;
      preview.classList.add('has-image');
      preview.appendChild(img);
    }

    function showPreviewFromStorage() {
      const stored = readStoredPhoto();
      if (!stored) {
        return false;
      }
      renderPreview(stored);
      if (helper && !(input.files && input.files.length)) {
        updateHelper(true);
      }
      return true;
    }

    if (!showPreviewFromStorage()) {
      resetPreview();
    }

    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file) {
        resetPreview();
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        renderPreview(reader.result);
        storePhoto(reader.result);
        updateHelper(false);
      };
      reader.readAsDataURL(file);
    });
  }

  function initSignatureModal() {
    const modal = document.getElementById('signature-modal');
    const signatureInput =
      document.querySelector('[data-signature-input]') || document.querySelector('[name="assinatura_data"]');
    if (!modal || !signatureInput) {
      return;
    }
    const canvas = modal.querySelector('canvas');
    const openButton = document.querySelector('[data-action="open-signature"]');
    const closeTriggers = modal.querySelectorAll('[data-action="close-signature"]');
    const clearButton = modal.querySelector('[data-action="clear-signature"]');
    const saveButton = modal.querySelector('[data-action="save-signature"]');
    if (!canvas || !openButton || !saveButton || !clearButton) {
      return;
    }
    const previewText = document.querySelector('[data-signature-preview-text]');
    const previewImage = document.querySelector('[data-signature-preview-img]');
    const ctx = canvas.getContext('2d');
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#0b1f64';
    let drawing = false;
    let activePointerId = null;

    function getCoords(event) {
      const rect = canvas.getBoundingClientRect();
      const clientX =
        event.touches?.[0]?.clientX ?? event.changedTouches?.[0]?.clientX ?? event.clientX;
      const clientY =
        event.touches?.[0]?.clientY ?? event.changedTouches?.[0]?.clientY ?? event.clientY;
      const x = (clientX ?? 0) - rect.left;
      const y = (clientY ?? 0) - rect.top;
      return { x, y };
    }

    function start(event) {
      event.preventDefault();
      drawing = true;
      activePointerId = event.pointerId ?? null;
      const { x, y } = getCoords(event);
      ctx.beginPath();
      ctx.moveTo(x, y);
      if (activePointerId && canvas.setPointerCapture) {
        canvas.setPointerCapture(activePointerId);
      }
    }

    function draw(event) {
      if (!drawing) {
        return;
      }
      event.preventDefault();
      const { x, y } = getCoords(event);
      ctx.lineTo(x, y);
      ctx.stroke();
    }

    function stop() {
      if (!drawing) {
        return;
      }
      drawing = false;
      if (activePointerId && canvas.releasePointerCapture) {
        canvas.releasePointerCapture(activePointerId);
      }
      activePointerId = null;
    }

    function setPreviewState(message, imageUrl) {
      if (previewText) {
        previewText.textContent = message;
      }
      if (previewImage) {
        if (imageUrl) {
          previewImage.src = imageUrl;
          previewImage.hidden = false;
        } else {
          previewImage.removeAttribute('src');
          previewImage.hidden = true;
        }
      }
    }

    function clearCanvas() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      signatureInput.value = '';
      setPreviewState('Sem assinatura ainda.');
    }

    function openModal() {
      modal.classList.add('is-visible');
      modal.setAttribute('aria-hidden', 'false');
    }

    function closeModal() {
      modal.classList.remove('is-visible');
      modal.setAttribute('aria-hidden', 'true');
    }

    function saveSignature() {
      const dataUrl = canvas.toDataURL('image/png');
      signatureInput.value = dataUrl;
      closeModal();
      setPreviewState('Assinatura registrada', dataUrl);
    }

    canvas.addEventListener('pointerdown', start);
    canvas.addEventListener('pointermove', draw);
    canvas.addEventListener('pointerup', stop);
    canvas.addEventListener('pointerleave', stop);
    canvas.addEventListener('pointercancel', stop);
    canvas.addEventListener('contextmenu', (event) => event.preventDefault());

    clearButton.addEventListener('click', clearCanvas);
    openButton.addEventListener('click', openModal);
    saveButton.addEventListener('click', saveSignature);
    closeTriggers.forEach((trigger) => trigger.addEventListener('click', closeModal));
    modal.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeModal();
      }
    });
    if (signatureInput.value) {
      setPreviewState('Assinatura registrada', signatureInput.value);
    }
  }

  function initClientValidation() {
    const form = document.getElementById('registration-form');
    const summary = document.querySelector('[data-error-summary]');
    if (!form) {
      return;
    }
    const requiredFields = Array.from(form.querySelectorAll('[required]'));

    function getFieldLabel(field) {
      if (field.dataset.errorLabel) {
        return field.dataset.errorLabel;
      }
      const label = field.closest('label');
      if (!label) {
        return 'Este campo';
      }
      return label.textContent.replace(/\s+/g, ' ').trim() || 'Este campo';
    }

    function setFieldError(field, message) {
      field.classList.add('is-invalid');
      field.setAttribute('aria-invalid', 'true');
      const container = field.closest('label') || field.parentElement;
      if (!container) {
        return;
      }
      let errorEl = container.querySelector('.field-error');
      if (!errorEl) {
        errorEl = document.createElement('span');
        errorEl.className = 'field-error';
        container.appendChild(errorEl);
      }
      errorEl.textContent = message;
    }

    function clearFieldError(field) {
      field.classList.remove('is-invalid');
      field.removeAttribute('aria-invalid');
      const container = field.closest('label') || field.parentElement;
      if (!container) {
        return;
      }
      const errorEl = container.querySelector('.field-error');
      if (errorEl) {
        errorEl.remove();
      }
    }

    function markFieldValidity(field) {
      const isEmpty = (() => {
        if (field.type === 'file') {
          return !(field.files && field.files.length > 0);
        }
        if (field.type === 'checkbox' || field.type === 'radio') {
          return !field.checked;
        }
        return !field.value || !field.value.toString().trim();
      })();
      if (isEmpty) {
        const label = getFieldLabel(field);
        setFieldError(field, `${label || 'Este campo'} é obrigatório.`);
        return false;
      }
      clearFieldError(field);
      return true;
    }

    function handleSubmit(event) {
      const invalid = requiredFields.filter((field) => !markFieldValidity(field));
      if (invalid.length) {
        event.preventDefault();
        if (summary) {
          summary.hidden = false;
          summary.textContent = 'Complete os campos em destaque antes de enviar.';
        }
        invalid[0].focus();
      } else if (summary) {
        summary.hidden = true;
        summary.textContent = '';
      }
    }

    requiredFields.forEach((field) => {
      const eventName = field.type === 'file' ? 'change' : 'input';
      field.addEventListener(eventName, () => {
        if (markFieldValidity(field) && summary) {
          const hasInvalid = requiredFields.some(
            (element) => element.classList.contains('is-invalid'),
          );
          if (!hasInvalid) {
            summary.hidden = true;
            summary.textContent = '';
          }
        }
      });
    });

    form.addEventListener('submit', handleSubmit);
  }

  function boot() {
    hydrateDateSelectors();
    initPhotoPreview();
    initSignatureModal();
    initClientValidation();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
