/**
 * cart.js — AJAX quantity updates for the cart page and "Add to Cart" functionality from the catalogue modal.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- Cart Page AJAX Quantity Updates ---
  const qtyMinusBtns = document.querySelectorAll('.qty-minus');
  const qtyPlusBtns = document.querySelectorAll('.qty-plus');
  const qtyInputs = document.querySelectorAll('.qty-value');

  function updateCartAJAX(productId, quantity) {
    const formData = new URLSearchParams();
    formData.append('product_id', productId);
    formData.append('quantity', quantity);

    // Get CSRF token from cookies
    const getCookie = (name) => {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    };
    const csrftoken = getCookie('csrftoken');

    fetch('/cart/update/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData.toString()
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Update nav badge
        const badge = document.getElementById('cartBadge');
        const badgeMobile = document.getElementById('cartBadgeMobile');
        
        if (badge) {
          if (data.cart_count > 0) {
            badge.textContent = data.cart_count;
            badge.style.display = 'flex';
          } else {
            badge.style.display = 'none';
          }
        }
        
        if (badgeMobile) {
          if (data.cart_count > 0) {
            badgeMobile.textContent = data.cart_count;
            badgeMobile.style.display = 'flex';
          } else {
            badgeMobile.style.display = 'none';
          }
        }

        // Update summaries
        const subtotal = document.getElementById('summarySubtotal');
        const tax = document.getElementById('summaryTax');
        const shipping = document.getElementById('summaryShipping');
        const total = document.getElementById('summaryTotal');

        if (subtotal) subtotal.textContent = '₹' + Math.round(parseFloat(data.totals.subtotal));
        if (tax) tax.textContent = '₹' + Math.round(parseFloat(data.totals.tax));
        if (shipping) {
          const shipVal = parseFloat(data.totals.shipping);
          shipping.textContent = shipVal === 0 ? 'FREE' : '₹' + Math.round(shipVal);
        }
        if (total) total.textContent = '₹' + Math.round(parseFloat(data.totals.total));
        
        // Reload page if item was removed (quantity hit 0)
        if (quantity <= 0) {
          window.location.reload();
        } else {
          // Update item total locally
          const row = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
          if (row) {
            const priceText = row.querySelector('.cart-item-price').textContent.replace('₹', '').replace(/,/g, '');
            const price = parseFloat(priceText);
            const itemTotal = row.querySelector('.cart-item-total');
            if (itemTotal && !isNaN(price)) {
              itemTotal.textContent = '₹' + (price * quantity).toFixed(2);
            }
          }
        }
      }
    })
    .catch(err => console.error('Cart update error:', err));
  }

  // Bind minus buttons
  qtyMinusBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const id = btn.getAttribute('data-id');
      const input = document.querySelector(`.qty-value[data-id="${id}"]`);
      if (input) {
        let val = parseInt(input.value);
        if (val > 1) {
          val--;
          input.value = val;
          updateCartAJAX(id, val);
        } else if (val === 1) {
          if (confirm('Remove item from cart?')) {
            updateCartAJAX(id, 0);
          }
        }
      }
    });
  });

  // Bind plus buttons
  qtyPlusBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const id = btn.getAttribute('data-id');
      const input = document.querySelector(`.qty-value[data-id="${id}"]`);
      if (input) {
        let val = parseInt(input.value);
        val++;
        input.value = val;
        updateCartAJAX(id, val);
      }
    });
  });

  // Bind input blur
  qtyInputs.forEach(input => {
    input.addEventListener('change', () => {
      const id = input.getAttribute('data-id');
      let val = parseInt(input.value);
      if (isNaN(val) || val < 1) {
        val = 1;
        input.value = 1;
      }
      updateCartAJAX(id, val);
    });
  });

  // --- Modal Add to Cart (Catalogue Listing Page) ---
  const modalAddToCartBtn = document.getElementById('modalAddToCart');
  if (modalAddToCartBtn) {
    modalAddToCartBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const productId = modalAddToCartBtn.getAttribute('data-id');
      if (!productId) return;

      const getCookie = (name) => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      };
      const csrftoken = getCookie('csrftoken');

      const formData = new URLSearchParams();
      formData.append('quantity', '1');

      // Add loading state
      const originalText = modalAddToCartBtn.innerHTML;
      modalAddToCartBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';
      modalAddToCartBtn.disabled = true;

      fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Update nav badges
          const badge = document.getElementById('cartBadge');
          const badgeMobile = document.getElementById('cartBadgeMobile');
          
          if (badge) {
            badge.textContent = data.cart_count;
            badge.style.display = 'flex';
          }
          if (badgeMobile) {
            badgeMobile.textContent = data.cart_count;
            badgeMobile.style.display = 'flex';
          }

          // Show success message
          modalAddToCartBtn.innerHTML = '<i class="fa-solid fa-check"></i> Added';
          modalAddToCartBtn.classList.remove('btn-primary');
          modalAddToCartBtn.style.backgroundColor = '#2ECC71';
          modalAddToCartBtn.style.color = 'white';
          
          // Revert after 2 seconds
          setTimeout(() => {
            modalAddToCartBtn.innerHTML = originalText;
            modalAddToCartBtn.disabled = false;
            modalAddToCartBtn.classList.add('btn-primary');
            modalAddToCartBtn.style.backgroundColor = '';
          }, 2000);
        }
      })
      .catch(err => {
        console.error('Add to cart error:', err);
        modalAddToCartBtn.innerHTML = originalText;
        modalAddToCartBtn.disabled = false;
      });
    });
  }
});
