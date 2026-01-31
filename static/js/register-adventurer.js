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
  const slotHeadingElements = Array.from(document.querySelectorAll("[data-slot-heading]"));
  const slotNameInputs = Array.from(document.querySelectorAll("[data-slot-name-input]"));
  const activeSlotNumber = document.querySelector("[data-active-slot-number]");
  const activeSlotName = document.querySelector("[data-active-slot-name]");
  const slotControl = document.querySelector("[data-slot-control]");
  const slotOrder = adventurerTabs.map((tab) => tab.dataset.adventurerTab);
  let currentStep = 1;
  const responsavelNomeInput = document.getElementById("responsavel_nome");
  const responsavelSobrenomeInput = document.getElementById("responsavel_sobrenome");
  const responsavelTelefoneInput = document.getElementById("responsavel_telefone");
  const responsavelWhatsappInput = document.getElementById("responsavel_whatsapp");
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
    if (slotControl) {
      slotControl.classList.toggle("is-hidden", step < 3);
    }
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

  const autoTargetsBySource = new Map();
  document
    .querySelectorAll("[data-auto-from]")
    .forEach((target) => {
      const sourceName = target.dataset.autoFrom?.trim();
      if (!sourceName) {
        return;
      }
      const targets = autoTargetsBySource.get(sourceName) || [];
      targets.push(target);
      autoTargetsBySource.set(sourceName, targets);
    });

  const applyAutoValue = (target, value) => {
    const normalized = value?.trim() || "";
    if (!normalized) {
      return;
    }
    const current = target.value?.trim() || "";
    const lastAuto = target.dataset.autoValue || "";
    if (!current || current === lastAuto) {
      target.value = normalized;
      target.dataset.autoValue = normalized;
    }
  };

  const updateAutoTargets = (sourceName, value) => {
    const targets = autoTargetsBySource.get(sourceName);
    if (!targets) {
      return;
    }
    targets.forEach((target) => applyAutoValue(target, value));
  };

  const autoSourceSelector = "[name='responsavel_whatsapp'],[name='responsavel_telefone'],[name='responsavel_street'],[name='responsavel_house_number'],[name='responsavel_neighborhood'],[name='responsavel_postal_code'],[name='responsavel_city'],[name='responsavel_state']";
  const autoSourceFields = Array.from(document.querySelectorAll(autoSourceSelector));
  autoSourceFields.forEach((field) => {
    field.addEventListener("input", () => updateAutoTargets(field.name, field.value));
    updateAutoTargets(field.name, field.value);
  });

  const termResponsibleInputs = Array.from(
    document.querySelectorAll("[data-auto-responsible-fullname]")
  );
  const getResponsibleNames = () => {
    const first = responsavelNomeInput?.value?.trim() || "";
    const last = responsavelSobrenomeInput?.value?.trim() || "";
    return [first, last].filter(Boolean).join(" ");
  };
  const syncTermResponsible = () => {
    const fullName = getResponsibleNames();
    termResponsibleInputs.forEach((input) => applyAutoValue(input, fullName));
  };
  [responsavelNomeInput, responsavelSobrenomeInput].forEach((field) => {
    field?.addEventListener("input", syncTermResponsible);
  });
  syncTermResponsible();

  const getSlotName = (slot) => {
    const input = document.querySelector(`[data-slot-name-input="${slot}"]`);
    return input?.value.trim() || "";
  };

  const formatTabLabel = (slot, name) => {
    if (!name) {
      return `Aventureiro ${slot}`;
    }
    return `${slot} • ${name}`;
  };

  const headingTemplates = {
    adventure: (slot, name) => (name ? `${name}` : `Aventureiro ${slot}`),
    medical: (slot, name) => (name ? `Ficha médica • ${name}` : `Ficha médica ${slot}`),
    term: (slot, name) => (name ? `Termo de autorização • ${name}` : `Termo ${slot}`),
  };

  const refreshSlotHeadings = (slot) => {
    const name = getSlotName(slot);
    slotHeadingElements.forEach((element) => {
      if (element.dataset.slot !== slot) {
        return;
      }
      const template = headingTemplates[element.dataset.slotHeading];
      if (!template) {
        return;
      }
      element.textContent = template(slot, name);
    });
  };

  const refreshTabLabel = (slot) => {
    const name = getSlotName(slot);
    const tab = adventurerTabs.find((candidate) => candidate.dataset.adventurerTab === slot);
    if (tab) {
      tab.textContent = formatTabLabel(slot, name);
    }
  };

  const refreshActiveSlotLabel = (slot) => {
    const name = getSlotName(slot);
    if (activeSlotNumber) {
      activeSlotNumber.textContent = `Aventureiro ${slot}`;
    }
    if (activeSlotName) {
      activeSlotName.textContent = name ? ` • ${name}` : "";
    }
  };

  const refreshSlotMetadata = (slot) => {
    refreshTabLabel(slot);
    refreshSlotHeadings(slot);
    if (slot === currentAdventurerSlot) {
      refreshActiveSlotLabel(slot);
    }
  };

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
    refreshSlotMetadata(normalized);
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
  slotOrder.forEach((slot) => refreshSlotMetadata(slot));

  slotNameInputs.forEach((input) => {
    const slot = input.dataset.slotNameInput;
    if (!slot) {
      return;
    }
    input.addEventListener("input", () => refreshSlotMetadata(slot));
  });

  const getErrorMessageElement = (element) => {
    const group = element.closest(".field-group");
    if (group) {
      return group.querySelector(".error-message");
    }
    const checkboxField = element.closest(".checkbox-field");
    if (checkboxField) {
      const nextMessage = checkboxField.nextElementSibling;
      if (nextMessage?.classList.contains("error-message")) {
        return nextMessage;
      }
      const parentMessage = checkboxField.parentElement?.querySelector(".error-message");
      if (parentMessage?.classList.contains("error-message")) {
        return parentMessage;
      }
    }
    return null;
  };

  const setError = (element) => {
    element.classList.add("input-error");
    const group = element.closest(".field-group");
    const checkboxField = element.closest(".checkbox-field");
    group?.classList.add("input-error");
    checkboxField?.classList.add("input-error");
    const message = getErrorMessageElement(element);
    if (message && !message.textContent.trim()) {
      message.textContent = "Campo obrigatório";
    }
  };

  const clearError = (element) => {
    element.classList.remove("input-error");
    const group = element.closest(".field-group");
    const checkboxField = element.closest(".checkbox-field");
    group?.classList.remove("input-error");
    checkboxField?.classList.remove("input-error");
    const message = getErrorMessageElement(element);
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

  const findSlotForField = (field) => field?.closest("[data-slot-panel]")?.dataset.slot;

  form?.addEventListener("submit", (event) => {
    const invalidFields = Array.from(form.querySelectorAll(":invalid"));
    const requiredCheckboxes = Array.from(
      form.querySelectorAll("input[type='checkbox'][required]")
    ).filter((checkbox) => !checkbox.checked);
    const highlightedFields = [...invalidFields, ...requiredCheckboxes];
    if (highlightedFields.length) {
      event.preventDefault();
      highlightedFields.forEach(setError);
      const firstInvalid = highlightedFields[0];
      const slot = findSlotForField(firstInvalid);
      if (slot) {
        setActiveAdventurerSlot(slot);
      }
      firstInvalid?.focus();
      goToStep(Number(firstInvalid?.closest(".adventurer-step")?.dataset.step) || 1);
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
