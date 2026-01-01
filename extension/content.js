(function install() {
  if (globalThis.__lucInstalled) return;
  globalThis.__lucInstalled = true;

  // Expose current link under cursor for the background to read
  globalThis.__linkUnderCursor = null;
  globalThis.__linkUnderCursorTitle = null;

  function resolveAnchor(el) {
    if (!el) return null;
    // Direct anchor
    if (el.tagName && el.tagName.toLowerCase() === 'a' && el.href) return el;
    // Inside an anchor
    if (el.closest) {
      const a = el.closest('a[href]');
      if (a && a.href) return a;
    }
    // Common patterns: clickable elements with data-href or role=link
    if (el.getAttribute) {
      const dh = el.getAttribute('data-href');
      if (dh) {
        const a = document.createElement('a');
        a.href = dh; a.textContent = el.textContent || '';
        return a;
      }
    }
    return null;
  }

  function updateFromTarget(target) {
    const anchor = resolveAnchor(target);
    if (anchor) {
      globalThis.__linkUnderCursor = anchor.href;
      globalThis.__linkUnderCursorTitle = anchor.textContent?.trim() || anchor.title || anchor.href;
    } else {
      globalThis.__linkUnderCursor = null;
      globalThis.__linkUnderCursorTitle = null;
    }
  }

  // Track mouse, pointer and touch
  const opts = { capture: true, passive: true };
  document.addEventListener('mousemove', (e) => updateFromTarget(e.target), opts);
  document.addEventListener('pointermove', (e) => updateFromTarget(e.target), opts);
  document.addEventListener('mouseover', (e) => updateFromTarget(e.target), true);

  // Also update on focus changes (keyboard navigation / accessibility)
  document.addEventListener('focusin', (e) => updateFromTarget(e.target), true);

  // Reset on leave
  document.addEventListener('mouseleave', () => {
    globalThis.__linkUnderCursor = null;
    globalThis.__linkUnderCursorTitle = null;
  }, true);
})();
