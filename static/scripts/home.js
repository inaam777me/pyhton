const urlParams = new URLSearchParams(window.location.search);
const tableNo = urlParams.get('table');

if (tableNo === null || tableNo === "") {
    document.getElementById("table-No").innerHTML = "Take a Way";
} else {
    document.getElementById("table-No").innerHTML = "Inside, " + tableNo;
}

let currentPage = 1;
document.getElementById('loadMore').addEventListener('click', function() {
    currentPage++;
    fetch(`/regular-menu?page=${currentPage}`)
        .then(response => response.json())
        .then(data => {
            if(data.items.length < 20) {
                this.style.display = 'none';
            }
        });
});

// function addToCart(itemId) {
//     fetch(`/add_to_cart/${itemId}`)
//         .then(response => response.json())
//         .then(data => {
//             // Update cart count in the UI
//             const cartCountElement = document.getElementById('cart-count');
//             if (cartCountElement) {
//                 cartCountElement.textContent = data.cart_total;
//             }
//             // Show a success message (optional)
//             alert('Item added to cart!');
//         })
//         .catch(error => {
//             console.error('Error:', error);
//             alert('Failed to add item to cart');
//         });
// }

// document.querySelectorAll('.card.selectable').forEach(card => {
//     card.addEventListener('click', () => {
//       card.classList.toggle('selected');
//       const checkbox = card.querySelector('input[type="checkbox"]');
//       checkbox.checked = !checkbox.checked;
//       console.log(`Card with ID ${card.id} selected: ${checkbox.checked}`);
//     });
//   });


document.addEventListener("DOMContentLoaded", function () {
  const selectedItemIds = new Set();

  // Get all select buttons
  const buttons = document.querySelectorAll(".select-btn");

  buttons.forEach(button => {
    button.addEventListener("click", function () {
      const itemId = this.getAttribute("data-item-id");
      const checkbox = this.nextElementSibling;

      // Toggle selection
      if (selectedItemIds.has(itemId)) {
        selectedItemIds.delete(itemId);
        checkbox.checked = false;
        this.classList.remove("btn-primary");
        this.classList.add("btn-outline-secondary");
        this.textContent = "Select";
      } else {
        selectedItemIds.add(itemId);
        checkbox.checked = true;
        this.classList.remove("btn-outline-secondary");
        this.classList.add("btn-primary");
        this.textContent = "Selected";
      }

      // Optional: call the processing function
      processSelectedItems([...selectedItemIds]);
    });
  });

  // Custom function to process selected items
  window.processSelectedItems = function (items) {
    console.log("Selected item IDs:", items);

    // You can add custom logic here
    // Example: send to server via fetch(), update UI, etc.
  };
});
