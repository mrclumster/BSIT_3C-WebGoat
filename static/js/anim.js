/* WebGoat Quarterly · v4 animations
 * No build step. Vanilla JS. Honors prefers-reduced-motion.
 *
 *  - [data-count-up="42"]              animate 0 → 42 over ~800ms
 *  - [data-scroll-reveal]              fade+rise once on entering viewport
 *  - [data-magnetic]                   button gently follows cursor
 *  - [data-typewriter="text"]          types text once
 *  - .htmx-* swaps                     soft crossfade (CSS handles the rest)
 */
(function () {
  'use strict';

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ease = (t) => 1 - Math.pow(1 - t, 4); // easeOutQuart

  /* ---------- Count-up ---------- */
  function countUp(el) {
    const target = parseFloat(el.dataset.countUp);
    if (Number.isNaN(target)) return;
    if (reduced) { el.textContent = String(target); return; }
    const dur = parseInt(el.dataset.countDuration || '850', 10);
    const start = performance.now();
    const isInt = Number.isInteger(target);
    function tick(now) {
      const t = Math.min(1, (now - start) / dur);
      const v = target * ease(t);
      el.textContent = isInt ? Math.round(v).toString() : v.toFixed(1);
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = String(target);
    }
    requestAnimationFrame(tick);
  }

  /* ---------- Scroll-reveal ---------- */
  const io = ('IntersectionObserver' in window) && !reduced
    ? new IntersectionObserver((entries) => {
        entries.forEach((e, i) => {
          if (e.isIntersecting) {
            const el = e.target;
            const idx = parseInt(el.dataset.scrollIndex || '0', 10);
            setTimeout(() => el.classList.add('is-visible'), idx * 50);
            io.unobserve(el);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' })
    : null;

  /* ---------- Magnetic ---------- */
  function attachMagnetic(el) {
    if (reduced) return;
    const strength = parseFloat(el.dataset.magnetic || '0.25');
    const max = 6;
    el.classList.add('magnetic');
    el.addEventListener('mousemove', (e) => {
      const r = el.getBoundingClientRect();
      const dx = (e.clientX - (r.left + r.width / 2)) * strength;
      const dy = (e.clientY - (r.top + r.height / 2)) * strength;
      el.style.setProperty('--mx', Math.max(-max, Math.min(max, dx)) + 'px');
      el.style.setProperty('--my', Math.max(-max, Math.min(max, dy)) + 'px');
    });
    el.addEventListener('mouseleave', () => {
      el.style.setProperty('--mx', '0px');
      el.style.setProperty('--my', '0px');
    });
  }

  /* ---------- Typewriter ---------- */
  function typewriter(el) {
    const text = el.dataset.typewriter;
    if (!text) return;
    if (reduced) { el.textContent = text; el.classList.add('done'); return; }
    const speed = parseInt(el.dataset.typeSpeed || '22', 10);
    const delay = parseInt(el.dataset.typeDelay || '300', 10);
    const key = 'tw-' + (el.dataset.typewriterKey || text.slice(0, 12));
    if (sessionStorage.getItem(key)) { el.textContent = text; el.classList.add('done'); return; }
    sessionStorage.setItem(key, '1');
    el.textContent = '';
    let i = 0;
    setTimeout(function step() {
      el.textContent = text.slice(0, ++i);
      if (i < text.length) setTimeout(step, speed);
      else el.classList.add('done');
    }, delay);
  }

  /* ---------- Init ---------- */
  function init(root) {
    root = root || document;
    root.querySelectorAll('[data-count-up]').forEach(countUp);
    if (io) root.querySelectorAll('[data-scroll-reveal]').forEach((el, i) => {
      if (!el.dataset.scrollIndex) el.dataset.scrollIndex = String(i % 8);
      io.observe(el);
    });
    root.querySelectorAll('[data-magnetic]').forEach(attachMagnetic);
    root.querySelectorAll('[data-typewriter]').forEach(typewriter);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init());
  } else {
    init();
  }

  // Re-init after HTMX swaps
  document.addEventListener('htmx:afterSwap', (e) => init(e.target));

  window.WGAnim = { init, countUp, typewriter };
})();
