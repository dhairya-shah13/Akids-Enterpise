/**
 * search.js — Live search functionality for the global navigation bar.
 */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('navSearchInput');
  const searchResults = document.getElementById('navSearchResults');
  let debounceTimeout;

  if (!searchInput || !searchResults) return;

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();

    clearTimeout(debounceTimeout);

    if (query.length < 2) {
      searchResults.style.display = 'none';
      searchResults.innerHTML = '';
      return;
    }

    // Debounce the API call to avoid spamming the backend
    debounceTimeout = setTimeout(() => {
      fetch(`/api/v1/search/?q=${encodeURIComponent(query)}`)
        .then(response => {
          if (!response.ok) throw new Error('Search failed');
          return response.json();
        })
        .then(data => {
          searchResults.innerHTML = '';

          if (data.length === 0) {
            searchResults.innerHTML = `
              <div style="padding: 16px; text-align: center; color: var(--color-muted);">
                No products found for "${query}"
              </div>
            `;
            searchResults.style.display = 'block';
            return;
          }

          data.forEach(product => {
            const link = document.createElement('a');
            // Reconstruct URL based on Django pattern
            link.href = `/products/${product.slug}/`;
            link.style.textDecoration = 'none';
            
            link.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div class="search-result-name">${product.name}</div>
                  <div class="search-result-meta">${product.category} | SKU: ${product.sku}</div>
                </div>
                <div style="font-weight: bold; color: var(--color-primary); font-family: var(--font-accent);">${product.price_label}</div>
              </div>
            `;
            searchResults.appendChild(link);
          });

          searchResults.style.display = 'block';
        })
        .catch(err => {
          console.error('Search error:', err);
        });
    }, 300);
  });

  // Hide results when clicking outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
      searchResults.style.display = 'none';
    }
  });

  // Re-show results on focus if there's a query
  searchInput.addEventListener('focus', () => {
    if (searchInput.value.trim().length >= 2 && searchResults.innerHTML !== '') {
      searchResults.style.display = 'block';
    }
  });
});
