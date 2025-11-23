// static/js/scheme.js

document.addEventListener('DOMContentLoaded', () => {
  // If on scheme form page, populate categories and wire submit
  if (typeof SCHEME_NAME !== 'undefined' && SCHEME_NAME) {
    loadSchemeCategories(SCHEME_NAME);
    document.getElementById('submitBtn').addEventListener('click', submitForm);
    document.getElementById('closeModal').addEventListener('click', hideModal);
      // OK button in ticket modal (if present)
      const okBtn = document.getElementById('ticketOkBtn');
      if (okBtn) okBtn.addEventListener('click', hideModal);
    document.getElementById('ticketModal').addEventListener('click', (e) => {
      if (e.target.id === 'ticketModal') hideModal();
    });
  }
});

function loadSchemeCategories(scheme) {
  fetch(`/scheme_options?scheme=${encodeURIComponent(scheme)}`)
    .then(r => r.json())
    .then(items => {
      const sel = document.getElementById('schemeCategory');
      sel.innerHTML = '';
      items.forEach(it => {
        const opt = document.createElement('option');
        opt.value = it;
        opt.textContent = it;
        sel.appendChild(opt);
      });
    })
    .catch(err => {
      console.error("Failed to load scheme categories:", err);
    });
}

function submitForm() {
  const payload = {
    scheme_name: SCHEME_NAME,
    scheme_category: document.getElementById('schemeCategory').value,
    scheme_subcategory: document.getElementById('schemeSubcategory').value,
    prabhag: document.getElementById('prabhag').value.trim(),
    address: document.getElementById('address').value.trim(),
    contact: document.getElementById('contact').value.trim(),
    email: document.getElementById('email').value.trim()
  };

  // Basic client-side validation
  if (!payload.scheme_category || !payload.scheme_subcategory || !payload.prabhag || !payload.address || !payload.contact) {
    alert("कृपया सर्व आवश्यक फील्ड भरा.");
    return;
  }

  fetch('/submit_scheme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      showTicketModal(data.application_id);
      // optionally reset form
      document.getElementById('schemeForm').reset();
      // re-load categories since reset clears select
      loadSchemeCategories(SCHEME_NAME);
    } else {
      alert("सर्वर त्रुटी: " + data.message);
    }
  })
  .catch(err => {
    console.error(err);
    alert("तांत्रिक त्रुटी आली. कृपया पुन्हा प्रयत्न करा.");
  });
}

function showTicketModal(applicationId) {
  document.getElementById('ticketIdDisplay').textContent = applicationId;
  const modal = document.getElementById('ticketModal');
  modal.setAttribute('aria-hidden', 'false');
}

function hideModal() {
  const modal = document.getElementById('ticketModal');
  modal.setAttribute('aria-hidden', 'true');
}
