(function () {
    const resultEl = document.getElementById('search-result');
    const suggestEl = document.getElementById('suggested-result');
    const searchInput = document.getElementById('internal-search-input');
    const searchBtn = document.getElementById('internal-search-btn');

    if (!resultEl) return;

    // Hàm tạo HTML cho 1 sản phẩm (nhìn chuyên nghiệp hơn)
    function createProductHTML(item) {
        return `
            <div class="product-card">
                <div style="width: 100%; height: 230px; background: #f9f9f9; overflow: hidden;">
                    <img src="${item.thumbnail || '/static/images/no-image.png'}" 
                         style="width: 100%; height: 100%; object-fit: cover;" alt="${item.name}">
                </div>
                <div style="padding: 15px; flex: 1; display: flex; flex-direction: column;">
                    <h4 style="font-size: 0.95rem; color: #333; margin-bottom: 10px; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                        ${item.name}
                    </h4>
                    <p style="color: #ff4d4f; font-size: 1.1rem; font-weight: bold; margin-bottom: 15px;">
                        ${new Intl.NumberFormat('vi-VN').format(item.price)} ₫
                    </p>
                    <a href="/shop/${item.id}" style="margin-top: auto; text-align: center; padding: 8px; border: 1px solid #ff4d4f; color: #ff4d4f; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: bold; transition: all 0.3s;">
                        XEM CHI TIẾT
                    </a>
                </div>
            </div>
        `;
    }

    // Hàm thực hiện tìm kiếm chính
    async function loadResults() {
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q') || '';
        // Cập nhật giá trị vào ô input nếu có q từ URL
        if (urlParams.has('q')) searchInput.value = urlParams.get('q');

        resultEl.innerHTML = '<p>Đang tìm kiếm sản phẩm...</p>';

        try {
            const res = await fetch(`/products?${urlParams.toString()}`);
            const data = await res.json();

            if (data.items && data.items.length > 0) {
                resultEl.innerHTML = data.items.map(item => createProductHTML(item)).join('');
            } else {
                resultEl.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 20px;">Không tìm thấy sản phẩm nào phù hợp.</p>';
            }
        } catch (e) {
            resultEl.innerHTML = '<p>Lỗi khi tải dữ liệu.</p>';
        }
    }
  async function loadSuggestions() {
      try {
          // Sửa per_page từ 4 thành 20 hoặc số lượng bạn muốn
          // Bỏ bớt các filter để nó hiện sản phẩm ngẫu nhiên hoặc mới nhất trên toàn hệ thống
          const res = await fetch('/products?per_page=20&sort=newest'); 
          const data = await res.json();
          
          if (data.items && data.items.length > 0) {
              suggestEl.innerHTML = data.items.map(item => createProductHTML(item)).join('');
          } else {
              suggestEl.innerHTML = '<p>Hiện chưa có sản phẩm gợi ý nào.</p>';
          }
      } catch (e) {
          console.error("Lỗi tải gợi ý:", e);
      }
  }

    // Xử lý khi nhấn nút Tìm kiếm trên trang
  function handleSearch() {
      const val = document.getElementById('internal-search-input').value.trim();
      if (!val) return;

      const currentUrl = new URL(window.location.href);
      // Xóa các tham số tìm kiếm cũ để tránh bị loạn
      currentUrl.searchParams.delete('q');
      currentUrl.searchParams.delete('keyword');
      
      // Gán giá trị mới (Gửi cả q và keyword để Backend kiểu gì cũng nhận được)
      currentUrl.searchParams.set('q', val); 
      currentUrl.searchParams.set('keyword', val);
      
      window.location.href = currentUrl.toString();
  }

    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });


    const urlParams = new URLSearchParams(window.location.search);
    const hasSearch = urlParams.has('q') || urlParams.get('keyword');

    loadSuggestions();

        // Nếu có từ khóa search thì mới load kết quả tìm kiếm
        if (hasSearch) {
            loadResults();
        }
})();