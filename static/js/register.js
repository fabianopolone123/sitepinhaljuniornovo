document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registration-form");
  const feedback = document.getElementById("form-feedback");
  const addButton = document.getElementById("add-adventurer");
  const adventurerList = document.getElementById("adventurer-list");
  const template = document.getElementById("adventurer-template");

  const responsavelNomeInput = document.getElementById("responsavel_nome");
  const responsavelSobrenomeInput = document.getElementById("responsavel_sobrenome");
  const responsavelTelefoneInput = document.getElementById("responsavel_telefone");
  const responsavelWhatsappInput = document.getElementById("responsavel_whatsapp");

  const showFeedback = (message, type = "error") => {
    if (!feedback) return;
    feedback.textContent = message;
    feedback.classList.toggle("form-feedback--error", type === "error");
    feedback.classList.toggle("form-feedback--success", type === "success");
  };

  const setError = (element) => {
    const group = element.closest(".field-group");
    const messageElement = group?.querySelector(".error-message");
    const message =
      element.dataset.errorMessage ||
      group?.dataset.fieldName ||
      "Preencha este campo.";

    if (messageElement) {
      messageElement.textContent = message;
    }
    element.classList.add("input-error");
  };

  const clearError = (element) => {
    const group = element.closest(".field-group");
    const messageElement = group?.querySelector(".error-message");
    if (messageElement) {
      messageElement.textContent = "";
    }
    element.classList.remove("input-error");
  };

  const updatePreview = (input) => {
    const preview = input.closest(".file-group")?.querySelector(".file-preview");
    if (!preview) return;
    const placeholder = preview.querySelector(".preview-placeholder");
    const existingImg = preview.querySelector("img");
    if (input.files && input.files[0]) {
      const reader = new FileReader();
      reader.addEventListener("load", () => {
        if (existingImg) {
          existingImg.src = reader.result;
        } else {
          const img = document.createElement("img");
          img.src = reader.result;
          preview.appendChild(img);
        }
        if (placeholder) placeholder.style.display = "none";
      });
      reader.readAsDataURL(input.files[0]);
    } else {
      if (existingImg) {
        existingImg.remove();
      }
      if (placeholder) placeholder.style.display = "";
    }
  };

  const registerFieldListeners = (root) => {
    const fields = root.querySelectorAll("input, textarea, select");
    fields.forEach((field) => {
      field.addEventListener("input", () => {
        clearError(field);
        if (field.name?.startsWith("emergencia_")) {
          delete field.dataset.autoValue;
        }
      });
      field.addEventListener("change", () => {
        clearError(field);
        if (field.type === "file") {
          updatePreview(field);
        }
      });
      field.addEventListener("invalid", (event) => {
        event.preventDefault();
        setError(field);
      });
    });
  };

  const getResponsibleFullName = () => {
    return [
      responsavelNomeInput?.value?.trim(),
      responsavelSobrenomeInput?.value?.trim(),
    ]
      .filter(Boolean)
      .join(" ");
  };

  const syncAutoField = (field, value) => {
    if (!field || !value) return;
    const normalizedValue = value.trim();
    if (!normalizedValue) {
      return;
    }

    const existingValue = field.value?.trim();
    const lastAuto = field.dataset?.autoValue?.trim();

    if (!existingValue || existingValue === lastAuto) {
      field.value = normalizedValue;
      field.dataset.autoValue = normalizedValue;
    }
  };

  const prefillEmergencyContacts = (card) => {
    const emergencyName = card.querySelector('[name="emergencia_nome[]"]');
    const emergencyPhone = card.querySelector('[name="emergencia_telefone[]"]');
    const emergencyWhatsapp = card.querySelector('[name="emergencia_whatsapp[]"]');

    const responsibleName = getResponsibleFullName();
    const responsiblePhone = responsavelTelefoneInput?.value?.trim();
    const responsibleWhatsapp = responsavelWhatsappInput?.value?.trim();

    syncAutoField(emergencyName, responsibleName);
    syncAutoField(emergencyPhone, responsiblePhone);
    syncAutoField(emergencyWhatsapp, responsibleWhatsapp);
  };

  const updateEmergencyContacts = () => {
    if (!adventurerList) return;
    adventurerList.querySelectorAll(".adventurer-card").forEach(prefillEmergencyContacts);
  };

  let whatsappManuallyEdited = false;
  let lastAutoWhatsappValue = "";

  const handleWhatsappInput = () => {
    if (!responsavelWhatsappInput) return;
    const hasValue = Boolean(responsavelWhatsappInput.value?.trim());
    whatsappManuallyEdited = hasValue;
    if (hasValue) {
      lastAutoWhatsappValue = "";
    }
    updateEmergencyContacts();
  };

  const syncWhatsappFromPhone = () => {
    if (!responsavelTelefoneInput || !responsavelWhatsappInput) return;
    const phoneValue = responsavelTelefoneInput.value?.trim();
    const whatsappValue = responsavelWhatsappInput.value?.trim();

    if (!whatsappManuallyEdited && phoneValue) {
      if (!whatsappValue || whatsappValue === lastAutoWhatsappValue) {
        responsavelWhatsappInput.value = phoneValue;
        lastAutoWhatsappValue = phoneValue;
      }
    } else if (!phoneValue) {
      lastAutoWhatsappValue = "";
    }
    updateEmergencyContacts();
  };

  if (form) {
    registerFieldListeners(form);

    form.addEventListener("submit", (event) => {
      const invalidFields = Array.from(form.querySelectorAll(":invalid"));
      if (invalidFields.length) {
        event.preventDefault();
        invalidFields.forEach(setError);
        invalidFields[0].focus();
        showFeedback(
          "Há campos obrigatórios marcados em vermelho — complete-os para continuar.",
          "error"
        );
      } else {
        showFeedback(
          "Enviando o cadastro…",
          "success"
        );
      }
    });
  }

  const refreshAdventurerTitles = () => {
    adventurerList.querySelectorAll(".adventurer-card").forEach((card, idx) => {
      const title = card.querySelector(".adventurer-title");
      if (title) {
        title.textContent = `Aventureiro #${idx + 1}`;
      }
    });
  };

  const createAdventurerBlock = () => template.content.firstElementChild.cloneNode(true);

  if (addButton) {
    addButton.addEventListener("click", () => {
      const block = createAdventurerBlock();
      adventurerList.appendChild(block);
      registerFieldListeners(block);
      refreshAdventurerTitles();
      updateEmergencyContacts();
      showFeedback("Um novo aventureiro foi adicionado ao formulário.", "success");
    });
  }

  refreshAdventurerTitles();
  updateEmergencyContacts();

  responsavelTelefoneInput?.addEventListener("input", syncWhatsappFromPhone);
  responsavelWhatsappInput?.addEventListener("input", handleWhatsappInput);
  responsavelNomeInput?.addEventListener("input", updateEmergencyContacts);
  responsavelSobrenomeInput?.addEventListener("input", updateEmergencyContacts);
});
