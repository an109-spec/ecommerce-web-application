(function () {
  const root = document.getElementById('product-detail-page');
  if (!root) return;

  const productId = root.dataset.productId;
  const endpointBase = root.dataset.endpointBase || '/products';
  const detailEl = document.getElementById('product-detail');
  const relatedEl = document.getElementById('related-products');
  const reviewEl = document.getElementById('review-list');
  const reviewForm = document.getElementById('review-form');

  function fmtCurrency(value) {
    const amount = Number(value || 0);
    return `₫${amount.toLocaleString('vi-VN')}`;
  }

  function toStars(rating) {
    const rounded = Math.round(Number(rating || 0));
    return '★'.repeat(Math.max(0, rounded)) + '☆'.repeat(Math.max(0, 5 - rounded));
  }

  function renderOptionGroup(title, values) {
    const items = (values || []).map((value) => `<button type="button" class="variant-chip">${value}</button>`).join('');
    return `<div class="product-option-row"><span>${title}:</span><div class="variant-chip-group">${items || '<small>Đang cập nhật</small>'}</div></div>`;
  }


  function renderProduct(item) {
    const shop = item.shop || {};
    const images = (item.images && item.images.length
  ? item.images
  : [item.thumbnail || '']
)
.filter(Boolean)
.map(src => src.startsWith('http') ? src : `/${src}`);
    const mainImage = images[0] || '/static/images/no-image.png';
    const currentPrice = item.flash_price != null ? item.flash_price : item.original_price;
    const shopLogo = shop.logo
  ? (shop.logo.startsWith('http') ? shop.logo : `/static/${shop.logo}`)
  : '/static/images/no-image.png'

    detailEl.innerHTML = `
      <article class="product-detail">
        <div class="product-hero-grid">
          <div class="product-media">
            <img src="${mainImage}" alt="${item.name}" class="product-main-image">
            <div class="product-thumbnails">
              ${images.map((src) => `<img src="${src}" alt="${item.name}">`).join('')}
            </div>
          </div>
          <div class="product-info">
            <h2>${item.name}</h2>
            <p class="product-rating">${toStars(item.rating)} • ${item.reviews_count || 0} đánh giá</p>
            <p class="product-original-price">Giá gốc: ${fmtCurrency(item.original_price)}</p>
            <p class="product-sale-price">Flash Sale: ${fmtCurrency(currentPrice)}</p>
            <p class="product-discount">Giảm: ${item.discount_percent || 0}%</p>
            <p class="product-countdown">Flash Sale kết thúc: <span id="product-flash-countdown" data-ends-at="${item.flash_sale_ends_at || ''}">--:--:--</span></p>
            ${renderOptionGroup('Size', item.size_options)}
            ${renderOptionGroup('Color', item.color_options)}
            <div class="quantity-picker">
              <span>Số lượng</span>
              <button type="button" id="qty-minus">-</button>
              <input type="number" id="detail-quantity" min="1" max="${item.stock || 1}" value="1">
              <button type="button" id="qty-plus">+</button>
              <small>Tồn kho: ${item.stock || 0}</small>
            </div>
            <div class="product-actions">
              <form action="/cart/add" method="post">
                <input type="hidden" name="product_id" value="${item.id}">
                <input type="hidden" name="quantity" id="add-to-cart-qty" value="1">
                <button type="submit" class="btn btn--outline">Thêm vào giỏ hàng</button>
              </form>
              <a class="btn btn--primary" href="/cart">Mua ngay</a>
            </div>
          </div>
        </div>
      </article>

      <section class="shop-info-block">
        <h3>Thông tin shop</h3>
        <div class="shop-info-grid">
          <img src="${shopLogo}" alt="${shop.name || 'Shop'}">
          <div>
            <p><strong>${shop.name || 'OneShop'}</strong></p>
            <p>Đánh giá shop: ${Number(shop.rating || 0).toFixed(1)}</p>
            <p>Tổng số sản phẩm: ${shop.total_products || 0}</p>
            <p>Người theo dõi: ${shop.followers || 0}</p>
            <a class="btn btn--outline" href="${shop.url || '/shop'}">Xem shop</a>
          </div>
        </div>
      </section>

      <section class="product-meta-block">
        <h3>Chi tiết sản phẩm</h3>
        <p>Danh mục: ${item.category || 'Đang cập nhật'}</p>
        <p>Tồn kho: ${item.stock || 0}</p>
      </section>
    `;

    const quantityInput = detailEl.querySelector('#detail-quantity');
    const qtyMinus = detailEl.querySelector('#qty-minus');
    const qtyPlus = detailEl.querySelector('#qty-plus');
    const hiddenQty = detailEl.querySelector('#add-to-cart-qty');

    const syncQty = () => {
      if (!quantityInput) return;
      const val = Math.max(1, Number(quantityInput.value || 1));
      quantityInput.value = String(val);
      if (hiddenQty) hiddenQty.value = String(val);
    };

    qtyMinus?.addEventListener('click', () => {
      quantityInput.value = String(Math.max(1, Number(quantityInput.value || 1) - 1));
      syncQty();
    });

    qtyPlus?.addEventListener('click', () => {
      const max = Number(quantityInput.max || 1);
      quantityInput.value = String(Math.min(max, Number(quantityInput.value || 1) + 1));
      syncQty();
    });

    quantityInput?.addEventListener('change', syncQty);
    syncQty();

    const countdownEl = detailEl.querySelector('#product-flash-countdown');
    if (countdownEl && countdownEl.dataset.endsAt) {
      const timer = () => {
        const diff = new Date(countdownEl.dataset.endsAt).getTime() - Date.now();
        if (diff <= 0) {
          countdownEl.textContent = 'Đã kết thúc';
          return;
        }

        const sec = Math.floor(diff / 1000) % 60;
        const min = Math.floor(diff / (1000 * 60)) % 60;
        const hour = Math.floor(diff / (1000 * 60 * 60));
        countdownEl.textContent = [hour, min, sec].map((v) => String(v).padStart(2, '0')).join(':');
        setTimeout(timer, 1000);
      };
      timer();
    }
  }

function renderRelated(items) {
  relatedEl.innerHTML = (items || []).map((item) => {
    const img = item.image
      ? (item.image.startsWith('http') ? item.image : `/static/${item.image}`)
      : '/static/images/no-image.png';

    return `
      <a class="product-card" href="/shop/${item.id}">
        <div class="product-card__image-wrap">
          <img src="${img}" alt="${item.name}">
        </div>
        <h4>${item.name}</h4>
        <p>${fmtCurrency(item.price)}</p>
      </a>
    `;
  }).join('');
}

  function renderReviews(items) {
    reviewEl.innerHTML = (items || []).map((r) => window.ProductReview.renderItem(r)).join('') || '<p>Chưa có đánh giá.</p>';
  }

  async function loadAll() {
    const [productRes, relatedRes, reviewsRes] = await Promise.all([
      fetch(`${endpointBase}/${productId}`),
      fetch(`${endpointBase}/${productId}/related`),
      fetch(`${endpointBase}/${productId}/reviews`)
    ]);

    renderProduct(await productRes.json());
    renderRelated((await relatedRes.json()).items || []);
    renderReviews((await reviewsRes.json()).items || []);
    if (window.ProductQR) window.ProductQR.bind(productId);
  }

  reviewForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(reviewForm);
    const payload = {
      user_id: Number(fd.get('user_id')),
      rating: Number(fd.get('rating')),
      comment: fd.get('comment')
    };

    await fetch(`${endpointBase}/${productId}/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const refreshed = await fetch(`${endpointBase}/${productId}/reviews`);
    renderReviews((await refreshed.json()).items || []);
    reviewForm.reset();
  });

  loadAll();
})();