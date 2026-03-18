document.addEventListener('DOMContentLoaded', function () {
  const root = document.getElementById('product-detail-page');
  if (!root) return;

  const productId = root.dataset.productId;
  const endpointBase = '/products';
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
  function normalizeAssetUrl(src, fallback = '/static/images/no-image.png') {
    if (!src) return fallback;
    if (src.startsWith('http://') || src.startsWith('https://')) return src;
    if (src.startsWith('/')) return src;
    if (src.startsWith('static/')) return `/${src}`;
    return `/static/${src}`;
  }

function renderOptionGroup(title, values, type) {
  const items = (values || []).map((value) => `
    <button 
      type="button" 
      class="variant-chip" 
      data-type="${type}" 
      data-value="${value}">
      ${value}
    </button>
  `).join('');

  return `
    <div class="product-option-row">
      <span>${title}:</span>
      <div class="variant-chip-group">
        ${items || '<small>Đang cập nhật</small>'}
      </div>
    </div>
  `;
}
  function calcDiscountPercent(originalPrice, flashPrice, reportedPercent) {
    const reported = Number(reportedPercent || 0);
    if (reported > 0) return reported;

    const original = Number(originalPrice || 0);
    const flash = Number(flashPrice || 0);
    if (original <= 0 || flash <= 0 || flash >= original) return 0;

    return Math.round(((original - flash) / original) * 100);
  }


  function renderProduct(item) {
    const shop = item.shop || {};
    const images = (item.images && item.images.length ? item.images : [item.thumbnail || ''])
      .filter(Boolean)
      .map((src) => normalizeAssetUrl(src));
    const mainImage = images[0] || '/static/images/no-image.png';
    const hasFlashSale = item.flash_price != null;
    const currentPrice = hasFlashSale ? item.flash_price : item.original_price;
    const discountPercent = calcDiscountPercent(item.original_price, item.flash_price, item.discount_percent);
    const shopLogo = normalizeAssetUrl(shop.logo);

     detailEl.innerHTML= `
      <article class="product-detail">
        <div class="product-hero-grid">
          <div class="product-media">
            <img src="${mainImage}" alt="${item.name}" class="product-main-image" onerror="this.onerror=null;this.src='/static/images/no-image.png';">
            <div class="product-thumbnails">
              ${images.map((src) => `<img src="${src}" data-src="${src}" class="thumb-img" alt="${item.name}" onerror="this.onerror=null;this.src='/static/images/no-image.png';">`).join('')}
            </div>
          </div>
          <div class="product-info">
            <h2>${item.name}</h2>
            <p class="product-rating">${toStars(item.rating)} • ${item.reviews_count || 0} đánh giá</p>
            <div class="price-block">

  ${hasFlashSale ? `
    <div class="flash-sale-bar">
      ⚡ FLASH SALE 
      <span id="product-flash-countdown" data-ends-at="${item.flash_sale_ends_at || ''}">
        --:--:--
      </span>
    </div>
  ` : ''}

  <div class="price-main">
    <span class="price-current" id="product-price">${fmtCurrency(currentPrice)}</span>
    
    ${discountPercent > 0 ? `
      <span class="price-original">${fmtCurrency(item.original_price)}</span>
      <span class="price-percent">-${discountPercent}%</span>
    ` : ''}
  </div>

</div>

${item.promotions && item.promotions.length ? `
  <div class="promotion-block">
    🎉 Khuyến mãi:
    ${item.promotions.map(p => `<span class="promo-chip">${p.description || 'Ưu đãi'}</span>`).join('')}
  </div>
` : ''}

${item.vouchers && item.vouchers.length ? `
  <div class="voucher-block">
    🎟️ Mã giảm giá:
    ${item.vouchers.map(v => `<span class="voucher-chip">${v.code || 'Voucher'}</span>`).join('')}
  </div>
` : ''}
            ${renderOptionGroup('Size', item.size_options, 'size')}
            ${renderOptionGroup('Color', item.color_options, 'color')}
            <div class="quantity-picker">
              <span>Số lượng</span>
              <button type="button" id="qty-minus">-</button>
              <input type="number" id="detail-quantity" min="1" max="${item.stock || 1}" value="1">
              <button type="button" id="qty-plus">+</button>
              <span class="stock-text">Kho: ${item.stock || 0}</span>
            </div>
            <div class="product-actions">
              <form id="add-to-cart-form">
                <input type="hidden" name="product_id" value="${item.id}">
                <input type="hidden" name="quantity" id="add-to-cart-qty" value="1">
                <button type="submit" class="btn btn--outline">Thêm vào giỏ hàng</button>
              </form>
              <button type="button" class="btn btn--primary" id="buy-now-btn">Mua ngay</button>
            </div>
          </div>
        </div>
      </article>

      <section class="shop-info-block">
        <h3>Thông tin shop</h3>
        <div class="shop-info-grid">
          <img src="${shopLogo}" alt="${shop.name || 'Shop'}" onerror="this.onerror=null;this.src='/static/images/no-image.png';">
              <div class="shop-info-content">
                <p class="shop-name">${shop.name || 'OneShop'}</p>

                <div class="shop-stats">
                  <div><span>Đánh giá</span><b>${Number(shop.rating || 0).toFixed(1)}</b></div>
                  <div><span>Sản phẩm</span><b>${shop.total_products || 0}</b></div>
                  <div><span>Follower</span><b>${shop.followers || 0}</b></div>
                </div>
      <a class="btn btn--outline shop-btn" href="${shop.url || '/shop'}">Xem shop</a>
    </div>
        </div>
      </section>

    <section class="product-meta-block">
      <h3>Chi tiết sản phẩm</h3>

      <div class="meta-table">
        <div class="meta-row">
          <span>Danh mục</span>
          <div>${(item.categories || []).join(', ') || 'Đang cập nhật'}</div>
        </div>

        <div class="meta-row">
          <span>Kho</span>
          <div>${item.stock || 0}</div>
        </div>
      </div>
    </section>

      <section class="product-description-block">
        <h3>Mô tả sản phẩm</h3>
        <div class="product-description">
          ${(item.description || 'Chưa có mô tả')
            .replace(/\n/g, '<br>')
          }
        </div>
      </section>
    `;
    let selected = {
  size: null,
  color: null
};

const priceEl = detailEl.querySelector('#product-price');
const mainImageEl = detailEl.querySelector('.product-main-image');

// CLICK SIZE / COLOR
detailEl.querySelectorAll('.variant-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    const type = btn.dataset.type;
    const value = btn.dataset.value;

    // set active UI
    detailEl.querySelectorAll(`.variant-chip[data-type="${type}"]`)
      .forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // lưu lựa chọn
    selected[type] = value;

    updateVariant();
  });
});

