(function () {
  const root = document.getElementById('product-page');
  if (!root) return;

  const endpoint = root.dataset.endpointProducts || '/products';
  const listEl = document.getElementById('product-list');
  const pageInfo = document.getElementById('page-info');
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const filterForm = document.getElementById('product-filter-form');
  const sortSelect = document.getElementById('sort-select');

  const state = { page: 1, per_page: 10, total: 0 };

function card(item) {
    const freeshipBadge = item.is_freeship 
      ? `<div class="freeship-badge-chay">
          <i class="fas fa-shipping-fast"></i> Freeship
         </div>` 
      : '';

    return `
      <article class="product-card">
        <div class="product-card__img-container">
          ${freeshipBadge}
          <img src="${item.thumbnail || ''}" alt="${item.name}" class="product-card__thumb">
        </div>
        <h4 class="product-card__name">${item.name}</h4>
        <p class="product-card__price">₫${Number(item.price).toLocaleString()}</p>
        <div class="product-card__actions">
            <a class="btn btn--outline" href="/shop/${item.id}">Xem chi tiết</a>
        </div>
      </article>`;
  }

  function render(data) {
    listEl.innerHTML = (data.items || []).map(card).join('') || '<p>Không có dữ liệu</p>';
    state.total = data.total || 0;
    state.page = data.page || 1;
    state.per_page = data.per_page || 10;
    const totalPages = Math.max(1, Math.ceil(state.total / state.per_page));
    pageInfo.textContent = `Trang ${state.page}/${totalPages}`;
    prevBtn.disabled = state.page <= 1;
    nextBtn.disabled = state.page >= totalPages;
  }

  async function load() {
      const params = new URLSearchParams({ page: state.page, per_page: state.per_page });
      
      const urlParams = new URLSearchParams(window.location.search);
      urlParams.forEach((v, k) => params.set(k, v));

      const filter = window.ProductFilter ? window.ProductFilter.read() : {};
      Object.entries(filter).forEach(([k, v]) => params.set(k, v));
      
      if (window.ProductSort) params.set('sort', window.ProductSort.read());

      const res = await fetch(`${endpoint}?${params.toString()}`);
      const data = await res.json();
      render(data);
    }

  filterForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    state.page = 1;
    load();
  });

  sortSelect?.addEventListener('change', () => {
    state.page = 1;
    load();
  });

  prevBtn?.addEventListener('click', () => { if (state.page > 1) { state.page -= 1; load(); } });
  nextBtn?.addEventListener('click', () => { state.page += 1; load(); });

  load();
})();