// JobPilot review lock. Injected into worker tabs when auto-submit is OFF, before and after every agent action.
// Blocks the FINAL submit of an application (submit-like buttons, form submit events, form.submit()/requestSubmit()),
// so an agent can't send an application even by accident (e.g. Enter in a field). Sign-in / "Next" / code forms are not
// touched. A small banner lets the human unlock the page and submit.
(() => {
  if (window.__jpg) return "guarded";
  window.__jpg = 1;
  const off = () => window.__jp_off === true;
  const FINAL = /^(submit|submit application|submit my application|send application|apply|apply now|finish|finish application|complete application|confirm and submit|submit & finish)$/i;
  const fieldsIn = root => [...root.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=search]),textarea,select')]
    .filter(i => (i.value || "").trim()).length;
  const isFinal = el => {
    const b = el && el.closest && el.closest('button,input[type=submit],[role=button],a');
    if (!b || b.closest('#jobpilot-review-lock')) return false;
    const t = (b.innerText || b.value || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim();
    if (!FINAL.test(t)) return false;
    return !/^apply/i.test(t) || fieldsIn(document) >= 3;   // "Apply" on a job listing page just opens the form
  };
  const note = () => { window.__jp_blocked = (window.__jp_blocked || 0) + 1; };
  document.addEventListener('click', e => {
    if (off()) return;
    const t = e.composedPath ? e.composedPath()[0] : e.target;
    if (isFinal(t)) { e.preventDefault(); e.stopImmediatePropagation(); note(); }
  }, true);
  document.addEventListener('submit', e => {
    if (off() || fieldsIn(e.target) < 4) return;            // small forms = sign-in / email / code steps
    e.preventDefault(); e.stopImmediatePropagation(); note();
  }, true);
  const F = HTMLFormElement.prototype, s = F.submit, r = F.requestSubmit;
  F.submit = function () { if (off() || fieldsIn(this) < 4) return s.call(this); note(); };
  if (r) F.requestSubmit = function (...a) { if (off() || fieldsIn(this) < 4) return r.apply(this, a); note(); };
  const bar = document.createElement('div');
  bar.id = 'jobpilot-review-lock';
  bar.innerHTML = '🔒 <b>JobPilot review lock</b>: the agent can’t submit this form. <button type="button">Unlock so I can submit</button>';
  Object.assign(bar.style, { position: 'fixed', left: '12px', bottom: '12px', zIndex: 2147483647, background: '#1d1d1b',
    color: '#fff', padding: '8px 12px', borderRadius: '10px', font: '13px system-ui, sans-serif', boxShadow: '0 4px 14px rgba(0,0,0,.3)' });
  const btn = bar.querySelector('button');
  Object.assign(btn.style, { marginLeft: '8px', padding: '4px 10px', borderRadius: '6px', border: '0', cursor: 'pointer' });
  btn.onclick = () => { window.__jp_off = true; bar.textContent = '🔓 Unlocked: you can submit now'; setTimeout(() => bar.remove(), 3000); };
  const add = () => (document.body || document.documentElement).appendChild(bar);
  document.body ? add() : document.addEventListener('DOMContentLoaded', add);
  return "ok";
})()
