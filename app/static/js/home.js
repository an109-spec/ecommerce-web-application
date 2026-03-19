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