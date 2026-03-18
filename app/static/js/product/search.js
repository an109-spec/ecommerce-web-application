(function () {
  const root = document.getElementById('product-search-page');
  if (!root) return;

  const endpoint = root.dataset.endpointProducts || '/products';
  const keywordInput = document.getElementById('search-keyword');
  const searchBtn = document.getElementById('search-button');
  const resultEl = document.getElementById('search-result');

  async function search() {
    const keyword = (keywordInput.value || '').trim();
    const params = new URLSearchParams({ keyword, page: 1, per_page: 20 });
    const res = await fetch(`${endpoint}?${params.toString()}`);
    const data = await res.json();
    resultEl.innerHTML = (data.items || []).map((item) => `
      <article class="product-card">
        <h4>${item.name}</h4>
        <p>${item.price}</p>
        ${item.shop_id ? `<a class="btn btn--outline" href="/shops/${item.shop_id}">Xem shop ${item.shop_name || ''}</a>` : ''}
      </article>
    `).join('') || '<p>Không tìm thấy sản phẩm</p>';
  }

  searchBtn?.addEventListener('click', search);
})();