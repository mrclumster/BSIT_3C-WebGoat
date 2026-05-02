// Tiny client glue: toast bus, celebration modal, copy-to-clipboard helper, lucide re-render after swaps.

// Pre-Alpine queue: any 'toast' / 'celebrate' events fired before Alpine finishes initializing
// get parked here and drained by toastBus.init() so we never miss a server-emitted notification.
(function () {
  window._pendingEvents = { toast: [], celebrate: [] };
  window._toastBusReady = false;
  ['toast', 'celebrate'].forEach(function (name) {
    document.addEventListener(name, function (e) {
      if (!window._toastBusReady) window._pendingEvents[name].push(e.detail || {});
    });
  });
})();

window.toastBus = function () {
  return {
    toasts: [],
    celebrate: { show: false, title: '', message: '', continueUrl: '#' },
    init() {
      document.addEventListener('toast',     (e) => this.push(e.detail || {}));
      document.addEventListener('celebrate', (e) => this.celebrateNow(e.detail || {}));
      window._toastBusReady = true;
      // Drain any events that fired before init.
      (window._pendingEvents.toast || []).forEach((d) => this.push(d));
      window._pendingEvents.toast = [];
      const pendingCel = (window._pendingEvents.celebrate || []);
      if (pendingCel.length) {
        this.celebrateNow(pendingCel[pendingCel.length - 1]);
        window._pendingEvents.celebrate = [];
      }
    },
    push({ message = 'Done', kind = 'info', ttl = 3500 } = {}) {
      const id = Date.now() + Math.random();
      this.toasts.push({ id, message, kind });
      setTimeout(() => { try { window.lucide && window.lucide.createIcons(); } catch(e){} }, 30);
      setTimeout(() => { this.toasts = this.toasts.filter(t => t.id !== id); }, ttl);
    },
    celebrateNow({ title = 'Lesson complete!', message = 'You finished every stage.', continueUrl = '#' } = {}) {
      this.celebrate = { show: true, title, message, continueUrl };
      setTimeout(() => { try { window.lucide && window.lucide.createIcons(); } catch(e){} }, 30);
      if (typeof window.confetti === 'function') {
        const end = Date.now() + 1200;
        const colors = ['#c41818', '#0c0a08', '#b07a1f', '#f1e9d6'];
        (function frame() {
          window.confetti({ particleCount: 4, angle: 60, spread: 55, origin: { x: 0 }, colors });
          window.confetti({ particleCount: 4, angle: 120, spread: 55, origin: { x: 1 }, colors });
          if (Date.now() < end) requestAnimationFrame(frame);
        })();
      }
    },
  };
};

window.copyToClipboard = function (text, label) {
  try {
    navigator.clipboard.writeText(text).then(() => {
      document.dispatchEvent(new CustomEvent('toast', {
        detail: { message: (label || 'Copied') + ' to clipboard', kind: 'success' }
      }));
    });
  } catch (e) {
    document.dispatchEvent(new CustomEvent('toast', {
      detail: { message: 'Copy failed — select manually', kind: 'error' }
    }));
  }
};

// HTMX hooks: re-render Lucide icons + Prism after every swap (boost + hint partial both go through here).
document.addEventListener('htmx:afterSwap', () => {
  try { window.lucide && window.lucide.createIcons(); } catch(e) {}
  if (window.Prism) try { window.Prism.highlightAllUnder(document.body); } catch(e) {}
});

// Final pass on full page load.
window.addEventListener('load', () => {
  try { window.lucide && window.lucide.createIcons(); } catch(e) {}
});
