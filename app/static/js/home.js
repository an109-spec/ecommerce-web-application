(function () {
    const categoryContainer = document.querySelector('.category-shopee-list');
    const categoryPrevBtn = document.querySelector('.category-prev');
    const categoryNextBtn = document.querySelector('.category-next');

    if (categoryContainer && categoryPrevBtn && categoryNextBtn) {
        // Cuộn ngang khoảng 4 cột mỗi lần click (120px * 4 = 480px)
        const scrollAmount = 480; 

        categoryPrevBtn.addEventListener('click', () => {
            categoryContainer.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });
        categoryNextBtn.addEventListener('click', () => {
            categoryContainer.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });
    }
})();

(function () {
  const el = document.getElementById('flash-countdown');
  if (!el) return;

  const endsAt = el.dataset.endsAt;
  if (!endsAt) {
    el.textContent = 'Đã kết thúc';
    return;
  }

  const endTime = new Date(endsAt).getTime();
  if (Number.isNaN(endTime)) {
    el.textContent = 'Đã kết thúc';
    return;
  }

  const render = () => {
    const diff = endTime - Date.now();
    if (diff <= 0) {
      el.textContent = 'Đã kết thúc';
      clearInterval(timer);
      return;
    }

    const sec = Math.floor(diff / 1000) % 60;
    const min = Math.floor(diff / (1000 * 60)) % 60;
    const hour = Math.floor(diff / (1000 * 60 * 60));
    el.textContent = [hour, min, sec].map((v) => String(v).padStart(2, '0')).join(':');
  };

  render();
  const timer = setInterval(render, 1000);
})();
(function () {
  const scrollContainer = document.querySelector('.flash-sale-scroll');
  const prevBtn = document.querySelector('.flash-prev');
  const nextBtn = document.querySelector('.flash-next');
  if (!scrollContainer || !prevBtn || !nextBtn) return;

  const scrollAmount = 180; // khoảng cách scroll mỗi click

  prevBtn.addEventListener('click', () => {
    scrollContainer.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
  });

  nextBtn.addEventListener('click', () => {
    scrollContainer.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  });
})();

(function () {
    const updateCountdowns = () => {
        const now = new Date().getTime();
        const items = document.querySelectorAll('.flash-item');

        items.forEach(item => {
            const endsAt = item.getAttribute('data-ends-at');
            const timerEl = item.querySelector('.item-timer');
            if (!endsAt || !timerEl) return;

            const diff = new Date(endsAt).getTime() - now;

            if (diff <= 0) {
                timerEl.textContent = "Hết hạn";
                item.style.opacity = "0.7";
                return;
            }

            const h = Math.floor(diff / (1000 * 60 * 60));
            const m = Math.floor((diff / (1000 * 60)) % 60);
            const s = Math.floor((diff / 1000) % 60);

            timerEl.textContent = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        });
    };

    updateCountdowns();
    setInterval(updateCountdowns, 1000);
})();

// 2. Hiện chữ dưới khoảng giá
const minInp = document.getElementById('min_price_input');
const maxInp = document.getElementById('max_price_input');
const priceText = document.getElementById('price-display-text');

function updatePriceText() {
    const min = minInp.value ? parseInt(minInp.value).toLocaleString('vi-VN') : '0';
    const max = maxInp.value ? parseInt(maxInp.value).toLocaleString('vi-VN') : 'Tối đa';
    if (minInp.value || maxInp.value) {
        priceText.innerText = `Lọc sản phẩm từ ${min} ₫ đến ${max} ₫`;
    } else {
        priceText.innerText = '';
    }
}
minInp.addEventListener('input', updatePriceText);
maxInp.addEventListener('input', updatePriceText);
let currentSlide = 0;

function moveSlide(direction) {
    const slider = document.querySelector('.slider-container');
    const items = document.querySelectorAll('.slider-item');
    if (!slider || items.length === 0) return;
    const totalItems = items.length;

    currentSlide += direction;

    if (currentSlide >= totalItems) currentSlide = 0;
    if (currentSlide < 0) currentSlide = totalItems - 1;

    const offset = -currentSlide * 100;
    slider.style.transform = `translateX(${offset}%)`;
}
if (document.querySelector('.slider-container')) {
    setInterval(() => moveSlide(1), 3000);
}

function copyVoucher(code) {
    alert("Đã lưu mã: " + code + ". Bạn có thể sử dụng khi thanh toán!");
}

// Tự động chạy slider mỗi 3 giây
setInterval(() => moveSlide(1), 3000);
let currentHeroIdx = 0;
let heroInterval = null;

window.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.hero-slide');

    // Tìm slide active ban đầu
    let found = false;
    slides.forEach((s, i) => {
        if (s.classList.contains('active')) {
            currentHeroIdx = i;
            found = true;
        }
    });

    // Nếu không có active thì set cái đầu
    if (!found && slides.length > 0) {
        slides[0].classList.add('active');
        currentHeroIdx = 0;
    }

    // Chỉ tạo 1 interval duy nhất
    if (heroInterval) clearInterval(heroInterval);
    heroInterval = setInterval(() => changeHeroSlide(1), 5000);
});

function changeHeroSlide(dir) {
    const slides = document.querySelectorAll('.hero-slide');
    if (slides.length <= 1) return;

    slides.forEach(slide => slide.classList.remove('active'));

    currentHeroIdx = (currentHeroIdx + dir + slides.length) % slides.length;
    if (slides[currentHeroIdx]) {
      slides[currentHeroIdx].classList.add('active');
}
}
function copyCode(code) {
    navigator.clipboard.writeText(code);
    alert("Đã copy mã giảm giá: " + code);
}

// Tự động chuyển sau 5 giây
setInterval(() => changeHeroSlide(1), 5000);