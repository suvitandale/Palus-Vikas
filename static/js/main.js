// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
  // If on complaint page, populate choices and wire submit
  if (typeof MAIN_CATEGORY !== 'undefined' && MAIN_CATEGORY) {
    loadChoices(MAIN_CATEGORY);
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

function loadChoices(category) {
  fetch(`/choices?category=${encodeURIComponent(category)}`)
    .then(r => r.json())
    .then(items => {
      const sel = document.getElementById('subCategory');
      sel.innerHTML = '';
      items.forEach(it => {
        const opt = document.createElement('option');
        opt.value = it;
        opt.textContent = it;
        sel.appendChild(opt);
      });
    })
    .catch(err => {
      console.error("Failed to load choices:", err);
    });
}

function submitForm() {
  const payload = {
    main_category: MAIN_CATEGORY,
    sub_category: document.getElementById('subCategory').value,
    prabhag: document.getElementById('prabhag').value.trim(),
    address: document.getElementById('address').value.trim(),
    contact: document.getElementById('contact').value.trim(),
    email: document.getElementById('email').value.trim()
  };

  // Basic client-side validation
  if (!payload.sub_category || !payload.prabhag || !payload.address || !payload.contact) {
    alert("कृपया सर्व आवश्यक फील्ड भरा.");
    return;
  }

  fetch('/submit_complaint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      showTicketModal(data.ticket_id);
      // optionally reset form
      document.getElementById('complaintForm').reset();
      // re-load subcategory since reset clears select
      loadChoices(MAIN_CATEGORY);
    } else {
      alert("सर्वर त्रुटी: " + data.message);
    }
  })
  .catch(err => {
    console.error(err);
    alert("तांत्रिक त्रुटी आली. कृपया पुन्हा प्रयत्न करा.");
  });
}

function showTicketModal(ticketId) {
  document.getElementById('ticketIdDisplay').textContent = ticketId;
  const modal = document.getElementById('ticketModal');
  modal.setAttribute('aria-hidden', 'false');
}

function hideModal() {
  const modal = document.getElementById('ticketModal');
  modal.setAttribute('aria-hidden', 'true');
}
