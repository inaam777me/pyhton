document.addEventListener('DOMContentLoaded', function() {
  // Initialize variables
  const urlParams = new URLSearchParams(window.location.search);
  const tableNo = urlParams.get('table');
  const csrfToken = document.querySelector('input[name="csrf_token"]').value;
  
  // Set table number display
  document.getElementById("table-No").textContent = tableNo ? `Inside, ${tableNo}` : "Take a Way";
  
  // Initialize cart from sessionStorage
  window.cart = JSON.parse(sessionStorage.getItem('cart')) || {};

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

  // Form submission handler
  document.querySelector('form').addEventListener('submit', function(e) {
    // Prepare form data with only items that have quantity > 0
    prepareFormData();
    
    // Check if cart is empty
    if (Object.keys(cart).length === 0) {
      e.preventDefault();
      alert('Please select at least one item');
      return;
    }
  });

  // Prepare form data before submission
  function prepareFormData() {
    const form = document.querySelector('form');
    const selectedItemsInputs = form.querySelectorAll('input[name="selected_items"]');
    const quantitiesInputs = form.querySelectorAll('input[name="quantities"]');
    
    // Reset all inputs
    selectedItemsInputs.forEach(input => {
      input.disabled = true;
    });
    quantitiesInputs.forEach(input => {
      input.disabled = true;
    });
    
    // Add only items with quantity > 0
    Object.entries(cart).forEach(([itemId, quantity]) => {
      if (quantity > 0) {
        const newItemInput = document.createElement('input');
        newItemInput.type = 'hidden';
        newItemInput.name = 'selected_items';
        newItemInput.value = itemId;
        form.appendChild(newItemInput);
        
        const newQuantityInput = document.createElement('input');
        newQuantityInput.type = 'hidden';
        newQuantityInput.name = 'quantities';
        newQuantityInput.value = quantity;
        form.appendChild(newQuantityInput);
      }
    });
  }

  // Cart functions
  function updateCart(itemId, change) {
    const currentQuantity = cart[itemId] || 0;
    const newQuantity = currentQuantity + change;
    
    if (newQuantity < 0) return;
    
    cart[itemId] = newQuantity;
    if (newQuantity === 0) {
      delete cart[itemId];
    }
    
    sessionStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    
    // Update the hidden input fields
    const quantityInput = document.querySelector(`.item-quantity-input[data-item-id="${itemId}"]`);
    if (quantityInput) {
      quantityInput.value = newQuantity;
    }
  }

  function updateCartUI() {
    // Update quantity displays
    document.querySelectorAll('[data-item-id]').forEach(el => {
      const itemId = el.dataset.itemId;
      if (el.classList.contains('item-quantity')) {
        const quantity = cart[itemId] || 0;
        el.textContent = quantity;
      }
    });

    // Update cart badge
    const totalItems = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
    const badge = document.querySelector('.quantity-badge');
    badge.textContent = totalItems;
    badge.style.display = totalItems > 0 ? 'flex' : 'none';
  }
});