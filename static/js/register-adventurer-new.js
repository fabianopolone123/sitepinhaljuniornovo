document.addEventListener("DOMContentLoaded", () => {
  const steps = Array.from(document.querySelectorAll("[data-flow-step-content]"));
  const stepButtons = Array.from(document.querySelectorAll("[data-flow-step]"));
  const nextButton = document.querySelector("[data-step-next]");
  const prevButton = document.querySelector("[data-step-prev]");
  const submitButton = document.querySelector("[data-step-submit]");
  const slotPanels = Array.from(document.querySelectorAll("[data-slot-panel]"));
  const medicalPanels = Array.from(document.querySelectorAll("[data-medical-slot]"));
  const termPanels = Array.from(document.querySelectorAll("[data-term-slot]"));
  const slotCountLabel = document.querySelector("[data-slot-count]");
  const addSlotButton = document.querySelector("[data-add-slot]");
  const hiddenStepInput = document.getElementById("flow-step");
  const maxSlots = slotPanels.length;
  let currentStep = 1;
  let activeSlots = 1;

  const updateStepVisibility = (step) => {
    currentStep = Math.min(Math.max(1, step), steps.length);
    steps.forEach((section) => {
      const stepId = Number(section.dataset.flowStepContent);
      section.classList.toggle("flow-step--active", stepId === currentStep);
    });
    stepButtons.forEach((button) => {
      button.classList.toggle("is-active", Number(button.dataset.flowStep) === currentStep);
    });
    if (submitButton) {
      submitButton.classList.toggle("hidden", currentStep !== steps.length);
    }
    if (nextButton) {
      nextButton.classList.toggle("hidden", currentStep === steps.length);
    }
    if (prevButton) {
      prevButton.disabled = currentStep === 1;
    }
    if (hiddenStepInput) {
      hiddenStepInput.value = currentStep;
    }
  };

  const updateSlots = () => {
    slotPanels.forEach((panel, index) => {
      panel.hidden = index >= activeSlots;
    });
    medicalPanels.forEach((panel, index) => {
      panel.hidden = index >= activeSlots || currentStep !== 3;
    });
    termPanels.forEach((panel, index) => {
      panel.hidden = index >= activeSlots || currentStep !== 4;
    });
    if (slotCountLabel) {
      slotCountLabel.textContent = `${activeSlots}`;
    }
    if (addSlotButton) {
      addSlotButton.disabled = activeSlots >= maxSlots;
    }
  };

  const goToStep = (targetStep) => {
    updateStepVisibility(targetStep);
    if (currentStep === 3) {
      medicalPanels.forEach((panel, index) => {
        panel.hidden = index >= activeSlots;
      });
    }
    if (currentStep === 4) {
      termPanels.forEach((panel, index) => {
        panel.hidden = index >= activeSlots;
      });
    }
  };

  nextButton?.addEventListener("click", () => {
    goToStep(currentStep + 1);
  });
  prevButton?.addEventListener("click", () => {
    goToStep(currentStep - 1);
  });
  stepButtons.forEach((button) => {
    button.addEventListener("click", () => {
      goToStep(Number(button.dataset.flowStep));
    });
  });

  addSlotButton?.addEventListener("click", () => {
    if (activeSlots >= maxSlots) {
      return;
    }
    activeSlots += 1;
    updateSlots();
  });

  const updateSlotNameLabels = () => {
    slotPanels.forEach((panel) => {
      const slot = panel.dataset.slot;
      const nameField = panel.querySelector(`[data-slot-name-input="${slot}"]`);
      const label = panel.querySelector(`[data-slot-name-label="${slot}"]`);
      if (label) {
        label.textContent = nameField?.value?.trim() || `Aventureiro ${slot}`;
      }
    });
  };

  const autoFields = Array.from(document.querySelectorAll("[data-auto-from]"));
  autoFields.forEach((target) => {
    const sourceName = target.dataset.autoFrom;
    const source = document.querySelector(`[name="${sourceName}"]`);
    if (!source) {
      return;
    }
    source.addEventListener("input", () => {
      if (target.dataset.userChanged === "true") {
        return;
      }
      target.value = source.value;
    });
    target.addEventListener("input", () => {
      target.dataset.userChanged = "true";
    });
  });

  slotPanels.forEach((panel) => {
    const slot = panel.dataset.slot;
    const nameInput = panel.querySelector(`[data-slot-name-input="${slot}"]`);
    nameInput?.addEventListener("input", () => {
      updateSlotNameLabels();
      updateTermChildNameLabels();
    });
  });
  const termNameSpans = Array.from(document.querySelectorAll("[data-term-child-name]"));
  const termNameInputs = Array.from(document.querySelectorAll("[data-term-child-name-input]"));

  const updateTermChildNameLabels = () => {
    termNameSpans.forEach((span) => {
      const slot = span.dataset.termChildName;
      const termInput = document.querySelector(`[data-term-child-name-input="${slot}"]`);
      const adventureInput = document.querySelector(`[data-slot-name-input="${slot}"]`);
      const fallback = `Aventureiro ${slot}`;
      span.textContent = termInput?.value?.trim() || adventureInput?.value?.trim() || fallback;
    });
  };

  termNameInputs.forEach((input) => {
    input.addEventListener("input", updateTermChildNameLabels);
  });
  updateStepVisibility(1);
  updateSlots();
  updateSlotNameLabels();
  updateTermChildNameLabels();

  const setTermDefaultDates = () => {
    const today = new Date().toISOString().split("T")[0];
    const termDateInputs = document.querySelectorAll('[name^="term_date_"]');
    termDateInputs.forEach((input) => {
      if (!input.value) {
        input.value = today;
      }
    });
  };

  setTermDefaultDates();

  if (window.initSignatureModal) {
    initSignatureModal({
      modalId: "responsavel-signature-modal",
      triggerSelector: "[data-trigger='responsavel']",
      placeholder: "Nenhum registro ainda",
    });
    initSignatureModal({
      modalId: "parent-signature-modal",
      triggerSelector: "[data-trigger='parent']",
      placeholder: "Nenhum registro ainda",
    });
    initSignatureModal({
      modalId: "adventure-data-signature-modal",
      triggerSelector: "[data-trigger='adventure-data']",
      placeholder: "Nenhum registro ainda",
    });
    initSignatureModal({
      modalId: "medical-signature-modal",
      triggerSelector: "[data-trigger='medical']",
      placeholder: "Nenhum registro ainda",
    });
    initSignatureModal({
      modalId: "adventurer-signature-modal",
      triggerSelector: "[data-trigger='adventurer']",
      placeholder: "Nenhum registro ainda",
    });
  }
});
