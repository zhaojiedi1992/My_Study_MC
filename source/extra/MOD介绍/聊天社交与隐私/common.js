(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const dots = [...document.querySelectorAll('.dot')];
  const prev = document.querySelector('[data-nav="prev"]');
  const next = document.querySelector('[data-nav="next"]');
  const params = new URLSearchParams(location.search);
  const exportMode = params.get('export') === '1';
  if (exportMode) document.documentElement.classList.add('export-mode');
  let current = Math.max(0, Math.min(slides.length - 1, Number(params.get('slide') || 1) - 1));
  function show(index, updateUrl = true) {
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((slide, i) => slide.classList.toggle('active', i === current));
    dots.forEach((dot, i) => dot.classList.toggle('active', i === current));
    if (prev) prev.disabled = current === 0;
    if (next) next.disabled = current === slides.length - 1;
    if (updateUrl) history.replaceState(null, '', `?slide=${current + 1}`);
  }
  prev?.addEventListener('click', () => show(current - 1));
  next?.addEventListener('click', () => show(current + 1));
  dots.forEach((dot, i) => dot.addEventListener('click', () => show(i)));
  document.querySelectorAll('[data-go]').forEach((button) => button.addEventListener('click', () => show(Number(button.dataset.go))));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft' || event.key === 'PageUp') show(current - 1);
    if (event.key === 'ArrowRight' || event.key === 'PageDown' || event.key === ' ') { event.preventDefault(); show(current + 1); }
    if (event.key === 'Home') show(0);
    if (event.key === 'End') show(slides.length - 1);
  });
  let startX = null;
  document.addEventListener('touchstart', (event) => { startX = event.changedTouches[0].clientX; }, {passive:true});
  document.addEventListener('touchend', (event) => { if (startX === null) return; const dx = event.changedTouches[0].clientX - startX; if (Math.abs(dx) > 45) show(current + (dx < 0 ? 1 : -1)); startX = null; }, {passive:true});
  show(current, false);
})();
