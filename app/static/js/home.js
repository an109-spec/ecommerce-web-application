(function () {
  const el = document.getElementById("flash-countdown");
  if (!el) return;

  const endsAt = el.dataset.endsAt;
  if (!endsAt) return;

  function render() {
    const diff = new Date(endsAt).getTime() - Date.now();
    if (diff <= 0) {
      el.textContent = "Đã kết thúc";
      return;
    }

    const sec = Math.floor(diff / 1000) % 60;
    const min = Math.floor(diff / (1000 * 60)) % 60;
    const hour = Math.floor(diff / (1000 * 60 * 60));
    el.textContent = [hour, min, sec].map((v) => String(v).padStart(2, "0")).join(":");
    requestAnimationFrame(render);
  }

  render();
})();
document.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("flash-countdown")
  if (!el) return

  const end = new Date(el.dataset.endsAt).getTime()

  setInterval(() => {
    const now = Date.now()
    const diff = end - now

    if (diff <= 0) {
      el.innerHTML = "Đã kết thúc"
      return
    }

    const h = Math.floor(diff / 3600000)
    const m = Math.floor((diff % 3600000) / 60000)
    const s = Math.floor((diff % 60000) / 1000)

    el.innerHTML =
      String(h).padStart(2, "0") + ":" +
      String(m).padStart(2, "0") + ":" +
      String(s).padStart(2, "0")
  }, 1000)
})