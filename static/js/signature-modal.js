(function () {
  const defaultPlaceholder = "Nenhuma assinatura registrada.";

  const getCanvasSize = () => {
    const margin = 40;
    const maxWidth = 560;
    const width = Math.min(maxWidth, window.innerWidth - margin);
    const height = window.innerWidth < 520 ? 220 : 260;
    return { width, height };
  };

  const registerPointerHandlers = (canvas, handlers) => {
    ["pointerdown", "pointermove", "pointerup", "pointercancel", "pointerleave"].forEach((eventName) => {
      canvas.addEventListener(eventName, handlers[eventName]);
    });
  };

  window.initSignatureModal = function (options = {}) {
    const {
      modalId,
      triggerSelector,
      inputSelector,
      previewSelector,
      placeholder = defaultPlaceholder,
    } = options;
    const trigger = document.querySelector(triggerSelector);
    const modal = document.getElementById(modalId);
    const input = document.querySelector(inputSelector);
    const preview = document.querySelector(previewSelector);
    if (!modal || !trigger || !input) {
      return null;
    }

    const canvas = modal.querySelector("canvas");
    if (!canvas) {
      return null;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return null;
    }

    const saveBtn = modal.querySelector("[data-save-signature]");
    const clearBtn = modal.querySelector("[data-clear-signature]");
    const closeBtns = modal.querySelectorAll("[data-close-signature],[data-cancel-signature]");

    const clearCanvas = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    };

    const resizeCanvas = () => {
      const { width, height } = getCanvasSize();
      canvas.width = width;
      canvas.height = height;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#0F3A74";
      ctx.fillStyle = "#fff";
      ctx.clearRect(0, 0, width, height);
      ctx.fillRect(0, 0, width, height);
    };

    const updatePreview = (value) => {
      if (!preview) return;
      if (value) {
        preview.innerHTML = `<img src="${value}" alt="Assinatura registrada" />`;
      } else {
        preview.innerHTML = `<span>${placeholder}</span>`;
      }
    };

    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;

    const getPointerPosition = (event) => {
      const rect = canvas.getBoundingClientRect();
      return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
    };

    const startDrawing = (event) => {
      event.preventDefault();
      isDrawing = true;
      const coords = getPointerPosition(event);
      lastX = coords.x;
      lastY = coords.y;
      canvas.setPointerCapture(event.pointerId);
    };

    const draw = (event) => {
      if (!isDrawing) {
        return;
      }
      event.preventDefault();
      const coords = getPointerPosition(event);
      ctx.beginPath();
      ctx.moveTo(lastX, lastY);
      ctx.lineTo(coords.x, coords.y);
      ctx.stroke();
      lastX = coords.x;
      lastY = coords.y;
    };

    const stopDrawing = (event) => {
      if (!isDrawing) {
        return;
      }
      isDrawing = false;
      try {
        canvas.releasePointerCapture(event.pointerId);
      } catch (err) {
        // best effort, ignore if not supported
      }
    };

    const openModal = () => {
      resizeCanvas();
      clearCanvas();
      canvas.focus?.();
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
    };

    const closeModal = () => {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
    };

    const handleSave = () => {
      const dataUrl = canvas.toDataURL("image/png");
      input.value = dataUrl;
      updatePreview(dataUrl);
      closeModal();
    };

    const handlers = {
      pointerdown: startDrawing,
      pointermove: draw,
      pointerup: stopDrawing,
      pointercancel: stopDrawing,
      pointerleave: stopDrawing,
    };

    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      openModal();
    });

    saveBtn?.addEventListener("click", handleSave);
    clearBtn?.addEventListener("click", () => clearCanvas());
    closeBtns.forEach((btn) => btn.addEventListener("click", closeModal));
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        closeModal();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal.classList.contains("is-open")) {
        closeModal();
      }
    });

    registerPointerHandlers(canvas, handlers);

    window.addEventListener("resize", () => {
      if (modal.classList.contains("is-open")) {
        resizeCanvas();
      }
    });

    updatePreview(input.value || "");

  };
})();
