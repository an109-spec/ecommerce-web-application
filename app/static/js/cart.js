document.addEventListener('DOMContentLoaded', () => {
  const cartPage = document.querySelector('[data-cart-page]');
  if (!cartPage) return;

  const modal = document.getElementById('edit-cart-modal');
  const modalContent = document.getElementById('edit-cart-modal-content');

  const formatMoney = (value) => `₫${Number(value || 0).toLocaleString('vi-VN')}`;

  const closeModal = () => {
    if (!modal) return;
    modal.hidden = true;
    modalContent.innerHTML = '';
  };

  const renderOptionButtons = (title, type, options, selectedValue) => `
    <div class="edit-cart-group">
      <span>${title}</span>
      <div class="edit-cart-group__options">
        ${(options || []).map((value) => `
          <button
            type="button"
            class="edit-cart-option ${value === selectedValue ? 'is-active' : ''}"
            data-option-type="${type}"
            data-option-value="${value}">
            ${value}
          </button>
        `).join('') || '<small>Đang cập nhật</small>'}
      </div>
    </div>
  `;

  async function openEditModal(variantId) {
    const response = await fetch(`/cart/item/${variantId}`, {
      headers: { Accept: 'application/json' },
    });
    const payload = await response.json();

    if (!response.ok) {
      alert(payload.error || 'Không thể tải dữ liệu sản phẩm');
      return;
    }

    modalContent.innerHTML = `
      <form id="edit-cart-form" data-variant-id="${payload.variant_id}">
        <div class="edit-cart-layout">
          <img src="${payload.product_image}" alt="${payload.product_name}" class="edit-cart-image">
          <div>
            <h2 id="edit-cart-title">${payload.product_name}</h2>
            ${renderOptionButtons('Size', 'size', payload.size_options, payload.selected?.size)}
            ${renderOptionButtons('Color', 'color', payload.color_options, payload.selected?.color)}
            <div class="edit-cart-grid">
              <div><span>Giá</span><strong>${formatMoney(payload.variant_price)}</strong></div>
              <div><span>Kho</span><strong>${payload.variant_stock}</strong></div>
              <div><span>Giá gốc</span><strong>${formatMoney(payload.original_price)}</strong></div>
              <div><span>Flash Sale 🔥</span><strong>${payload.flash_price != null ? formatMoney(payload.flash_price) : '-'}</strong></div>
              <div><span>Promotion</span><strong>-${formatMoney(payload.promotion_discount)}</strong></div>
            </div>
            <div class="edit-cart-quantity">
              <span>Số lượng</span>
              <button type="button" data-qty-action="minus">-</button>
              <input type="number" name="quantity" value="${payload.quantity}" min="1" max="${payload.variant_stock}">
              <button type="button" data-qty-action="plus">+</button>
            </div>
            <div class="edit-cart-actions">
              <button type="submit" class="btn btn--primary">Save</button>
              <button type="button" class="btn btn--outline" data-close-modal>Cancel</button>
            </div>
          </div>
        </div>
      </form>
    `;

    modal.hidden = false;

    const form = document.getElementById('edit-cart-form');
    const quantityInput = form.querySelector('input[name="quantity"]');
    const selected = {
      size: payload.selected?.size || null,
      color: payload.selected?.color || null,
    };

    form.querySelectorAll('[data-option-type]').forEach((button) => {
      button.addEventListener('click', () => {
        const type = button.dataset.optionType;
        selected[type] = button.dataset.optionValue;
        form.querySelectorAll(`[data-option-type="${type}"]`).forEach((item) => item.classList.remove('is-active'));
        button.classList.add('is-active');
      });
    });

    form.querySelectorAll('[data-qty-action]').forEach((button) => {
      button.addEventListener('click', () => {
        const max = Number(quantityInput.max || payload.variant_stock || 1);
        const current = Number(quantityInput.value || 1);
        quantityInput.value = button.dataset.qtyAction === 'plus'
          ? String(Math.min(max, current + 1))
          : String(Math.max(1, current - 1));
      });
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      const updateResponse = await fetch(`/cart/item/${variantId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          quantity: Number(quantityInput.value || 1),
          size: selected.size,
          color: selected.color,
        }),
      });

      const updatePayload = await updateResponse.json();
      if (!updateResponse.ok) {
        alert(updatePayload.error || 'Không thể cập nhật giỏ hàng');
        return;
      }

      if (window.HeaderMiniCart) {
        await window.HeaderMiniCart.refresh(true);
      }
      window.location.reload();
    });
  }

  document.querySelectorAll('[data-edit-cart-item]').forEach((button) => {
    button.addEventListener('click', () => openEditModal(button.dataset.editCartItem));
  });

  document.querySelectorAll('[data-delete-cart-item]').forEach((button) => {
    button.addEventListener('click', async () => {
      const response = await fetch(`/cart/item/${button.dataset.deleteCartItem}`, {
        method: 'DELETE',
        headers: { Accept: 'application/json' },
      });
      const payload = await response.json();
      if (!response.ok) {
        alert(payload.error || 'Không thể xóa sản phẩm');
        return;
      }
      if (window.HeaderMiniCart) {
        await window.HeaderMiniCart.refresh(true);
      }
      window.location.reload();
    });
  });

  modal?.querySelectorAll('[data-close-modal]').forEach((button) => {
    button.addEventListener('click', closeModal);
  });

  modal?.addEventListener('click', (event) => {
    if (event.target.matches('[data-close-modal]')) {
      closeModal();
    }
  });
  
});