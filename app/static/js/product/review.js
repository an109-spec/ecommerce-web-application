// C:\DO_AN_TOT_NGHIEP\app\static\js\product\review.js

/**
 * Hàm tạo chuỗi HTML cho sao (Vàng/Xám)
 */
function generateStarsHtml(rating) {
    let starsHtml = '';
    for (let i = 1; i <= 5; i++) {
        // fas = font-awesome solid (sao vàng), far = font-awesome regular (sao rỗng)
        starsHtml += `<i class="${i <= rating ? 'fas' : 'far'} fa-star"></i>`;
    }
    return starsHtml;
}

/**
 * Hàm đổ dữ liệu vào giao diện
 */
function renderReviews(data) {
    const reviewList = document.getElementById('review-list');
    if (!reviewList) return;

    // 1. Cập nhật con số tổng quan (Header)
    const ratingScoreEl = document.querySelector('.rating-overview__score');
    const starsStaticEl = document.querySelector('.rating-overview__stars');
    
    if (ratingScoreEl) ratingScoreEl.textContent = data.average_rating || 0;
    if (starsStaticEl) starsStaticEl.innerHTML = generateStarsHtml(Math.round(data.average_rating || 0));

    // 2. Cập nhật số lượng trên các nút Filter
    if (data.counts) {
        const stars = ['1', '2', '3', '4', '5'];
        stars.forEach(s => {
            const btn = document.querySelector(`.btn-filter[data-star="${s}"]`);
            if (btn) btn.textContent = `${s} Sao (${data.counts[s] || 0})`;
        });
        const btnComment = document.querySelector('.btn-filter[data-star="comment"]');
        if (btnComment) btnComment.textContent = `Bình Luận (${data.counts['comment'] || 0})`;
    }

    // 3. Render danh sách bài đánh giá
    const reviews = data.reviews || data.items || [];
    reviewList.innerHTML = ''; // Xóa sạch cũ

    if (reviews.length === 0) {
        reviewList.innerHTML = '<div style="padding: 60px; text-align: center; color: rgba(0,0,0,.4);">Chưa có đánh giá nào.</div>';
        return;
    }

    reviewList.innerHTML = reviews.map(rev => `
        <div class="review-item">
            <div class="review-item__avatar">
                <img src="https://ui-avatars.com/api/?name=${rev.user_name || 'U'}&background=f5f5f5&color=ee4d2d" 
                    style="width:100%; height:100%; object-fit:cover;">
            </div>
            <div class="review-item__content">
                <div class="review-item__author">${rev.user_name || 'Người dùng OneShop'}</div>
                <div class="review-item__stars">${generateStarsHtml(rev.rating)}</div>
                <div class="review-item__date">${rev.created_at || ''}</div>
                <div class="review-item__comment">${rev.comment || 'Khách hàng không để lại bình luận.'}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Gọi API lấy dữ liệu
 */
async function loadProductReviews() {
    const pageEl = document.getElementById('product-detail-page');
    const reviewList = document.getElementById('review-list');
    
    if (!pageEl || !reviewList) return;

    // QUAN TRỌNG: Xóa nội dung cũ (dòng chữ lỗi) trước khi load
    reviewList.innerHTML = '<div style="text-align:center; padding:20px;">Đang tải đánh giá...</div>';

    const productId = pageEl.dataset.productId;
    try {
        // Gọi đúng endpoint base từ data attribute
        const response = await fetch(`/products/${productId}/reviews`);
        if (!response.ok) throw new Error("Lỗi server");
        
        const data = await response.json();
        renderReviews(data);
    } catch (error) {
        console.error("Lỗi:", error);
        reviewList.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">Chưa có đánh giá nào.</div>';
    }
}
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-filter')) {
        // Đổi màu nút active
        document.querySelectorAll('.btn-filter').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
        
        const filterType = e.target.dataset.star;
        // Logic lọc dữ liệu ở đây nếu bạn muốn làm lọc phía Client
        // Hoặc đơn giản là gọi lại API với tham số ?star=5
    }
});
// Chạy khi trang sẵn sàng
document.addEventListener('DOMContentLoaded', loadProductReviews);