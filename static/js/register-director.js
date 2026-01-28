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

  const termNameDisplay = document.querySelector("#term-name-display");
  const updateTermName = () => {
    const source = document.querySelector("#director_full_name");
    if (!termNameDisplay || !source) return;
    const value = source.value.trim();
    termNameDisplay.textContent = value || "[nome completo]";
  };

  const syncFullName = () => {
    const first = document.querySelector("#responsavel_nome")?.value.trim() || "";
    const last = document.querySelector("#responsavel_sobrenome")?.value.trim() || "";
    const target = document.querySelector("#director_full_name");
    if (!target) return;
    const combined = [first, last].filter(Boolean).join(" ").trim();
    if (combined) {
      target.value = combined;
    }
    updateTermName();
  };

  const syncCPF = () => {
    const source = document.querySelector("#responsavel_cpf")?.value.trim() || "";
    const termTarget = document.querySelector("#term_cpf");
    const directorTarget = document.querySelector("#director_cpf");
    if (termTarget && source) {
      termTarget.value = source;
    }
    if (directorTarget && source) {
      directorTarget.value = source;
    }
  };

  const copyValueIfEmpty = (source, target) => {
    if (!source || !target) return;
    const value = source.value.trim();
    if (!value) return;
    if (!target.value.trim() || target.dataset.autoSourceValue === value) {
      target.value = value;
      target.dataset.autoSourceValue = value;
    }
  };

  const syncAddressFromTerm = () => {
    copyValueIfEmpty(
      document.querySelector("#term_residence"),
      document.querySelector("#director_street_address")
    );
    copyValueIfEmpty(
      document.querySelector("#term_municipality"),
      document.querySelector("#director_city")
    );
    copyValueIfEmpty(
      document.querySelector("#term_marital_status"),
      document.querySelector("#director_marital_status")
    );
  };

  const handlePhotoPreview = () => {
    const input = document.querySelector("input[name='director_photo']");
    const previewWrapper = document.querySelector(".director-photo-preview");
    if (!input || !previewWrapper) return;
    const placeholder = previewWrapper.querySelector(".preview-placeholder");
    const showImage = (src) => {
      previewWrapper.innerHTML = "";
      const img = document.createElement("img");
      img.src = src;
      previewWrapper.appendChild(img);
    };
    const resetPreview = () => {
      previewWrapper.innerHTML = "";
      if (placeholder) {
        previewWrapper.appendChild(placeholder);
      }
    };
    input.addEventListener("change", () => {
      const file = input.files?.[0];
      if (!file) {
        resetPreview();
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        showImage(event.target.result);
      };
      reader.readAsDataURL(file);
    });
  };

  document.querySelector("#responsavel_nome")?.addEventListener("input", syncFullName);
  document.querySelector("#responsavel_sobrenome")?.addEventListener("input", syncFullName);
  document.querySelector("#director_full_name")?.addEventListener("input", updateTermName);
  document.querySelector("#responsavel_cpf")?.addEventListener("input", () => {
    syncCPF();
  });
  document.querySelector("#term_cpf")?.addEventListener("input", (event) => {
    copyValueIfEmpty(event.target, document.querySelector("#director_cpf"));
  });
  document
    .querySelector("#term_residence")
    ?.addEventListener("input", syncAddressFromTerm);
  document
    .querySelector("#term_municipality")
    ?.addEventListener("input", syncAddressFromTerm);
  document
    .querySelector("#term_marital_status")
    ?.addEventListener("input", syncAddressFromTerm);

  syncFullName();
  syncCPF();
  syncAddressFromTerm();
  updateTermName();
  handlePhotoPreview();
});
