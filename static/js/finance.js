(function () {
  function toggleModal(overlay, show) {
    if (show) {
      overlay.classList.add('is-visible');
    } else {
      overlay.classList.remove('is-visible');
    }
  }

  function redirectTo(returnUrl) {
    if (returnUrl) {
      window.location.href = returnUrl;
      return;
    }
    if (document.referrer && document.referrer !== window.location.href) {
      window.location.href = document.referrer;
      return;
    }
    window.location.href = window.location.origin;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var overlay = document.querySelector('[data-payment-modal]');
    if (!overlay) {
      return;
    }

    var shouldShow = overlay.getAttribute('data-visible') === 'true';
    var returnUrl = overlay.getAttribute('data-return-url');
    var closeBtn = overlay.querySelector('[data-payment-modal-close]');

    function closeAndReturn() {
      toggleModal(overlay, false);
      setTimeout(function () {
        redirectTo(returnUrl);
      }, 150);
    }

    if (shouldShow) {
      toggleModal(overlay, true);
    }

    overlay.addEventListener('click', function (event) {
      if (event.target === overlay) {
        closeAndReturn();
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', closeAndReturn);
    }
  });
})();
