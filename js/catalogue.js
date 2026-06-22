/**
 * AKIDS — Catalogue Script
 * Handles product rendering, search, filtering, sorting, layout toggle, and modals.
 */

// We expect `CATALOGUE_DATA` to be defined globally by the specific catalogue's data.js file
// Example: let CATALOGUE_DATA = INDOOR_PRODUCTS; 
// We will set this variable in the HTML script tag before loading this file.

document.addEventListener('DOMContentLoaded', () => {
  if (typeof CATALOGUE_DATA === 'undefined') {
    console.error("CATALOGUE_DATA is not defined.");
    return;
  }

  const productGrid = document.getElementById('productGrid');
  const searchInput = document.getElementById('searchInput');
  const categoryFilter = document.getElementById('categoryFilter');
  const sortSelect = document.getElementById('sortSelect');
  const resultsCount = document.getElementById('resultsCount');
  
  const layoutGridBtn = document.getElementById('layoutGrid');
  const layoutListBtn = document.getElementById('layoutList');

  // Modal Elements
  const quickViewModal = document.getElementById('quickViewModal');
  const modalClose = document.getElementById('modalClose');
  const modalName = document.getElementById('modalName');
  const modalSku = document.getElementById('modalSku');
  const modalDesc = document.getElementById('modalDesc');
  const modalCategory = document.getElementById('modalCategory');
  const modalPrice = document.getElementById('modalPrice');
  const modalSpecsBody = document.getElementById('modalSpecsBody');
  const modalIcon = document.getElementById('modalIcon');

  let currentData = [...CATALOGUE_DATA];

  // Initialize Categories Dropdown
  const initCategories = () => {
    const categories = new Set();
    CATALOGUE_DATA.forEach(p => categories.add(p.category));
    
    // Convert to array and sort alphabetically
    const sortedCats = Array.from(categories).sort();
    
    sortedCats.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat;
      option.textContent = cat;
      categoryFilter.appendChild(option);
    });
  };

  // Render Products
  const renderProducts = (products) => {
    productGrid.innerHTML = '';
    
    if (products.length === 0) {
      productGrid.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-box-open"></i>
          <h3>No products found</h3>
          <p class="text-muted">Try adjusting your search or filters to find what you're looking for.</p>
        </div>
      `;
      resultsCount.textContent = `Showing 0 results`;
      return;
    }

    resultsCount.textContent = `Showing ${products.length} results`;

    const fragment = document.createDocumentFragment();

    products.forEach(product => {
      const card = document.createElement('div');
      card.className = 'product-card reveal-scale visible'; // pre-visible to avoid scroll observer delay on filter
      
      // Determine icon based on tags/category
      let iconClass = 'fa-box';
      let iconColorClass = 'indoor';
      
      const pstr = (product.name + product.category + product.tags.join(' ')).toLowerCase();
      
      if (pstr.includes('slide')) iconClass = 'fa-person-arrow-down-to-line';
      else if (pstr.includes('swing')) iconClass = 'fa-child-reaching';
      else if (pstr.includes('rocker')) iconClass = 'fa-horse';
      else if (pstr.includes('trampoline')) iconClass = 'fa-people-arrows';
      else if (pstr.includes('furniture') || pstr.includes('desk') || pstr.includes('chair')) iconClass = 'fa-chair';
      else if (pstr.includes('fitness')) iconClass = 'fa-dumbbell';
      else if (pstr.includes('puzzle') || pstr.includes('educational')) iconClass = 'fa-puzzle-piece';
      else if (pstr.includes('rideon') || pstr.includes('car')) iconClass = 'fa-car-side';
      else if (pstr.includes('ball')) iconClass = 'fa-basketball';
      else if (pstr.includes('part') || pstr.includes('component')) iconClass = 'fa-gear';

      if (product.tags.includes('outdoor')) iconColorClass = 'outdoor';
      if (product.tags.includes('parts')) iconColorClass = 'parts';

      let badgeHtml = '';
      if (product.badge) {
        let badgeClass = 'badge-popular';
        if (product.badge.toLowerCase() === 'new') badgeClass = 'badge-new';
        if (product.badge.toLowerCase() === 'best seller') badgeClass = 'badge-bestseller';
        badgeHtml = `<div class="badge ${badgeClass}">${product.badge}</div>`;
      }

      card.innerHTML = `
        <div class="card-image-wrap">
          ${badgeHtml}
          <div class="card-image-placeholder">
            <i class="fa-solid ${iconClass} card-icon ${iconColorClass}"></i>
          </div>
          <button class="btn-wishlist" aria-label="Add to wishlist"><i class="fa-regular fa-heart"></i></button>
        </div>
        <div class="card-body">
          <div class="card-category">${product.category}</div>
          <h3 class="card-name">${product.name}</h3>
          <div class="card-sku">SKU: ${product.sku}</div>
          <p class="card-desc">${product.description}</p>
          <div class="card-footer">
            <div class="card-price ${product.price === 0 ? 'inquire' : ''}">${product.priceLabel}</div>
            <button class="btn btn-primary btn-sm btn-enquire" data-id="${product.id}">Quick View</button>
          </div>
        </div>
      `;

      fragment.appendChild(card);
    });

    productGrid.appendChild(fragment);

    // Attach Quick View events
    document.querySelectorAll('.btn-enquire').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const productId = e.target.getAttribute('data-id');
        openQuickView(productId);
      });
    });
    
    // Wishlist toggle (visual only)
    document.querySelectorAll('.btn-wishlist').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const icon = e.currentTarget.querySelector('i');
        if (icon.classList.contains('fa-regular')) {
          icon.classList.remove('fa-regular');
          icon.classList.add('fa-solid');
          icon.style.color = 'var(--color-danger)';
        } else {
          icon.classList.remove('fa-solid');
          icon.classList.add('fa-regular');
          icon.style.color = '';
        }
      });
    });
  };

  // Filter & Sort Logic
  const applyFilters = () => {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedCat = categoryFilter.value;
    const sortBy = sortSelect.value;

    // Filter
    currentData = CATALOGUE_DATA.filter(p => {
      const matchSearch = p.name.toLowerCase().includes(searchTerm) || 
                          p.sku.toLowerCase().includes(searchTerm) ||
                          p.tags.some(t => t.toLowerCase().includes(searchTerm));
      const matchCat = selectedCat === 'all' || p.category === selectedCat;
      return matchSearch && matchCat;
    });

    // Sort
    if (sortBy === 'name-asc') {
      currentData.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === 'name-desc') {
      currentData.sort((a, b) => b.name.localeCompare(a.name));
    } else if (sortBy === 'price-asc') {
      currentData.sort((a, b) => {
        // Push 0 price (inquire) to bottom when sorting low to high
        if (a.price === 0) return 1;
        if (b.price === 0) return -1;
        return a.price - b.price;
      });
    } else if (sortBy === 'price-desc') {
      currentData.sort((a, b) => b.price - a.price);
    }

    renderProducts(currentData);
  };

  // Event Listeners for Filters
  searchInput.addEventListener('input', applyFilters);
  categoryFilter.addEventListener('change', applyFilters);
  sortSelect.addEventListener('change', applyFilters);

  // Layout Toggles
  layoutGridBtn.addEventListener('click', () => {
    productGrid.classList.remove('list-view');
    layoutGridBtn.classList.add('active');
    layoutListBtn.classList.remove('active');
  });

  layoutListBtn.addEventListener('click', () => {
    productGrid.classList.add('list-view');
    layoutListBtn.classList.add('active');
    layoutGridBtn.classList.remove('active');
  });

  // Modal Logic
  const openQuickView = (productId) => {
    const product = CATALOGUE_DATA.find(p => p.id === productId);
    if (!product) return;

    modalName.textContent = product.name;
    modalSku.textContent = `SKU: ${product.sku}`;
    modalCategory.textContent = product.category;
    modalDesc.textContent = product.description;
    
    modalPrice.textContent = product.priceLabel;
    if (product.price === 0) {
      modalPrice.classList.add('inquire');
    } else {
      modalPrice.classList.remove('inquire');
    }

    // Set specs
    modalSpecsBody.innerHTML = '';
    const specs = product.specs || {};
    let hasSpecs = false;
    for (const [key, val] of Object.entries(specs)) {
      hasSpecs = true;
      const tr = document.createElement('tr');
      const th = document.createElement('th');
      // Capitalize key
      th.textContent = key.charAt(0).toUpperCase() + key.slice(1);
      const td = document.createElement('td');
      td.textContent = val;
      tr.appendChild(th);
      tr.appendChild(td);
      modalSpecsBody.appendChild(tr);
    }
    
    if (!hasSpecs) {
      modalSpecsBody.innerHTML = '<tr><td colspan="2" class="text-muted">Standard Specifications</td></tr>';
    }

    // Set Icon
    const pstr = (product.name + product.category + product.tags.join(' ')).toLowerCase();
    let iconClass = 'fa-box';
    if (pstr.includes('slide')) iconClass = 'fa-person-arrow-down-to-line';
    else if (pstr.includes('swing')) iconClass = 'fa-child-reaching';
    else if (pstr.includes('rocker')) iconClass = 'fa-horse';
    else if (pstr.includes('trampoline')) iconClass = 'fa-people-arrows';
    else if (pstr.includes('furniture') || pstr.includes('desk') || pstr.includes('chair')) iconClass = 'fa-chair';
    else if (pstr.includes('fitness')) iconClass = 'fa-dumbbell';
    else if (pstr.includes('puzzle') || pstr.includes('educational')) iconClass = 'fa-puzzle-piece';
    else if (pstr.includes('rideon') || pstr.includes('car')) iconClass = 'fa-car-side';
    else if (pstr.includes('ball')) iconClass = 'fa-basketball';
    else if (pstr.includes('part') || pstr.includes('component')) iconClass = 'fa-gear';
    
    modalIcon.className = `fa-solid ${iconClass} modal-icon`;

    // Show modal
    quickViewModal.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';
  };

  const closeQuickView = () => {
    quickViewModal.setAttribute('hidden', '');
    document.body.style.overflow = '';
  };

  modalClose.addEventListener('click', closeQuickView);
  quickViewModal.addEventListener('click', (e) => {
    if (e.target === quickViewModal) {
      closeQuickView();
    }
  });
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !quickViewModal.hasAttribute('hidden')) {
      closeQuickView();
    }
  });

  // Init
  initCategories();
  renderProducts(currentData);
});
