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
    const normalized = Math.min(Math.max(1, step), steps.length);
    currentStep = normalized;
    renderStep(currentStep);
  };

  nextBtn?.addEventListener("click", () => goToStep(currentStep + 1));
  prevBtn?.addEventListener("click", () => goToStep(currentStep - 1));

  stepButtons.forEach((button) => {
    const target = Number(button.dataset.stepTarget);
    button.addEventListener("click", () => goToStep(target));
  });

  renderStep(currentStep);

  const syncFullName = () => {
    const first = document.querySelector("#responsavel_nome")?.value.trim() || "";
    const last = document.querySelector("#responsavel_sobrenome")?.value.trim() || "";
    const target = document.querySelector("#director_full_name");
    if (!target) return;
    const combined = [first, last].filter(Boolean).join(" ").trim();
    if (combined) {
      target.value = combined;
    }
  };

  const syncCPF = () => {
    const source = document.querySelector("#responsavel_cpf")?.value.trim() || "";
    const target = document.querySelector("#director_cpf");
    if (target && source) {
      target.value = source;
    }
  };

  const syncMaritalStatus = () => {
    const source = document.querySelector("input[name='term_marital_status']")?.value.trim() || "";
    const target = document.querySelector("#director_marital_status");
    if (target && source) {
      target.value = source;
    }
  };

  document.querySelector("#responsavel_nome")?.addEventListener("input", syncFullName);
  document.querySelector("#responsavel_sobrenome")?.addEventListener("input", syncFullName);
  document.querySelector("#responsavel_cpf")?.addEventListener("input", syncCPF);
  document.querySelector("input[name='term_marital_status']")?.addEventListener("input", syncMaritalStatus);

  // Initialize sync in case fields already have value
  syncFullName();
  syncCPF();
  syncMaritalStatus();
});
