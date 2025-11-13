// Счётчики «растут» при появлении в вьюпорте
(function(){
  const els = document.querySelectorAll('.mini-stats .num');
  if(!els.length) return;
  const ease = t => 1 - Math.pow(1 - t, 3);
  const animate = el => {
    const end = Number(el.dataset.count || 0);
    const dur = 1000 + Math.random()*700;
    const st = performance.now();
    const tick = now => {
      const p = Math.min(1, (now - st)/dur);
      el.textContent = Math.floor(end*ease(p));
      if(p<1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){ animate(e.target); io.unobserve(e.target); }
    });
  }, {threshold:.5});
  els.forEach(el=>io.observe(el));
})();

// Конфетти по клику
(function(){
  const btn = document.querySelector('.confetti-btn');
  if(!btn) return;
  btn.addEventListener('click', ()=>{
    shootConfetti();
  });

  function shootConfetti(){
    const colors = ['#6366f1','#22d3ee','#f472b6','#f59e0b','#22c55e'];
    const count = 120;
    const w = window.innerWidth;
    for(let i=0;i<count;i++){
      const d = document.createElement('i');
      d.className = 'confetti';
      d.style.left = (Math.random()*w) + 'px';
      d.style.background = colors[Math.floor(Math.random()*colors.length)];
      const rot = (Math.random()*360)|0;
      const fall = 800 + Math.random()*900;
      const drift = (Math.random()*120 - 60);
      d.style.transform = `rotate(${rot}deg)`;
      document.body.appendChild(d);
      d.animate([
        { transform:`translate(0, -20px) rotate(${rot}deg)`, opacity:1 },
        { transform:`translate(${drift}px, ${fall}px) rotate(${rot+360}deg)`, opacity:0.2 }
      ],{ duration: 1400 + Math.random()*800, easing: 'cubic-bezier(.22,.61,.36,1)' })
      .onfinish = ()=> d.remove();
    }
  }
})();
(function () {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;

  const iconSpan = btn.querySelector('.theme-icon');

  // подстановка правильной иконки
  const syncIcon = () => {
    const theme = document.documentElement.getAttribute('data-theme');
    iconSpan.textContent = theme === 'dark' ? '🌙' : '☀️';
  };

  // если пользователь не выбирал — уважаем системную тему при первом заходе,
  // но inline-скрипт в <head> это уже сделал. Здесь только иконку синхронизируем.
  syncIcon();

  btn.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('ff-theme', next); } catch (e) {}
    syncIcon();
  });

  // если пользователь выбрал "auto", можно подписаться на смену системной темы:
  // но мы сохраняем явный light/dark. Если захочешь режим "auto" — скажи, добавлю тристейт.
})();

async function fetchJSON(url, opts={}) {
  const r = await fetch(url, Object.assign({
    headers: { "X-Requested-With": "XMLHttpRequest" }
  }, opts));
  if (!r.ok) throw new Error("Request failed");
  return r.json();
}

async function refreshNotifBadge() {
  try {
    const data = await fetchJSON("/api/notifications/unread_count/");
    const badge = document.getElementById("notifBadge");
    if (!badge) return;
    const n = data.count || 0;
    badge.textContent = n;
    badge.classList.toggle("d-none", n === 0);
  } catch(e) {
    // тихо игнорируем
  }
}

async function loadNotifs() {
  try {
    const data = await fetchJSON("/api/notifications/?page=1");
    const list = document.getElementById("notifList");
    if (!list) return;
    list.innerHTML = "";
    data.results?.forEach(n => {
      const div = document.createElement("div");
      div.className = "border rounded p-2";
      div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <strong>${n.title}</strong>
          ${n.is_read ? "" : '<span class="badge bg-primary">new</span>'}
        </div>
        <div class="small text-muted">${new Date(n.created_at).toLocaleString()}</div>
        <div>${n.message || ""}</div>
        ${!n.is_read ? `<button class="btn btn-sm btn-link p-0 mark-read" data-id="${n.id}">Отметить прочитанным</button>` : ""}
      `;
      list.appendChild(div);
    });

    list.addEventListener("click", async (ev) => {
      const btn = ev.target.closest(".mark-read");
      if (!btn) return;
      const id = btn.getAttribute("data-id");
      await fetchJSON(`/api/notifications/${id}/mark_read/`, { method: "POST", headers: {"X-CSRFToken": getCookie('csrftoken')} });
      await loadNotifs();
      await refreshNotifBadge();
    }, { once: true });
  } catch(e) {}
}

async function markAllRead() {
  try {
    await fetchJSON("/api/notifications/mark_all_read/", { method: "POST", headers: {"X-CSRFToken": getCookie('csrftoken')} });
    await loadNotifs();
    await refreshNotifBadge();
  } catch(e) {}
}

function getCookie(name) { // стандартная утилита для CSRF
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const c = cookie.trim();
      if (c.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
  refreshNotifBadge();
  setInterval(refreshNotifBadge, 30000); // каждые 30 сек
  const offc = document.getElementById("notifOffcanvas");
  if (offc) {
    offc.addEventListener("show.bs.offcanvas", loadNotifs);
  }
  const btnAll = document.getElementById("markAllReadBtn");
  if (btnAll) btnAll.addEventListener("click", markAllRead);
});