document.addEventListener("DOMContentLoaded", () => {
  const menuButtons = document.querySelectorAll(".menu-item");
  const panels = document.querySelectorAll(".dashboard-panel");

  const setActivePanel = (key) => {
    panels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.id === key);
    });
    menuButtons.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.target === key);
    });
  };

  menuButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setActivePanel(button.dataset.target);
    });
  });

  const panelToggles = document.querySelectorAll("[data-toggle='panel-details']");
  panelToggles.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const targetId = trigger.dataset.target;
      const panel = document.getElementById(targetId);
      if (!panel) return;
      const isOpen = panel.classList.toggle("is-open");
      const toggleButton = trigger.querySelector(".ghost-btn");
      if (toggleButton) {
        toggleButton.textContent = isOpen ? "Ocultar detalhes" : "Ver detalhes";
      }
    });
  });

  const editButtons = document.querySelectorAll(".edit-entry");
  editButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const form = button.closest("form");
      if (!form) return;
      const fields = form.querySelectorAll("input, select, textarea");
      fields.forEach((field) => {
        field.removeAttribute("disabled");
      });
      const submit = form.querySelector(".submit-btn");
      if (submit) {
        submit.removeAttribute("disabled");
      }
      button.setAttribute("disabled", "disabled");
    });
  });

  setActivePanel("initial");

  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (button.classList.contains("is-active")) return;
      const target = button.dataset.tab;
      document.querySelectorAll(".finance-section").forEach((section) => {
        section.classList.toggle("is-hidden", section.id !== target);
      });
      tabButtons.forEach((tab) => tab.classList.remove("is-active"));
      button.classList.add("is-active");
    });
  });
});
