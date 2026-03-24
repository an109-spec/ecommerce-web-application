(function () {
  const root = document.getElementById('shop-public-page');
  if (!root) return;

  const shopId = root.dataset.shopId;
  const summaryEndpoint = `/shops/${shopId}/summary`;
  const productsEndpoint = `/shops/${shopId}/products`;
  const followEndpoint = `/shops/${shopId}/follow`;

  const state = {
    currentFilter: 'all',
    currentSort: 'popular',
    currentPage: 1,
    limit: 9,
    isFollowing: false,
    canFollow: true,
  };

  const els = {
    shopName: document.getElementById('shop-name'),
    shopBreadcrumbName: document.getElementById('shop-breadcrumb-name'),
    shopLogo: document.getElementById('shop-logo'),
    shopRating: document.getElementById('shop-rating'),
    shopFollowers: document.getElementById('shop-followers'),
    shopProducts: document.getElementById('shop-products'),
    shopDescription: document.getElementById('shop-description'),
    followBtn: document.getElementById('follow-btn'),
    grid: document.getElementById('shop-product-grid'),
    pagination: document.getElementById('shop-pagination'),
    sortSelect: document.getElementById('shop-sort-select'),
    menu: document.getElementById('shop-menu'),
  };

  function formatCurrency(value) {
    return `₫${Number(value || 0).toLocaleString('vi-VN')}`;
  }

  function stars(rating) {
    const rounded = Math.round(Number(rating || 0));
    return '★'.repeat(Math.max(0, rounded)) + '☆'.repeat(Math.max(0, 5 - rounded));
  }

  function updateFollowButton() {
    const textEl = els.followBtn?.querySelector('.follow-btn__text');
    const iconEl = els.followBtn?.querySelector('.follow-btn__icon');
    if (!els.followBtn || !textEl || !iconEl) return;

    els.followBtn.dataset.following = String(state.isFollowing);
    els.followBtn.classList.toggle('is-following', state.isFollowing);
    els.followBtn.disabled = !state.canFollow;

    if (!state.canFollow) {
      textEl.textContent = 'Shop của bạn';
      iconEl.textContent = '🏪';
      return;
    }

    textEl.textContent = state.isFollowing ? 'Đang theo dõi' : '+ Theo dõi shop';
    iconEl.textContent = state.isFollowing ? '❤️' : '🤍';
  }

  function renderSummary(data) {
    state.isFollowing = !!data.is_following;
    state.canFollow = data.can_follow !== false;
    els.shopName.textContent = data.name || 'Tên shop';
    els.shopBreadcrumbName.textContent = data.name || 'Tên shop';
    els.shopLogo.src = data.logo || '/static/images/no-image.png';
    els.shopRating.textContent = Number(data.rating || 0).toFixed(1);
    els.shopFollowers.textContent = data.followers_count || 0;
    if (data.owner_id) {
      els.shopFollowers.style.cursor = 'pointer';
      els.shopFollowers.title = 'Xem trang người mua';
      els.shopFollowers.onclick = () => {
        window.location.href = `/user/view/${data.owner_id}`;
      };
    }
    els.shopProducts.textContent = data.total_products || 0;
    els.shopDescription.textContent = data.description || 'Shop chưa cập nhật mô tả.';
    updateFollowButton();
  }

  function renderProducts(items) {
    els.grid.innerHTML = (items || []).map((item) => `
      <a class="product-card" href="${item.product_url}">
        <div class="product-card__image-wrap">
          <img class="product-card__thumb" src="${item.thumbnail}" alt="${item.name}" onerror="this.onerror=null;this.src='/static/images/no-image.png';">
        </div>
        <h3 class="product-card__name">${item.name}</h3>
        <div class="shop-product-card__rating">${stars(item.rating)} <span>${Number(item.rating || 0).toFixed(1)}</span></div>
        <p class="product-card__price">${formatCurrency(item.price)}</p>
        <p class="shop-product-card__sold">Đã bán ${item.sold || 0}</p>
      </a>
    `).join('') || '<p class="shop-empty-state">Shop chưa có sản phẩm phù hợp.</p>';
  }

  function renderPagination(totalPages) {
    const pageCount = Math.max(1, Number(totalPages || 1));
    const buttons = [];
    buttons.push(`<button type="button" data-page="${Math.max(1, state.currentPage - 1)}" ${state.currentPage <= 1 ? 'disabled' : ''}>&lt;</button>`);

    for (let page = 1; page <= pageCount; page += 1) {
      buttons.push(`<button type="button" data-page="${page}" class="${page === state.currentPage ? 'active' : ''}">${page}</button>`);
    }

    buttons.push(`<button type="button" data-page="${Math.min(pageCount, state.currentPage + 1)}" ${state.currentPage >= pageCount ? 'disabled' : ''}>&gt;</button>`);
    els.pagination.innerHTML = buttons.join('');
  }

  async function loadProducts() {
    const params = new URLSearchParams({
      filter: state.currentFilter,
      sort: state.currentSort,
      page: state.currentPage,
      limit: state.limit,
    });

    const res = await fetch(`${productsEndpoint}?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) {
      els.grid.innerHTML = `<p class="shop-empty-state">${data.error || 'Không tải được sản phẩm.'}</p>`;
      els.pagination.innerHTML = '';
      return;
    }

    renderProducts(data.items || []);
    renderPagination(data.total_pages || 1);
  }

  async function loadSummary() {
    const res = await fetch(summaryEndpoint);
    const data = await res.json();
    if (!res.ok) {
      els.shopName.textContent = data.error || 'Không tải được shop';
      updateFollowButton();
      return;
    }

    renderSummary(data);
  }

  async function toggleFollow() {
    if (!state.canFollow) return;

    const method = state.isFollowing ? 'DELETE' : 'POST';
    const res = await fetch(followEndpoint, { method });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || 'Không thể cập nhật theo dõi shop.');
      return;
    }

    state.isFollowing = !!data.is_following;
    els.shopFollowers.textContent = data.followers_count || 0;
    updateFollowButton();
  }

  els.menu?.addEventListener('click', (event) => {
    const btn = event.target.closest('button[data-filter]');
    if (!btn) return;

    state.currentFilter = btn.dataset.filter || 'all';
    state.currentPage = 1;

    els.menu.querySelectorAll('button[data-filter]').forEach((item) => {
      item.classList.toggle('active', item === btn);
    });

    loadProducts();
  });

  els.sortSelect?.addEventListener('change', () => {
    state.currentSort = els.sortSelect.value || 'popular';
    state.currentPage = 1;
    loadProducts();
  });

  els.pagination?.addEventListener('click', (event) => {
    const btn = event.target.closest('button[data-page]');
    if (!btn || btn.disabled) return;
    const nextPage = Number(btn.dataset.page || 1);
    if (nextPage === state.currentPage) return;
    state.currentPage = nextPage;
    loadProducts();
  });

  els.followBtn?.addEventListener('click', toggleFollow);

  updateFollowButton();
  loadSummary();
  loadProducts();
})();