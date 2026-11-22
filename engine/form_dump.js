// formdump: one compact line per visible form field, each tagged with a stable key (f1, f2…) for fillform.
// key | type | label | value [| options]   (radios are grouped: one line per group)
(() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return (r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none") || el.type === "file"; };
  const clean = t => (t || "").replace(/\s+/g, " ").trim().slice(0, 110);
  const labelOf = el => {
    if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) return clean(l.innerText); }
    if (el.getAttribute("aria-label")) return clean(el.getAttribute("aria-label"));
    const by = el.getAttribute("aria-labelledby");
    if (by) { const t = by.split(/\s+/).map(i => document.getElementById(i)?.innerText || "").join(" "); if (t.trim()) return clean(t); }
    const wrap = el.closest("label"); if (wrap) return clean(wrap.innerText);
    const fs = el.closest("fieldset"); if (fs && fs.querySelector("legend")) return clean(fs.querySelector("legend").innerText);
    let p = el.parentElement;                       // nearest preceding text in the field's container
    for (let i = 0; i < 4 && p; i++, p = p.parentElement) {
      const t = clean([...p.childNodes].filter(n => n !== el && !(n.contains && n.contains(el))).map(n => n.innerText || n.textContent || "").join(" "));
      if (t) return t;
    }
    return clean(el.placeholder || el.name || "");
  };
  let n = 0; const out = []; const groups = {};
  const fields = [...document.querySelectorAll("input, textarea, select")]
    .filter(el => !["hidden", "submit", "button", "reset", "image"].includes(el.type) && vis(el) && !el.closest("#jobpilot-review-lock"));
  for (const el of fields) {
    if (el.type === "radio") {
      const g = el.name || labelOf(el.closest("fieldset") || el.parentElement);
      if (!groups[g]) { groups[g] = { key: "f" + (++n), els: [] }; out.push(groups[g]); }
      groups[g].els.push(el); el.setAttribute("data-jp", groups[g].key); continue;
    }
    const key = "f" + (++n); el.setAttribute("data-jp", key);
    out.push({ key, el });
  }
  return out.map(o => {
    if (o.els) {
      const q = clean(o.els[0].closest("fieldset")?.querySelector("legend")?.innerText || o.els[0].closest("[role=radiogroup]")?.getAttribute("aria-label") || labelOf(o.els[0].closest("fieldset,[role=radiogroup]") || o.els[0].parentElement?.parentElement || o.els[0]));
      const opts = o.els.map(e => labelOf(e) || e.value);
      const cur = o.els.find(e => e.checked);
      return `${o.key} | radio | ${q} | ${cur ? labelOf(cur) || cur.value : ""} | ${opts.join(" / ")}`;
    }
    const el = o.el;
    const req = (el.required || el.getAttribute("aria-required") === "true") && !/\*\s*$/.test(labelOf(el)) ? "*" : "";
    if (el.tagName === "SELECT") {
      const opts = [...el.options].map(x => clean(x.text)).filter(Boolean);
      return `${o.key} | select | ${labelOf(el)}${req} | ${clean(el.options[el.selectedIndex]?.text)} | ${opts.slice(0, 15).join(" / ")}${opts.length > 15 ? " …" : ""}`;
    }
    if (el.type === "checkbox") return `${o.key} | checkbox | ${labelOf(el)}${req} | ${el.checked}`;
    if (el.type === "file") return `${o.key} | file | ${labelOf(el)}${req} | ${el.files?.length ? el.files[0].name : ""}`;
    const t = el.getAttribute("role") === "combobox" || el.getAttribute("aria-autocomplete") ? "combobox" : (el.tagName === "TEXTAREA" ? "textarea" : el.type);
    return `${o.key} | ${t} | ${labelOf(el)}${req} | ${clean(el.value)}`;
  }).join("\n") || "no form fields found";
})()
