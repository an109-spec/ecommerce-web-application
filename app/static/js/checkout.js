document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('[data-checkout-root]');
  const initialNode = document.getElementById('checkout-initial-data');
  const page = document.querySelector('[data-checkout-page]');
  if (!page || !root) return;

  let checkout = null;

  const notify = (message, type = 'info') => {
    if (typeof window.showToast === 'function') {
      window.showToast(message, type);
      return;
    }
    alert(message);
  };


  const formatMoney = (value) => `₫${Number(value || 0).toLocaleString('vi-VN')}`;
  const escapeHtml = (value) => String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || 'Yêu cầu thất bại');
    }
    return payload;
  }

  function addressText(address) {
    if (!address) return 'Chưa có địa chỉ mặc định';
    return [address.address_line, address.ward, address.district, address.city].filter(Boolean).join(', ');
  }

  function renderShop(shop) {
    return `
      <section class="checkout-section checkout-shop-card">
        <div class="checkout-shop-header">
          <div>
            <p class="checkout-muted">Shop</p>
            <h3>${escapeHtml(shop.shop_name)}</h3>
          </div>
          <div class="checkout-muted">Tạm tính shop: <strong>${formatMoney(shop.shop_subtotal)}</strong></div>
        </div>

        <div>
          ${shop.items.map((item) => `
            <article class="checkout-product-item">
              <img class="checkout-product-thumb" src="${escapeHtml(item.product_image)}" alt="${escapeHtml(item.product_name)}">
              <div class="checkout-product-meta">
                <strong>${escapeHtml(item.product_name)}</strong>
                <span class="checkout-product-variant">Phân loại: ${escapeHtml([item.size, item.color].filter(Boolean).join(' / ') || 'Mặc định')}</span>
                <span class="checkout-muted">Đơn giá: ${formatMoney(item.effective_price)} · Số lượng: ${item.quantity}</span>
              </div>
              <div class="checkout-product-price">
                <span>${formatMoney(item.item_total)}</span>
                <small class="checkout-muted">Kho: ${item.stock}</small>
              </div>
            </article>
          `).join('')}
        </div>

        <div class="checkout-summary-card">
          <h4>Voucher của Shop</h4>
          <div class="checkout-voucher-row">
            <div>${shop.voucher ? `${escapeHtml(shop.voucher.voucher_code)} · Giảm ${formatMoney(shop.voucher.voucher_discount)}` : 'Chưa áp dụng voucher'}</div>
            <div class="checkout-inline-form">
              <input type="text" placeholder="Nhập mã voucher" data-voucher-code="${shop.shop_id}">
              <button type="button" class="btn btn--outline" data-apply-voucher-code="${shop.shop_id}">Áp dụng</button>
              <select data-voucher-select="${shop.shop_id}">
                <option value="">Chọn voucher có sẵn</option>
                ${(shop.available_vouchers || []).map((voucher) => `
                  <option value="${voucher.voucher_id}">${escapeHtml(voucher.voucher_code)} - ${voucher.discount_type === 'percent' ? voucher.voucher_discount + '%' : formatMoney(voucher.voucher_discount)}</option>
                `).join('')}
              </select>
            </div>
          </div>
        </div>

        <div class="checkout-summary-card">
          <h4>Phương thức vận chuyển</h4>
          <div class="checkout-shipping-list">
            ${(shop.shipping_methods || []).map((method) => `
              <div class="checkout-shipping-option ${method.selected ? 'is-selected' : ''}">
                <div>
                  <strong>${escapeHtml(method.label)}</strong>
                  <div class="checkout-muted">Phí vận chuyển: ${formatMoney(method.fee)}</div>
                </div>
                <button type="button" class="btn ${method.selected ? 'btn--primary' : 'btn--outline'}" data-shipping-method="${shop.shop_id}" data-shipping-code="${method.code}">${method.selected ? 'Đã chọn' : 'Chọn'}</button>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="checkout-summary-card">
          <h4>Chi tiết Shop</h4>
          <div class="checkout-summary-list">
            <div class="checkout-summary-line"><span>Tổng tiền hàng</span><strong>${formatMoney(shop.shop_subtotal)}</strong></div>
            <div class="checkout-summary-line"><span>Phí vận chuyển</span><strong>${formatMoney(shop.shipping_fee)}</strong></div>
            <div class="checkout-summary-line"><span>Giảm giá voucher</span><strong>- ${formatMoney(shop.shop_voucher_discount)}</strong></div>
            <div class="checkout-summary-line is-total"><span>Tổng shop</span><strong>${formatMoney(shop.shop_total)}</strong></div>
          </div>
        </div>
      </section>
    `;
  }

  function renderAddressModal(addresses, selectedAddressId) {
    return `
      <div class="checkout-address-modal" id="checkout-address-modal" hidden>
        <div class="checkout-address-modal__backdrop" data-close-address-modal></div>
        <div class="checkout-address-modal__dialog">
          <div class="checkout-shop-header">
            <h3>Địa chỉ nhận hàng</h3>
            <button type="button" class="btn btn--outline" data-close-address-modal>Đóng</button>
          </div>
          <div class="checkout-address-list">
            ${(addresses || []).map((address) => `
              <div class="checkout-address-option ${selectedAddressId === address.id ? 'is-selected' : ''}">
                <div>
                  <strong>${escapeHtml(address.full_name || 'Người nhận')}</strong> · ${escapeHtml(address.phone || '')}
                  <div class="checkout-muted">${escapeHtml(addressText(address))}</div>
                </div>
                <button type="button" class="btn ${selectedAddressId === address.id ? 'btn--primary' : 'btn--outline'}" data-select-address="${address.id}">${selectedAddressId === address.id ? 'Đang dùng' : 'Chọn'}</button>
              </div>
            `).join('')}
          </div>
          <form class="checkout-address-form" id="checkout-address-form">
            <input name="full_name" placeholder="Tên người nhận" required>
            <input name="phone" placeholder="Số điện thoại" required>
            <input name="city" placeholder="Tỉnh/Thành phố" required>
            <input name="district" placeholder="Quận/Huyện" required>
            <input name="ward" placeholder="Phường/Xã" required>
            <input class="is-full" name="address_line" placeholder="Địa chỉ chi tiết" required>
            <label class="is-full"><input type="checkbox" name="is_default"> Đặt làm mặc định</label>
            <button type="submit" class="btn btn--primary is-full">Lưu địa chỉ</button>
          </form>
        </div>
      </div>
    `;
  }

  function render(data) {
    if (!data || !Array.isArray(data.shops) || !data.shops.length) {
      root.innerHTML = '';
      return;
    }

    root.innerHTML = `
      <section class="checkout-section">
        <h2 class="checkout-section__title">ĐỊA CHỈ NHẬN HÀNG</h2>
        <div class="checkout-address-card">
          <div class="checkout-address-main">
            <div class="checkout-address-meta">
              <div class="checkout-address-name">📍 ${escapeHtml(data.address?.full_name || 'Chưa có người nhận')} | ${escapeHtml(data.address?.phone || '')}</div>
              <div>${escapeHtml(addressText(data.address))}</div>
            </div>
            <div class="checkout-address-actions">
              <button type="button" class="btn btn--outline" id="change-address-btn">Thay đổi</button>
            </div>
          </div>
        </div>
      </section>

      <section class="checkout-section">
        <h2 class="checkout-section__title">SẢN PHẨM</h2>
        ${data.shops.map(renderShop).join('')}
      </section>

      <section class="checkout-section">
        <h2 class="checkout-section__title">PHƯƠNG THỨC THANH TOÁN</h2>
        <div class="checkout-radio-card checkout-payment-list">
          ${(data.payment_methods || []).map((method) => `
            <div class="checkout-payment-option ${data.payment_method === method.code ? 'is-selected' : ''}">
              <div><strong>${escapeHtml(method.label)}</strong></div>
              <label>
                <input type="radio" name="payment_method" value="${method.code}" ${data.payment_method === method.code ? 'checked' : ''}>
              </label>
            </div>
          `).join('')}
        </div>
      </section>

      <section class="checkout-section">
        <h2 class="checkout-section__title">CHI TIẾT THANH TOÁN</h2>
        <div class="checkout-summary-card">
          <div class="checkout-summary-list">
            <div class="checkout-summary-line"><span>Tổng tiền hàng</span><strong>${formatMoney(data.subtotal)}</strong></div>
            <div class="checkout-summary-line"><span>Phí vận chuyển</span><strong>${formatMoney(data.shipping_total)}</strong></div>
            <div class="checkout-summary-line"><span>Giảm giá</span><strong>- ${formatMoney(data.discount_total)}</strong></div>
            <div class="checkout-summary-line is-total"><span>Tổng thanh toán</span><strong>${formatMoney(data.total)}</strong></div>
          </div>
        </div>
      </section>

      <div class="checkout-total-bar">
        <div class="checkout-total-bar__meta">
          <span class="checkout-muted">Tổng cộng</span>
          <strong>${formatMoney(data.total)}</strong>
        </div>
        <button type="button" class="btn btn--primary" id="place-order-btn">ĐẶT HÀNG</button>
      </div>

      ${renderAddressModal(data.addresses || [], data.address?.id || null)}
    `;

    bindEvents();
  }

  async function refreshCheckout() {
    checkout = await fetchJson('/checkout/data');
    render(checkout);
  }

  function bindEvents() {
    root.querySelector('#place-order-btn')?.addEventListener('click', async () => {
      try {
        const selectedShopId = checkout?.shops?.[0]?.shop_id;
        const selectedAddressId = checkout?.address?.id;
        const selectedPaymentMethod = root.querySelector('input[name="payment_method"]:checked')?.value || checkout?.payment_method;

        if (!selectedShopId) throw new Error('Chưa xác định shop_id');
        if (!selectedAddressId) throw new Error('Chưa có địa chỉ giao hàng');
        if (!selectedPaymentMethod) throw new Error('Chưa chọn phương thức thanh toán');

        const payload = {
          shop_id: Number(selectedShopId),
          address_id: selectedAddressId,
          payment_method: selectedPaymentMethod,
        };

        const result = await fetchJson('/checkout/confirm', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        window.location.href = result.redirect_url;
      } catch (error) {
        notify(error.message || 'Không thể đặt hàng, vui lòng thử lại.', 'error');
      }
    });

    root.querySelectorAll('[data-apply-voucher-code]').forEach((button) => {
      button.addEventListener('click', async () => {
        const shopId = Number(button.dataset.applyVoucherCode);
        const input = root.querySelector(`[data-voucher-code="${shopId}"]`);
        const code = (input?.value || '').trim();

        if (!shopId) {
          notify('Không tìm thấy cửa hàng áp dụng voucher.', 'error');
          return;
        }

        if (!code) {
          notify('Vui lòng nhập mã voucher trước khi áp dụng.', 'warning');
          return;
        }

        try {
          checkout = await fetchJson('/checkout/apply-voucher', {
            method: 'POST',
            body: JSON.stringify({
              shop_id: shopId,
              voucher_code: code,
            }),
          });
          render(checkout);
          notify('Áp dụng voucher thành công.', 'success');
        } catch (_error) {
          notify('Không thể áp dụng voucher. Vui lòng kiểm tra lại mã.', 'error');
        }
      });
    });


    root.querySelectorAll('[data-voucher-select]').forEach((select) => {
      select.addEventListener('change', async () => {
        if (!select.value) return;
        try {
          checkout = await fetchJson('/checkout/apply-voucher', {
            method: 'POST',
            body: JSON.stringify({ shop_id: Number(select.dataset.voucherSelect), voucher_id: Number(select.value) }),
          });
          render(checkout);
          notify('Áp dụng voucher thành công.', 'success');
        } catch (_error) {
          notify('Không thể áp dụng voucher đã chọn.', 'error');
        }
      });
    });

    root.querySelectorAll('[data-shipping-method]').forEach((button) => {
      button.addEventListener('click', async () => {
        const shopId = Number(button.dataset.shippingMethod);
        const shippingCode = button.dataset.shippingCode;
        if (!shopId || !shippingCode) {
          notify('Không thể xác định phương thức vận chuyển.', 'error');
          return;
        }

        try {
          checkout = await fetchJson('/checkout/shipping-method', {
            method: 'POST',
            body: JSON.stringify({ shop_id: shopId, shipping_method: shippingCode }),
          });
          render(checkout);
          notify('Đã cập nhật phương thức vận chuyển.', 'success');
        } catch (_error) {
          notify('Không thể cập nhật phương thức vận chuyển.', 'error');
        }
      });
    });

    root.querySelectorAll('input[name="payment_method"]').forEach((radio) => {
      radio.addEventListener('change', async () => {
        try {
          checkout = await fetchJson('/checkout/payment-method', {
            method: 'POST',
            body: JSON.stringify({ payment_method: radio.value }),
          });
          render(checkout);
        } catch (_error) {
          notify('Không thể cập nhật phương thức thanh toán.', 'error');
        }
      });
    });

    const modal = root.querySelector('#checkout-address-modal');
    root.querySelector('#change-address-btn')?.addEventListener('click', () => {
      if (modal) modal.hidden = false;
    });
    modal?.querySelectorAll('[data-close-address-modal]').forEach((button) => {
      button.addEventListener('click', () => {
        modal.hidden = true;
      });
    });
    modal?.querySelectorAll('[data-select-address]').forEach((button) => {
      button.addEventListener('click', async () => {
        try {
          await fetchJson('/checkout/address', {
            method: 'POST',
            body: JSON.stringify({ address_id: button.dataset.selectAddress }),
          });
          modal.hidden = true;
          await refreshCheckout();
          notify('Đã cập nhật địa chỉ nhận hàng.', 'success');
        } catch (_error) {
          notify('Không thể cập nhật địa chỉ nhận hàng.', 'error');
        }
      });
    });

    modal?.querySelector('#checkout-address-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(event.currentTarget);
      const payload = Object.fromEntries(formData.entries());
      payload.is_default = formData.get('is_default') === 'on';
      try {
        await fetchJson('/user/address', { method: 'PUT', body: JSON.stringify(payload) });
        await refreshCheckout();
        notify('Đã lưu địa chỉ mới.', 'success');
      } catch (_error) {
        notify('Không thể lưu địa chỉ. Vui lòng kiểm tra lại thông tin.', 'error');
      }
    });
  }

  try {
    checkout = JSON.parse(initialNode?.textContent || 'null');
  } catch (_error) {
    checkout = null;
  }

  if (checkout && Array.isArray(checkout.shops) && checkout.shops.length) {
    render(checkout);
  } else {
    fetchJson('/checkout/data')
      .then((payload) => {
        checkout = payload;
        render(checkout);
      })
      .catch(() => {});
  }
});