// CLICK ẢNH NHỎ
detailEl.querySelectorAll('.thumb-img').forEach(img => {
  img.addEventListener('click', () => {
    mainImageEl.src = img.dataset.src;

    detailEl.querySelectorAll('.thumb-img')
      .forEach(i => i.classList.remove('active'));
    img.classList.add('active');
  });
});


// 🔥 CORE LOGIC
function updateVariant() {
  if (!item.variants) return;

  const match = item.variants.find(v => {
    return (!selected.size || v.size == selected.size) &&
          (!selected.color || (v.color || '').toLowerCase() === selected.color.toLowerCase());
  });

  if (!match) return;

  // ✅ ĐỔI GIÁ
  if (priceEl && match.price) {
    priceEl.textContent = fmtCurrency(match.price);
  }

  // ✅ luôn tìm riêng theo color để đổi ảnh
  if (selected.color && item.variants && mainImageEl) {
    const colorVariant = item.variants.find(v =>
  (v.color || '').toLowerCase() === selected.color.toLowerCase()
  && v.image
);

    if (colorVariant && colorVariant.image) {
      mainImageEl.src = normalizeAssetUrl(colorVariant.image);
    }
  }
}
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

        const addToCartForm = detailEl.querySelector('#add-to-cart-form');
    const buyNowBtn = detailEl.querySelector('#buy-now-btn');

    const selectedVariant = () => {
      if (!item.variants || !item.variants.length) return null;
      return item.variants.find((variant) => {
        const sizeOk = !selected.size || variant.size === selected.size;
        const colorOk = !selected.color || (variant.color || '').toLowerCase() === (selected.color || '').toLowerCase();
        return sizeOk && colorOk;
      }) || item.variants[0];
    };

    const submitCartAction = async (redirectToCart = false) => {
      const requiresSize = Array.isArray(item.size_options) && item.size_options.length > 0;
      const requiresColor = Array.isArray(item.color_options) && item.color_options.length > 0;
      if ((requiresSize && !selected.size) || (requiresColor && !selected.color)) {
        alert('Vui lòng chọn đầy đủ phân loại sản phẩm');
        return;
      }

      const variant = selectedVariant();
      if (!variant) {
        alert('Vui lòng chọn phân loại sản phẩm');
        return;
      }

      const response = await fetch('/cart/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          product_id: item.id,
          variant_id: variant.id,
          size: selected.size,
          color: selected.color,
          quantity: Number(hiddenQty?.value || 1),
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        alert(payload.error || 'Không thể thêm vào giỏ hàng');
        return;
      }

      if (window.HeaderMiniCart) {
        await window.HeaderMiniCart.refresh(true);
      }

      if (redirectToCart) {
        window.location.href = '/cart';
        return;
      }

      alert(`Đã thêm vào giỏ. Tổng số lượng hiện tại: ${payload.cart_item_count}`);
    };

    addToCartForm?.addEventListener('submit', async (event) => {
      event.preventDefault();
      await submitCartAction(false);
    });

    buyNowBtn?.addEventListener('click', async () => {
      await submitCartAction(true);
    });


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
    const img = normalizeAssetUrl(item.image || item.thumbnail);

    return `
      <a class="product-card" href="/shop/${item.id}">
        <div class="product-card__image-wrap">
          <img src="${img}" alt="${item.name}" onerror="this.onerror=null;this.src='/static/images/no-image.png';">
        </div>
        <h4 class="product-card__title">${item.name}</h4>
        <div class="product-card__meta">
          <span class="rating">
            ${toStars(item.rating)} (${item.reviews_count || 0})
          </span>
          <span class="sold">
            Đã bán ${item.sold || 0}
          </span>
        </div>
        <p class="product-card__price">${fmtCurrency(item.price)}</p>
      </a>
    `;
  }).join('');
}

  function renderReviews(items) {
    if (!window.ProductReview) {
    reviewEl.innerHTML = '<p>Lỗi load review component</p>';
    return;
  }

  reviewEl.innerHTML =
    (items || []).map((r) => window.ProductReview.renderItem(r)).join('')
    || '<p>Chưa có đánh giá.</p>';
}

  async function loadAll() {
    const [productRes, relatedRes, reviewsRes] = await Promise.all([
      fetch(`${endpointBase}/${productId}`),
      fetch(`${endpointBase}/${productId}/related`),
      fetch(`${endpointBase}/${productId}/reviews`)
    ]);

    const productData = await productRes.json();
    console.log("PRODUCT DATA:", productData);
    const relatedData = await relatedRes.json();
    const reviewData = await reviewsRes.json();

    // ❗ CHECK API ERROR
    if (!productRes.ok || productData.error) {
      detailEl.innerHTML = `<p>Lỗi: ${productData.error || 'Không tải được sản phẩm'}</p>`;
      return;
    }

    renderProduct(productData);
    renderRelated(relatedData.items || []);
    renderReviews(reviewData.items || []);
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

});