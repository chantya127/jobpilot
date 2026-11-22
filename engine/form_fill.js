// fillform: fill many fields in one call. `data` maps formdump keys (or CSS selectors) to values:
//   text/textarea/email/tel/number/date → string      select → option text (case-insensitive, exact then partial)
//   radio group → option label                          checkbox → true/false
// Uses the native value setter + input/change/blur events so React/Vue/Angular forms register the change.
// Returns one line per key: ok/FAIL and the value read back. Custom (non-native) comboboxes must still be clicked.
(data) => {
  const clean = t => (t || "").replace(/\s+/g, " ").trim();
  const fire = (el, ...types) => types.forEach(t => el.dispatchEvent(new Event(t, { bubbles: true })));
  const setVal = (el, v) => {
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : el.tagName === "SELECT" ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(el, v);
  };
  const labelText = el => clean((el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.innerText) || el.closest("label")?.innerText || el.getAttribute("aria-label") || el.value);
  const find = k => /^f\d+$/.test(k) ? [...document.querySelectorAll(`[data-jp="${k}"]`)] : [...document.querySelectorAll(k)];
  const out = [];
  for (const [k, raw] of Object.entries(data)) {
    const els = find(k);
    if (!els.length) { out.push(`${k}: FAIL not found (run formdump again)`); continue; }
    const el = els[0], v = typeof raw === "string" ? raw : raw;
    try {
      if (el.type === "radio") {
        const want = clean(String(v)).toLowerCase();
        const r = els.find(e => labelText(e).toLowerCase() === want) || els.find(e => labelText(e).toLowerCase().startsWith(want)) || els.find(e => clean(e.value).toLowerCase() === want);
        if (!r) { out.push(`${k}: FAIL no option "${v}" (have: ${els.map(labelText).join(" / ")})`); continue; }
        if (!r.checked) r.click();
        out.push(`${k}: ok ${labelText(r)}`);
      } else if (el.type === "checkbox") {
        const want = v === true || /^(true|yes|1|on)$/i.test(String(v));
        if (el.checked !== want) el.click();
        out.push(`${k}: ${el.checked === want ? "ok" : "FAIL"} ${el.checked}`);
      } else if (el.tagName === "SELECT") {
        const want = clean(String(v)).toLowerCase();
        const opts = [...el.options];
        const o = opts.find(x => clean(x.text).toLowerCase() === want) || opts.find(x => clean(x.value).toLowerCase() === want)
               || opts.find(x => clean(x.text).toLowerCase().includes(want));
        if (!o) { out.push(`${k}: FAIL no option "${v}"`); continue; }
        setVal(el, o.value); fire(el, "input", "change", "blur");
        out.push(`${k}: ok ${clean(o.text)}`);
      } else if (el.type === "file") {
        out.push(`${k}: FAIL file inputs: use up "[data-jp=${k}]"`);
      } else {
        el.focus(); setVal(el, String(v)); fire(el, "input", "change"); el.blur(); fire(el, "blur", "focusout");
        out.push(`${k}: ${el.value === String(v) ? "ok" : "CHECK"} ${clean(el.value).slice(0, 60)}`);
      }
    } catch (e) { out.push(`${k}: FAIL ${e.message}`); }
  }
  return out.join("\n");
}
