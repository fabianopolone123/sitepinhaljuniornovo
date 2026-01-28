(function () {
  function toggleModal(overlay, show) {
    overlay.classList.toggle('is-visible', show);
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

  function pollStatus(callback) {
    var interval = setInterval(function () {
      fetch(window.location.pathname + '?poll=1', {
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin',
      })
        .then(function (resp) {
          if (!resp.ok) {
            throw new Error('status ' + resp.status);
          }
          return resp.json();
        })
        .then(function (data) {
          if (data.status === 'A' || data.status === 'PAID') {
            clearInterval(interval);
            callback(data);
          }
        })
        .catch(function () {
          // ignore
        });
    }, 5000);
    return interval;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var overlay = document.querySelector('[data-payment-modal]');
    if (!overlay) {
      return;
    }

    var returnUrl = overlay.getAttribute('data-return-url');
    var closeBtn = overlay.querySelector('[data-payment-modal-close]');
    var main = document.querySelector('.finance-card');
    var status = main && main.getAttribute('data-charge-status');

    function closeAndReturn() {
      toggleModal(overlay, false);
      setTimeout(function () {
        redirectTo(returnUrl);
      }, 150);
    }

    if (overlay.getAttribute('data-visible') === 'true') {
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

    if (status !== 'PAID' && status !== 'A') {
      pollStatus(function () {
        toggleModal(overlay, true);
      });
    }
  });
})();
