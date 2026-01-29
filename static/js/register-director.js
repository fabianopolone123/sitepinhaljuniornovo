document.addEventListener("DOMContentLoaded", () => {
  const steps = Array.from(document.querySelectorAll(".director-step"));
  const stepButtons = Array.from(document.querySelectorAll(".step-btn"));
  const nextBtn = document.querySelector("[data-next]");
  const prevBtn = document.querySelector("[data-prev]");
  const submitBtn = document.querySelector("[data-submit]");
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

  nextBtn?.addEventListener("click", () => goToStep(currentStep + 1));
  prevBtn?.addEventListener("click", () => goToStep(currentStep - 1));

  stepButtons.forEach((button) => {
    const target = Number(button.dataset.stepTarget);
    button.addEventListener("click", () => goToStep(target));
  });

  renderStep(currentStep);

  const termNameDisplay = document.querySelector("#term-name-display");
  const updateTermName = () => {
    const source = document.querySelector("#director_full_name");
    if (!termNameDisplay || !source) return;
    const value = source.value.trim();
    termNameDisplay.textContent = value || "[nome completo]";
  };

  const copyValueToTargets = (source, targets) => {
    if (!source || !targets.length) return;
    targets.forEach((target) => {
      if (!target || target.dataset.manual === "true") return;
      target.value = source.value;
    });
  };

  const setupSync = (sourceSelector, targetSelectors) => {
    const source = document.querySelector(sourceSelector);
    if (!source) return;
    const targets = targetSelectors
      .map((selector) => document.querySelector(selector))
      .filter(Boolean);
    const markManual = (event) => {
      if (!event.isTrusted) return;
      event.currentTarget.dataset.manual = "true";
    };
    targets.forEach((target) => {
      target.addEventListener("input", markManual);
    });
    source.addEventListener("input", () => copyValueToTargets(source, targets));
    copyValueToTargets(source, targets);
  };

  syncFullName();
  syncCPF();
  syncAddressFromInitial();
  setupSync("#term_rg_number", ["#director_rg"]);
  updateTermName();
  handlePhotoPreview();

  function syncFullName() {
    const first = document.querySelector("#responsavel_nome");
    const last = document.querySelector("#responsavel_sobrenome");
    const target = document.querySelector("#director_full_name");
    if (!target) return;
    const combined = [first?.value.trim(), last?.value.trim()].filter(Boolean).join(" ").trim();
    if (combined) {
      target.value = combined;
    }
    updateTermName();
  }

  function syncCPF() {
    const source = document.querySelector("#responsavel_cpf");
    const termTarget = document.querySelector("#term_cpf");
    const directorTarget = document.querySelector("#director_cpf");
    copyValueToTargets(source, [termTarget, directorTarget]);
  }

  function syncAddressFromInitial() {
  setupSync("#responsavel_street", ["#term_residence", "#director_street_address"]);
  setupSync("#responsavel_house_number", ["#term_number", "#director_house_number"]);
  setupSync("#responsavel_neighborhood", ["#term_neighborhood", "#director_neighborhood"]);
  setupSync("#responsavel_postal_code", ["#term_postal_code", "#director_postal_code"]);
  setupSync("#responsavel_city", ["#term_municipality", "#director_city"]);
  setupSync("#responsavel_state", ["#term_state", "#director_state"]);
  setupSync("#responsavel_telefone", ["#director_cellphone"]);
  }

  document.querySelector("#responsavel_nome")?.addEventListener("input", () => {
    syncFullName();
  });
  document.querySelector("#responsavel_sobrenome")?.addEventListener("input", () => {
    syncFullName();
  });
  document.querySelector("#director_full_name")?.addEventListener("input", () => {
    updateTermName();
  });
  document.querySelector("#responsavel_cpf")?.addEventListener("input", syncCPF);
  document.querySelector("#term_cpf")?.addEventListener("input", (event) => {
    copyValueToTargets(event.target, [document.querySelector("#director_cpf")]);
  });
  document.querySelector("#term_rg_number")?.addEventListener("input", (event) => {
    copyValueToTargets(event.target, [document.querySelector("#director_rg")]);
  });

  function handlePhotoPreview() {
    const input = document.querySelector("input[name='director_photo']");
    const previewWrapper = document.querySelector(".director-photo-preview");
    if (!input || !previewWrapper) return;
    const previewTemplate = previewWrapper.innerHTML;
    const showImage = (src) => {
      previewWrapper.innerHTML = "";
      const img = document.createElement("img");
      img.src = src;
      previewWrapper.appendChild(img);
    };
    input.addEventListener("change", () => {
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
  });
  };

  initSignatureModal({
    modalId: "director-signature-modal",
    triggerSelector: "[data-signature-trigger='director']",
    inputSelector: "#director-signature-input",
    previewSelector: "#director-signature-preview",
    placeholder: "Nenhum registro ainda",
  });

});
