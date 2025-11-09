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
