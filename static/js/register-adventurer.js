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

  const exportFormButton = document.querySelector("[data-export-form]");
  const importFormButton = document.querySelector("[data-open-import]");
  const importFormInput = document.querySelector("[data-import-file]");
  const slotPanels = Array.from(document.querySelectorAll("[data-slot-panel]"));
  const slotHeadingElements = Array.from(document.querySelectorAll("[data-slot-heading]"));
  const slotNameInputs = Array.from(document.querySelectorAll("[data-slot-name-input]"));
  const activeSlotNumber = document.querySelector("[data-active-slot-number]");
  const activeSlotName = document.querySelector("[data-active-slot-name]");
  const slotControl = document.querySelector("[data-slot-control]");
  const slotOrder = adventurerTabs.map((tab) => tab.dataset.adventurerTab);
  const csrfTokenInput = form?.querySelector("[name='csrfmiddlewaretoken']");
  const errorModal = document.getElementById("form-error-modal");
  const errorList = errorModal?.querySelector("[data-error-list]");
  const closeErrorModalBtn = errorModal?.querySelector("[data-error-modal-close]");
  let currentStep = 1;
  const responsavelNomeInput = document.getElementById("responsavel_nome");
  const responsavelSobrenomeInput = document.getElementById("responsavel_sobrenome");
  const responsavelTelefoneInput = document.getElementById("responsavel_telefone");
  const responsavelWhatsappInput = document.getElementById("responsavel_whatsapp");
  const defaultSlot = slotOrder[0] || "01";
  let currentAdventurerSlot = activeSlotInput?.value || defaultSlot;

  const getNormalizedSlotCount = () => {
    const rawValue = parseInt(adventurerCountSelect?.value || "1", 10);
    if (Number.isNaN(rawValue)) {
      return 1;
    }
    return Math.min(Math.max(1, rawValue), slotOrder.length || 1);
  };

  const getAllowedSlots = () => slotOrder.slice(0, getNormalizedSlotCount());

  const cssEscape =
    window.CSS?.escape ??
    ((value) => value.replace(/([\\\"'!#%&()*+,./:;<=>?@[\\]^`{|}~-])/g, "\\$1"));

  const signatureGuidance = [
    {
      pattern: /^parent_signature$/,
      label: "Assinatura dos pais",
      trigger: "[data-signature-trigger='parent']",
      step: 2,
      needsSlot: false,
    },
    {
      pattern: /^adventure_data_signature_/,
      label: "Assinatura dos dados do aventureiro",
      trigger: "[data-signature-trigger='adventure-data']",
      step: 3,
      needsSlot: true,
    },
    {
      pattern: /^medical_signature_/,
      label: "Assinatura da ficha médica",
      trigger: "[data-signature-trigger='medical']",
      step: 4,
      needsSlot: true,
    },
    {
      pattern: /^term_signature_/,
      label: "Assinatura do termo",
      trigger: "[data-signature-trigger='adventurer']",
      step: 5,
      needsSlot: true,
    },
  ];

  const getCookie = (name) => {
    const cookieString = document.cookie || "";
    const cookies = cookieString.split(";");
    for (let raw of cookies) {
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

  const ignoredExportFields = new Set(["csrfmiddlewaretoken"]);
  const signatureFieldPattern = /_signature_/;

  const collectFormSnapshot = () => {
    const snapshot = {};
    form
      ?.querySelectorAll("input[name], select[name], textarea[name]")
      .forEach((field) => {
        if (!field.name) return;
        if (field.type === "file") return;
        if (ignoredExportFields.has(field.name)) return;
        if (signatureFieldPattern.test(field.name)) return;
        if (field.type === "radio" && !field.checked) {
          return;
        }
        const rawValue =
          field.type === "checkbox" ? field.checked : field.value ?? "";
        const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
        if (snapshot[field.name]) {
          if (!Array.isArray(snapshot[field.name])) {
            snapshot[field.name] = [snapshot[field.name]];
          }
          snapshot[field.name].push(value);
        } else {
          snapshot[field.name] = value;
        }
      });
    return snapshot;
  };

  const downloadSnapshot = (payload) => {
    if (!payload || !Object.keys(payload).length) {
      alert("Não há dados para exportar.");
      return;
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `cadastro-${Date.now()}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
  };

  const downloadCurrentState = () => downloadSnapshot(collectFormSnapshot());

  const setFieldValueFromSnapshot = (field, storedValue) => {
    if (!field) {
      return;
    }
    const value = Array.isArray(storedValue) ? storedValue[0] : storedValue;
    if (field.type === "checkbox") {
      field.checked =
        value === true || value === "true" || value === "on" || value === "1";
      field.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    if (field.type === "radio") {
      if (field.value === value) {
        field.checked = true;
      }
      field.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    field.value = value ?? "";
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  };

  const openSignatureModalFor = (triggerSelector, slot, needsSlot) => {
    if (!triggerSelector) {
      return;
    }
    let selector = triggerSelector;
    if (needsSlot && slot) {
      selector += `[data-slot='${slot}']`;
    }
    const trigger = document.querySelector(selector);
    if (trigger) {
      trigger.click();
    }
  };

  const resetSignatureFields = () => {
    form
      ?.querySelectorAll("input[name*='_signature']")
      .forEach((field) => {
        field.value = "";
        field.dispatchEvent(new Event("input", { bubbles: true }));
      });
  };

  const applyImportedSnapshot = (snapshot) => {
    if (!snapshot || typeof snapshot !== "object") {
      return;
    }
    Object.keys(snapshot).forEach((name) => {
      const selector = `[name="${cssEscape(name)}"]`;
      const fields = form?.querySelectorAll(selector);
      if (!fields || fields.length === 0) {
        return;
      }
      fields.forEach((field) => setFieldValueFromSnapshot(field, snapshot[name]));
    });
    const importedCount = snapshot["adventure_count"];
    if (importedCount && adventurerCountSelect) {
      adventurerCountSelect.value = `${importedCount}`.padStart(2, "0");
      const normalized = getNormalizedSlotCount();
      updateTabVisibility(normalized);
    }
    const importedSlot = snapshot["active_adventurer_slot"];
    if (importedSlot) {
      setActiveAdventurerSlot(importedSlot);
    }
    updateSlotPanels();
    alert("Dados importados. Reenvie fotos e assinaturas antes de concluir.");
    resetSignatureFields();
    syncCsrfFromCookie();
  };

  const handleImportFile = (file) => {
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result);
        applyImportedSnapshot(parsed);
      } catch (error) {
        alert("Arquivo inválido.");
      }
    };
    reader.onerror = () => {
      alert("Não foi possível ler o arquivo.");
    };
    reader.readAsText(file, "utf-8");
  };

  const syncCsrfFromCookie = () => {
    if (!csrfTokenInput) {
      return;
    }
    const cookieToken = getCookie("csrftoken");
    if (cookieToken) {
      csrfTokenInput.value = cookieToken;
    }
  };

  exportFormButton?.addEventListener("click", () => downloadCurrentState());
  importFormButton?.addEventListener("click", () => importFormInput?.click());
  importFormInput?.addEventListener("change", () => {
    const file = importFormInput?.files?.[0];
    if (!file) {
      return;
    }
    handleImportFile(file);
    importFormInput.value = "";
  });

  syncCsrfFromCookie();

  const togglePanelFields = (panel, enabled) => {
    panel.querySelectorAll("input, select, textarea").forEach((field) => {
      field.disabled = !enabled;
    });
  };

  const updateSlotPanels = () => {
    const allowedSlots = getAllowedSlots();
    slotPanels.forEach((panel) => {
      const slot = panel.dataset.slot;
      const isAllowed = allowedSlots.includes(slot);
      const shouldShow = isAllowed && slot === currentAdventurerSlot;
      panel.classList.toggle("is-hidden", !shouldShow);
      togglePanelFields(panel, isAllowed);
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

  if (adventurerCountSelect) {
    const markUserChange = () => {
      adventurerCountSelect.dataset.userChanged = "true";
    };
    if (!adventurerCountSelect.dataset.userChanged) {
      adventurerCountSelect.value = "01";
    }
    adventurerCountSelect.addEventListener("change", () => {
      markUserChange();
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
  }

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

  const normalizeSlotValue = (value) => {
    if (!value) {
      return defaultSlot;
    }
    return value.toString().padStart(2, "0");
  };

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
  const termChildInputs = Array.from(document.querySelectorAll("[data-slot-term-child]"));
  const termChildNameInputs = Array.from(
    document.querySelectorAll("[data-slot-term-child-name]")
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

    const describeField = (field) => {
      const label =
        field.closest("label")?.textContent?.trim().replace(/\s+/g, " ") ||
        field.dataset.placeholder ||
        field.name;
      const stepNumber = Number(field.closest(".adventurer-step")?.dataset.step) || 1;
      const slotPanel = field.closest("[data-slot]");
      const slot = slotPanel?.dataset.slot;
      const guidance =
        signatureGuidance.find((entry) => entry.pattern.test(field.name)) || null;
      return {
        field,
        label: guidance?.label || label,
        step: guidance?.step || stepNumber,
        slot,
        guidance,
      };
  };

  const buildErrorMarkup = (error) => {
    const li = document.createElement("li");
    const guidance = error.guidance;
    const text = document.createElement("span");
    text.textContent = `${error.label} — passo ${error.step}`;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ghost-btn";
    button.textContent = "Arrumar";
    button.addEventListener("click", () => {
      const targetSlot = error.slot || currentAdventurerSlot;
      setActiveAdventurerSlot(targetSlot);
      goToStep(error.step);
      error.field.focus();
      closeErrorModal();
    });
    li.appendChild(text);
    li.appendChild(button);
    if (guidance?.trigger) {
      const signBtn = document.createElement("button");
      signBtn.type = "button";
      signBtn.className = "ghost-btn";
      signBtn.textContent = "Assinar";
      signBtn.addEventListener("click", () => {
        const targetSlot = error.slot || currentAdventurerSlot;
        setActiveAdventurerSlot(targetSlot);
        goToStep(error.step);
        setTimeout(() => openSignatureModalFor(guidance.trigger, targetSlot, guidance.needsSlot), 150);
        closeErrorModal();
      });
      li.appendChild(signBtn);
    }
    return li;
  };

  const openErrorModal = (errors) => {
    if (!errorModal || !errorList) {
      return;
    }
    errorList.innerHTML = "";
    errors.forEach((error) => errorList.appendChild(buildErrorMarkup(error)));
    errorModal.classList.add("is-open");
  };

  const closeErrorModal = () => {
    if (!errorModal) {
      return;
    }
    errorModal.classList.remove("is-open");
  };

  closeErrorModalBtn?.addEventListener("click", closeErrorModal);
  const updateTermChildFieldsForSlot = (slot) => {
    const name = getSlotName(slot);
    termChildInputs.forEach((input) => {
      if (input.dataset.slotTermChild === slot) {
        applyAutoValue(input, name);
      }
    });
    termChildNameInputs.forEach((input) => {
      if (input.dataset.slotTermChildName === slot) {
        applyAutoValue(input, name);
      }
    });
  };

  const getSlotPanel = (slot) => document.querySelector(`[data-slot="${slot}"]`);

  const refreshDocumentRequirements = (slot) => {
    const panel = getSlotPanel(slot);
    if (!panel) return;
    const rgCheckbox = panel.querySelector(`[name="adventure_rg_missing_${slot}"]`);
    const cpfCheckbox = panel.querySelector(`[name="adventure_cpf_missing_${slot}"]`);
    const rgField = panel.querySelector(`[name="adventure_rg_${slot}"]`);
    const rgIssuerField = panel.querySelector(`[name="adventure_rg_issuer_${slot}"]`);
    const cpfField = panel.querySelector(`[name="adventure_cpf_${slot}"]`);
    const certidaoField = panel.querySelector(`[name="adventure_certidao_${slot}"]`);
    if (rgField) {
      rgField.required = !(rgCheckbox?.checked);
    }
    if (rgIssuerField) {
      rgIssuerField.required = !(rgCheckbox?.checked);
    }
    if (cpfField) {
      cpfField.required = !(cpfCheckbox?.checked);
    }
    if (certidaoField) {
      certidaoField.required = Boolean(rgCheckbox?.checked && cpfCheckbox?.checked);
    }
  };

  const missingCheckboxes = Array.from(document.querySelectorAll("[data-missing-checkbox]"));
  missingCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const slot = checkbox.dataset.slotFlag;
      if (!slot) {
        return;
      }
      refreshDocumentRequirements(slot);
    });
  });

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
    updateTermChildFieldsForSlot(slot);
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
    const normalized = normalizeSlotValue(slot || defaultSlot);
    const allowedSlots = getAllowedSlots();
    const fallbackSlot = allowedSlots[0] || defaultSlot;
    const finalSlot = allowedSlots.includes(normalized) ? normalized : fallbackSlot;
    currentAdventurerSlot = finalSlot;
    if (syncInput && activeSlotInput) {
      activeSlotInput.value = finalSlot;
    }
    adventurerTabs.forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.adventurerTab === finalSlot);
    });
    refreshSlotMetadata(finalSlot);
    updateSlotPanels();
    loadPhotoPreview(finalSlot);
  };

  adventurerTabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveAdventurerSlot(tab.dataset.adventurerTab));
  });

  const initialCount = getNormalizedSlotCount();
  updateTabVisibility(initialCount);
  setActiveAdventurerSlot(currentAdventurerSlot, false);
  slotOrder.forEach((slot) => {
    refreshSlotMetadata(slot);
    refreshDocumentRequirements(slot);
  });

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
  const isSlotFieldAllowed = (field, allowedSlotSet) => {
    const slot = findSlotForField(field);
    if (!slot) {
      return true;
    }
    return allowedSlotSet.has(slot);
  };

  form?.addEventListener("submit", (event) => {
    const allowedSlots = new Set(getAllowedSlots());
    const invalidFields = Array.from(form.querySelectorAll(":invalid")).filter((field) =>
      isSlotFieldAllowed(field, allowedSlots)
    );
    const requiredCheckboxes = Array.from(
      form.querySelectorAll("input[type='checkbox'][required]")
    )
      .filter((checkbox) => !checkbox.checked)
      .filter((checkbox) => isSlotFieldAllowed(checkbox, allowedSlots));
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
      const errors = highlightedFields.map(describeField);
      openErrorModal(errors);
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
