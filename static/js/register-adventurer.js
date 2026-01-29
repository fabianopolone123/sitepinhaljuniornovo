document.addEventListener("DOMContentLoaded", () => {
  const steps = Array.from(document.querySelectorAll(".adventurer-step"));
  const stepButtons = Array.from(document.querySelectorAll(".step-btn"));
  const nextBtn = document.querySelector("[data-next]");
  const prevBtn = document.querySelector("[data-prev]");
  const submitBtn = document.querySelector("[data-submit]");
  const form = document.querySelector(".adventurer-form");
  let currentStep = 1;

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
      field.addEventListener("change", () => handlePhotoPreview());
    }
  });

  const toggleDependentDetail = (select) => {
    if (!select?.dataset?.detailTarget) return;
    const detail = document.getElementById(select.dataset.detailTarget);
    if (!detail) return;
    detail.classList.toggle("is-active", select.value === "sim");
  };

  ["medical_plan", "medical_heart_meds", "medical_diabetic_meds", "medical_kidney_meds"].forEach((name) => {
    const select = form?.querySelector(`[name='${name}']`);
    if (!select) return;
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

  const handlePhotoPreview = () => {
    const input = document.querySelector("input[name='adventure_photo']");
    const previewWrapper = document.querySelector(".adventurer-photo-preview");
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

  handlePhotoPreview();
  renderStep(currentStep);
  initSignatureModal({
    modalId: "adventurer-signature-modal",
    triggerSelector: "[data-signature-trigger='adventurer']",
    inputSelector: "#adventurer-signature-input",
    previewSelector: "#adventurer-signature-preview",
    placeholder: "Nenhum registro ainda",
  });
});
