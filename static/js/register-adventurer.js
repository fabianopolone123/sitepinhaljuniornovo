document.addEventListener("DOMContentLoaded", () => {
  const steps = Array.from(document.querySelectorAll(".adventurer-step"));
  const stepButtons = Array.from(document.querySelectorAll(".step-btn"));
  const nextBtn = document.querySelector("[data-next]");
  const prevBtn = document.querySelector("[data-prev]");
  const submitBtn = document.querySelector("[data-submit]");
  const form = document.querySelector(".adventurer-form");
  const adventurerTabs = Array.from(document.querySelectorAll(".adventurer-tab"));
  const adventurerCountSelect = document.querySelector("[name='adventure_count']");
  const activeSlotInput = document.querySelector("[name='active_adventurer_slot']");
  const adventurerSlotLabel = document.querySelector("#adventurer-slot-label");
  const slotPanels = Array.from(document.querySelectorAll("[data-slot-panel]"));
  const slotOrder = adventurerTabs.map((tab) => tab.dataset.adventurerTab);
  let currentStep = 1;
  let currentAdventurerSlot = activeSlotInput?.value || "01";

  const getNormalizedSlotCount = () => {
    const rawValue = parseInt(adventurerCountSelect?.value || "1", 10);
    if (Number.isNaN(rawValue)) {
      return 1;
    }
    return Math.min(Math.max(1, rawValue), slotOrder.length || 1);
  };

  const updateSlotPanels = () => {
    const allowedSlots = slotOrder.slice(0, getNormalizedSlotCount());
    slotPanels.forEach((panel) => {
      const slot = panel.dataset.slot;
      const shouldShow = allowedSlots.includes(slot) && slot === currentAdventurerSlot;
      panel.classList.toggle("is-hidden", !shouldShow);
    });
  };

  const loadPhotoPreview = (slot) => {
    if (!slot) return;
    const input = document.querySelector(`[name='adventure_photo_${slot}']`);
    const previewWrapper = document.querySelector(`#adventurer-photo-preview-${slot}`);
    if (!input || !previewWrapper) return;
    const previewTemplate =
      previewWrapper.dataset.template || previewWrapper.innerHTML || "";
    if (!previewWrapper.dataset.template) {
      previewWrapper.dataset.template = previewTemplate;
    }
    const showImage = (src) => {
      previewWrapper.innerHTML = "";
      const img = document.createElement("img");
      img.src = src;
      previewWrapper.appendChild(img);
    };
    const file = input.files?.[0];
    if (!file) {
      previewWrapper.innerHTML = previewTemplate;
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      showImage(event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const renderStep = (step) => {
    steps.forEach((section) => {
      section.classList.toggle("is-active", Number(section.dataset.step) === step);
    });
    stepButtons.forEach((button) => {
      button.classList.toggle(
        "is-active",
        Number(button.dataset.stepTarget) === step
      );
    });
    if (prevBtn) {
      prevBtn.disabled = step === 1;
    }
    if (nextBtn) {
      nextBtn.classList.toggle("is-hidden", step === steps.length);
    }
    if (submitBtn) {
      submitBtn.classList.toggle("is-hidden", step !== steps.length);
    }
    updateSlotPanels();
  };

  const goToStep = (step) => {
    currentStep = Math.min(Math.max(1, step), steps.length);
    renderStep(currentStep);
  };

  if (nextBtn) {
    nextBtn.addEventListener("click", () => goToStep(currentStep + 1));
  }
  if (prevBtn) {
    prevBtn.addEventListener("click", () => goToStep(currentStep - 1));
  }
  stepButtons.forEach((button) => {
    const target = Number(button.dataset.stepTarget);
    button.addEventListener("click", () => goToStep(target));
  });

  const normalizeSlotValue = (value) => value.toString().padStart(2, "0");

  const updateTabVisibility = (count) => {
    const normalizedCount = Math.min(Math.max(1, count), slotOrder.length || 1);
    adventurerTabs.forEach((tab, index) => {
      const visible = index < normalizedCount;
      tab.classList.toggle("is-hidden", !visible);
    });
    const activeTab = adventurerTabs.find(
      (tab) => !tab.classList.contains("is-hidden") && tab.dataset.adventurerTab === currentAdventurerSlot
    );
    if (!activeTab) {
      const firstVisible = adventurerTabs.find((tab) => !tab.classList.contains("is-hidden"));
      if (firstVisible) {
        setActiveAdventurerSlot(firstVisible.dataset.adventurerTab, false);
      }
    }
  };

  const setActiveAdventurerSlot = (slot, syncInput = true) => {
    const normalized = normalizeSlotValue(slot || "01");
    currentAdventurerSlot = normalized;
    if (syncInput && activeSlotInput) {
      activeSlotInput.value = normalized;
    }
    adventurerTabs.forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.adventurerTab === normalized);
    });
    if (adventurerSlotLabel) {
      adventurerSlotLabel.textContent = `Aventureiro ${normalized}`;
    }
    updateSlotPanels();
    loadPhotoPreview(normalized);
  };

  adventurerTabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveAdventurerSlot(tab.dataset.adventurerTab));
  });

  adventurerCountSelect?.addEventListener("change", () => {
    const normalizedCount = getNormalizedSlotCount();
    updateTabVisibility(normalizedCount);
    const activeTab = adventurerTabs.find(
      (tab) => !tab.classList.contains("is-hidden") && tab.dataset.adventurerTab === currentAdventurerSlot
    );
    if (!activeTab) {
      const firstVisible = adventurerTabs.find((tab) => !tab.classList.contains("is-hidden"));
      if (firstVisible) {
        setActiveAdventurerSlot(firstVisible.dataset.adventurerTab);
      }
    }
    updateSlotPanels();
  });

  const initialCount = getNormalizedSlotCount();
  updateTabVisibility(initialCount);
  setActiveAdventurerSlot(currentAdventurerSlot, false);

  const setError = (element) => {
    element.classList.add("input-error");
    const group = element.closest(".field-group");
    const message = group?.querySelector(".error-message");
    if (message && !message.textContent.trim()) {
      message.textContent = "Campo obrigatório";
    }
  };

  const clearError = (element) => {
    element.classList.remove("input-error");
    const group = element.closest(".field-group");
    const message = group?.querySelector(".error-message");
    if (message && message.textContent === "Campo obrigatório") {
      message.textContent = "";
    }
  };

  form?.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("input", () => clearError(field));
    field.addEventListener("invalid", (event) => {
      event.preventDefault();
      setError(field);
      field.focus();
    });
    if (field.type === "file") {
      const slotKey = field.dataset.slotPhoto;
      if (slotKey) {
        field.addEventListener("change", () => loadPhotoPreview(slotKey));
      }
    }
  });

  const toggleDependentDetail = (select) => {
    if (!select?.dataset?.detailTarget) return;
    const detail = document.getElementById(select.dataset.detailTarget);
    if (!detail) return;
    detail.classList.toggle("is-active", select.value === "sim");
  };

  form?.querySelectorAll("[data-detail-target]").forEach((select) => {
    select.addEventListener("change", () => toggleDependentDetail(select));
    toggleDependentDetail(select);
  });

  form?.addEventListener("submit", (event) => {
    const invalidFields = Array.from(form.querySelectorAll(":invalid"));
    if (invalidFields.length) {
      event.preventDefault();
      invalidFields.forEach(setError);
      invalidFields[0]?.focus();
      goToStep(Number(invalidFields[0]?.closest(".adventurer-step")?.dataset.step) || 1);
    }
  });

  renderStep(currentStep);
  initSignatureModal({
    modalId: "responsavel-signature-modal",
    triggerSelector: "[data-signature-trigger='responsavel']",
    inputSelector: "#responsavel-signature-input",
    previewSelector: "#responsavel-signature-preview",
    placeholder: "Nenhum registro ainda",
  });
  initSignatureModal({
    modalId: "parent-signature-modal",
    triggerSelector: "[data-signature-trigger='parent']",
    inputSelector: "#parent-signature-input",
    previewSelector: "#parent-signature-preview",
    placeholder: "Nenhum registro ainda",
  });
  initSignatureModal({
    modalId: "medical-signature-modal",
    triggerSelector: "[data-signature-trigger='medical']",
    inputSelector: "#medical-signature-input",
    previewSelector: "#medical-signature-preview",
    placeholder: "Nenhum registro ainda",
  });
  initSignatureModal({
    modalId: "adventure-data-signature-modal",
    triggerSelector: "[data-signature-trigger='adventure-data']",
    inputSelector: "#adventure-data-signature-input",
    previewSelector: "#adventure-data-signature-preview",
    placeholder: "Nenhum registro ainda",
  });
  initSignatureModal({
    modalId: "adventurer-signature-modal",
    triggerSelector: "[data-signature-trigger='adventurer']",
    inputSelector: "#adventurer-signature-input",
    previewSelector: "#adventurer-signature-preview",
    placeholder: "Nenhum registro ainda",
  });
});
