document.addEventListener('DOMContentLoaded', function() {
  // Initialize variables
  const urlParams = new URLSearchParams(window.location.search);
  const tableNo = urlParams.get('table');
  const csrfToken = document.querySelector('input[name="csrf_token"]').value;
  
  // Set table number display
  document.getElementById("table-No").textContent = tableNo ? `Inside, ${tableNo}` : "Take a Way";
  
  // Initialize cart
  window.cart = JSON.parse(localStorage.getItem('cart')) || {};

  // Update UI with cart data
  updateCartUI();

  // Quantity button handlers
  document.querySelectorAll('.plus-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const itemId = this.dataset.itemId;
      updateCart(itemId, 1);
    });
  });

  document.querySelectorAll('.minus-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const itemId = this.dataset.itemId;
      updateCart(itemId, -1);
    });
  });

  // Form submission
  document.querySelector('form').addEventListener('submit', function(e) {
    if (Object.keys(cart).length === 0) {
      e.preventDefault();
      alert('Please select at least one item');
    }
  });

  // Cart functions
  function updateCart(itemId, change) {
    fetch('/update_cart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ item_id: itemId, change: change })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        if (data.quantity > 0) {
          cart[itemId] = data.quantity;
        } else {
          delete cart[itemId];
        }
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartUI();
      }
    });
  }

  function updateCartUI() {
    // Update quantity displays
    document.querySelectorAll('[data-item-id]').forEach(el => {
      const itemId = el.dataset.itemId;
      if (el.classList.contains('item-quantity')) {
        const quantity = cart[itemId] || 0;
        el.textContent = quantity;
        
        // Find corresponding checkbox
        const checkbox = document.querySelector(`.visible-checkbox[value="${itemId}"]`);
        if (checkbox) {
          checkbox.checked = quantity > 0;
        }
      }
    });

    // Update cart badge
    const totalItems = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
    const badge = document.querySelector('.quantity-badge');
    badge.textContent = totalItems;
    badge.style.display = totalItems > 0 ? 'flex' : 'none';
  }
});