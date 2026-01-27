document.addEventListener("DOMContentLoaded", () => {
  const copyBtn = document.querySelector("[data-copy-btn]");

  const showCopiedFeedback = (button) => {
    const original = button.textContent;
    button.textContent = "Copiado!";
    setTimeout(() => {
      button.textContent = original;
    }, 1800);
  };

  if (copyBtn) {
    copyBtn.addEventListener("click", async (event) => {
      const targetId = event.currentTarget.getAttribute("data-copy-target");
      const target = document.getElementById(targetId);
      if (!target) {
        return;
      }
      const text = target.value || target.textContent || "";
      try {
        await navigator.clipboard.writeText(text.trim());
        showCopiedFeedback(copyBtn);
      } catch (error) {
        target.select();
        document.execCommand("copy");
        showCopiedFeedback(copyBtn);
      }
    });
  }
});
