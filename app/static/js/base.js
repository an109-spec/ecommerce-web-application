document.addEventListener('DOMContentLoaded', () => {
  console.log('Shopee Mini UI Loaded');

  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = '0.5s';
      setTimeout(() => alert.remove(), 500);
    }, 3000);
  });

  const input = document.getElementById('searchInput');
  const suggest = document.getElementById('searchSuggest');
  if (input && suggest) {
    input.addEventListener('focus', () => {
      suggest.style.display = 'block';
    });
    input.addEventListener('blur', () => {
      setTimeout(() => {
        suggest.style.display = 'none';
      }, 200);
    });
  }

  const cartTrigger = document.querySelector('[data-cart-trigger]');
  const miniCart = document.querySelector('[data-mini-cart]');
  const badge = document.querySelector('[data-cart-badge]');
  const miniCartList = document.querySelector('[data-mini-cart-items]');
  const miniCartSubtotal = document.querySelector('[data-mini-cart-subtotal]');
  const badgeInline = document.querySelector('[data-cart-badge-inline]');

  const formatMoney = (value) => `₫${Number(value || 0).toLocaleString('vi-VN')}`;

  const renderMiniCart = (payload) => {
    if (!badge) return;

    const count = Number(payload.cart_item_count || 0);
    badge.textContent = count;
    badge.hidden = count <= 0;
    if (badgeInline) badgeInline.textContent = count;

    if (miniCartList) {
      miniCartList.innerHTML = (payload.items || []).map((item) => `
        <article class="mini-cart__item">
          <img src="${item.product_image}" alt="${item.product_name}" onerror="this.onerror=null;this.src='/static/images/no-image.png';">
          <div>
            <h4>${item.product_name}</h4>
            <p>${formatMoney(item.price)} × ${item.quantity}</p>
          </div>
        </article>
      `).join('') || '<p class="mini-cart__empty">Giỏ hàng đang trống.</p>';
    }

    if (miniCartSubtotal) {
      miniCartSubtotal.textContent = formatMoney(payload.cart_subtotal);
    }
  };

  const refreshMiniCart = async (openAfterRefresh = false) => {
    const response = await fetch('/cart/mini', { headers: { Accept: 'application/json' } });
    const payload = await response.json();
    renderMiniCart(payload);
    if (openAfterRefresh && miniCart) {
      miniCart.hidden = false;
    }
    return payload;
  };

  if (cartTrigger && miniCart) {
    cartTrigger.addEventListener('click', async (event) => {
      event.preventDefault();
      const isHidden = miniCart.hidden;
      if (isHidden) {
        await refreshMiniCart(true);
      } else {
        miniCart.hidden = true;
      }
    });

    document.addEventListener('click', (event) => {
      const withinCart = event.target.closest('[data-cart-shell]');
      if (!withinCart && !miniCart.hidden) {
        miniCart.hidden = true;
      }
    });
  }

  refreshMiniCart().catch((error) => console.error('Failed to load mini cart', error));

  window.HeaderMiniCart = {
    refresh: refreshMiniCart,
    render: renderMiniCart,
  };

});

