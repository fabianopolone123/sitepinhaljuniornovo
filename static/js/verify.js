document.addEventListener("DOMContentLoaded", () => {
  const codeInput = document.querySelector("input[name='code']");
  const passwordInputs = document.querySelectorAll("input[name^='new_password']");

  const createValidator = (input, message) => {
    input.setAttribute("inputmode", "numeric");
    input.setAttribute("pattern", "[0-9]{4}");
    input.setAttribute("title", message);

    const handler = () => {
      const value = input.value || "";
      if (!value) {
        input.setCustomValidity("");
        return;
      }
      if (/^[0-9]{4}$/.test(value)) {
        input.setCustomValidity("");
      } else {
        input.setCustomValidity(message);
      }
    };

    input.addEventListener("input", handler);
    input.addEventListener("blur", handler);
  };

  if (codeInput) {
    createValidator(codeInput, "Informe os quatro dígitos numéricos enviados no WhatsApp.");
    codeInput.focus();
  }

  passwordInputs.forEach((input) => {
    createValidator(input, "Informe quatro dígitos para a nova senha.");
  });
});
