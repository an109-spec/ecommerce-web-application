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
