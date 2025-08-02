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
        alert('An error occurred while placing your order. Please try again.');
    })
    .finally(() => {
        setLoading(false);
    });
}