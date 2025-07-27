document.addEventListener('DOMContentLoaded', function() {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            let isLoading = false;
            
            // Initialize cart from HTML data
            let cart = {};
            const cartItems = document.querySelectorAll('.cart-item-card');
            
            cartItems.forEach(item => {
                const itemId = item.dataset.itemId;
                const quantity = parseInt(item.querySelector('.quantity').textContent);
                const price = parseFloat(item.querySelector('.cart-item-price').dataset.price);
                
                cart[itemId] = {
                    quantity: quantity,
                    price: price,
                    total: quantity * price
                };
            });
            
            // Quantity adjustment handlers - using event delegation
            document.addEventListener('click', function(e) {
                if (isLoading) return;
                
                // Plus button
                if (e.target.closest('.plus-btn')) {
                    const btn = e.target.closest('.plus-btn');
                    updateQuantity(btn.dataset.itemId, 1);
                }
                
                // Minus button
                else if (e.target.closest('.minus-btn')) {
                    const btn = e.target.closest('.minus-btn');
                    updateQuantity(btn.dataset.itemId, -1);
                }
                
                // Remove button
                else if (e.target.closest('.btn-remove')) {
                    const btn = e.target.closest('.btn-remove');
                    if (confirm('Are you sure you want to remove this item from your cart?')) {
                        removeItem(btn.dataset.itemId);
                    }
                }
            });
            
            // Clear cart handler
            const clearCartBtn = document.getElementById('clear-cart');
            if (clearCartBtn) {
                clearCartBtn.addEventListener('click', function() {
                    if (!isLoading && confirm('Are you sure you want to clear your entire cart?')) {
                        clearCart();
                    }
                });
            }
            
            // Checkout handler
            const checkoutBtn = document.getElementById('checkout-btn');
            if (checkoutBtn) {
                checkoutBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (!isLoading) {
                        proceedToCheckout();
                    }
                });
            }
            
            function setLoading(state) {
                isLoading = state;
                document.querySelectorAll('button').forEach(btn => {
                    btn.disabled = state;
                });
                
                if (checkoutBtn) {
                    if (state) {
                        checkoutBtn.innerHTML = '<span class="loading"></span> Processing...';
                    } else {
                        checkoutBtn.innerHTML = '<i class="fas fa-credit-card me-1"></i> Checkout';
                    }
                }
            }
            
            function updateQuantity(itemId, change) {
                if (!cart[itemId]) return;
                
                const currentQuantity = cart[itemId].quantity;
                const newQuantity = currentQuantity + change;
                
                if (newQuantity <= 0) {
                    removeItem(itemId);
                    return;
                }
                
                // Update cart
                cart[itemId].quantity = newQuantity;
                cart[itemId].total = cart[itemId].price * newQuantity;
                
                // Update UI
                const itemElement = document.querySelector(`.cart-item-card[data-item-id="${itemId}"]`);
                if (itemElement) {
                    itemElement.querySelector('.quantity').textContent = newQuantity;
                    itemElement.querySelector('.cart-item-total').textContent = `Rs. ${cart[itemId].total.toFixed(2)}`;
                }
                
                // Update cart summary
                updateCartSummary();
            }
            
            function removeItem(itemId) {
                if (!cart[itemId]) return;
                
                // Remove from cart
                delete cart[itemId];
                
                // Remove from UI with animation
                const itemElement = document.querySelector(`.cart-item-card[data-item-id="${itemId}"]`);
                if (itemElement) {
                    itemElement.style.transform = 'translateX(-100%)';
                    itemElement.style.opacity = '0';
                    setTimeout(() => {
                        itemElement.remove();
                        
                        // Check if cart is empty
                        if (Object.keys(cart).length === 0) {
                            showEmptyCart();
                        } else {
                            updateCartSummary();
                        }
                    }, 300);
                }
            }
            
            function clearCart() {
                // Clear the cart object
                cart = {};
                
                // Remove all items from UI with animation
                const items = document.querySelectorAll('.cart-item-card');
                items.forEach((item, index) => {
                    setTimeout(() => {
                        item.style.transform = 'translateX(-100%)';
                        item.style.opacity = '0';
                        setTimeout(() => item.remove(), 300);
                    }, index * 100);
                });
                
                // After all animations complete, show empty cart
                setTimeout(() => {
                    showEmptyCart();
                }, items.length * 100 + 300);
            }
            
            function showEmptyCart() {
                const cartContainer = document.getElementById('cart-container');
                cartContainer.innerHTML = `
                    <div class="empty-cart">
                        <i class="fas fa-shopping-cart"></i>
                        <h4>Your cart is empty</h4>
                        <p>Looks like you haven't added anything to your cart yet</p>
                        <a href="/" class="btn btn-primary mt-2">
                            <i class="fas fa-utensils me-1"></i> Browse Menu
                        </a>
                    </div>
                `;
                
                // Hide action buttons
                const actionButtons = document.querySelector('.action-buttons');
                if (actionButtons) {
                    actionButtons.style.display = 'none';
                }
            }
            
            function updateCartSummary() {
                let totalItems = 0;
                let subtotal = 0;
                
                // Calculate totals
                for (const itemId in cart) {
                    totalItems += cart[itemId].quantity;
                    subtotal += cart[itemId].total;
                }
                
                // Update UI
                const totalItemsElement = document.getElementById('total-items');
                const subtotalElement = document.getElementById('subtotal');
                
                if (totalItemsElement) totalItemsElement.textContent = totalItems;
                if (subtotalElement) subtotalElement.textContent = subtotal.toFixed(2);
            }
            
            function proceedToCheckout() {
                setLoading(true);
                
                // Prepare order data
                const orderItems = [];
                for (const itemId in cart) {
                    orderItems.push({
                        id: itemId,
                        quantity: cart[itemId].quantity,
                        price: cart[itemId].price
                    });
                }
                
                const orderData = {
                    items: orderItems,
                    total: parseFloat(document.getElementById('subtotal').textContent)
                };
                
                // Send to server
                fetch('/submit_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(orderData)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Redirect to confirmation page
                        window.location.href = '/order_confirmation?order_id=' + data.order_id;
                    } else {
                        alert(data.message || 'Failed to place order');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while placing your order');
                })
                .finally(() => {
                    setLoading(false);
                });
            }
        });