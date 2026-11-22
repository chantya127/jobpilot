// Small Alpine components shared by the dashboard pages.

// Keep a scroll box pinned to the bottom only while the user is already at the bottom,
// so reading older lines never gets yanked away by new output.
function nearBottom(el) { return !el || el.scrollHeight - el.scrollTop - el.clientHeight < 40; }
function toBottom(el) { if (el) el.scrollTop = el.scrollHeight; }
// Icons and status labels come from jobpilot/ui.py via window.ICONS / window.STATUS_LABELS (set in base.html).
function icon(name) { return (window.ICONS || {})[name] || ""; }
function statusLabel(s) { return (window.STATUS_LABELS || {})[s] || String(s || "").replace(/-/g, " "); }
const LOG_ICON = { tool: "terminal", text: "message", result: "check", info: "dot" };
const FEED_ICON = { queued: "plus", known: "dot", easy: "user", skip: "minus", error: "alert", done: "check" };
function logIcon(kind) { return icon(LOG_ICON[kind] || "dot"); }
function feedIcon(tag) { return FEED_ICON[tag] ? icon(FEED_ICON[tag]) : ""; }

async function getJSON(url) { const r = await fetch(url); return r.json(); }
async function postForm(url, data) {
  const fd = new FormData(); Object.entries(data || {}).forEach(([k, v]) => fd.append(k, v));
  return fetch(url, { method: "POST", body: fd });
}

// Multi-select chips with presets + custom values. Stored in a hidden input as "a; b; c".
function chips(initial, options, single) {
  return {
    options: options || [], single: !!single, custom: "",
    selected: (initial || "").split(/;|\n/).map(s => s.trim()).filter(Boolean),
    get value() { return this.selected.join("; "); },
    has(o) { return this.selected.includes(o); },
    toggle(o) {
      if (this.has(o)) { this.selected = this.selected.filter(x => x !== o); return; }
      this.selected = this.single ? [o] : [...this.selected, o];
    },
    add() {
      const v = this.custom.trim(); if (!v) return;
      if (!this.has(v)) this.selected = this.single ? [v] : [...this.selected, v];
      this.custom = "";
    },
    get extra() { return this.selected.filter(s => !this.options.includes(s)); },
  };
}

// Tag input (keywords, avoid list, stack). Stored newline-separated.
function tags(initial) {
  return {
    items: (initial || []).slice(), draft: "",
    get value() { return this.items.join("\n"); },
    add() {
      this.draft.split(/[,\n]/).map(s => s.trim()).filter(Boolean)
        .forEach(v => { if (!this.items.some(i => i.toLowerCase() === v.toLowerCase())) this.items.push(v); });
      this.draft = "";
    },
    remove(i) { this.items.splice(i, 1); },
    back() { if (!this.draft && this.items.length) this.items.pop(); },
  };
}

// Find jobs: idle (start button + last summary) ⇄ running (steps, live counts, Stop). Log hidden behind "details".
function findPage(initialBusy, hasSearch) {
  const zero = () => ({ queued: 0, known: 0, easy: 0, skip: 0, error: 0 });
  return {
    busy: initialBusy, hasSearch, lines: [], total: 0, phase: "starting", activity: "Starting…",
    counts: zero(), summary: null, details: false, follow: true, starting: false, stopping: false,
    stepClass(step) {
      const order = ["starting", "notifications", "search", "done"];
      const cur = order.indexOf(this.phase), me = order.indexOf(step);
      return me < cur ? "done" : me === cur ? "active" : "";
    },
    async poll() {
      const d = await getJSON(`/find/log.json?after=${this.total}`);
      if (d.total < this.total) { this.lines = []; this.total = 0; this.counts = zero(); return this.poll(); }
      const box = this.$refs.feed, stick = nearBottom(box);
      for (const l of d.lines) { this.lines.push(l); if (l.tag in this.counts) this.counts[l.tag]++; }
      this.total = d.total; this.phase = d.phase; this.activity = d.activity;
      if (this.busy && !d.busy) {            // run just ended → back to the initial state with a summary
        this.counts = zero(); this.phase = "starting"; this.activity = "Starting…";
        this.details = false; this.stopping = false;
      }
      this.busy = d.busy; this.summary = d.summary;
      if (stick && d.lines.length) this.$nextTick(() => toBottom(this.$refs.feed));
    },
    async start() {
      this.starting = true;
      await fetch("/find/run", { method: "POST" });
      this.lines = []; this.total = 0; this.counts = zero(); this.details = false;
      await this.poll(); this.starting = false;
    },
    async stop() { this.stopping = true; await fetch("/find/stop", { method: "POST" }); this.poll(); },
    jump() { toBottom(this.$refs.feed); this.follow = true; },
    init() { this.poll(); setInterval(() => this.poll(), 1500); },
  };
}

// Tracker: per-row status change / delete, plus bulk actions on selected rows.
function trackerActs(ids) {
  return {
    ids, sel: [], bulk: "",
    async apply(list, status) {
      if (!list.length || !status) return;
      if (status === "delete" && !confirm(`Delete ${list.length} job(s) from the tracker? This can't be undone.`)) return;
      await postForm("/tracker/update", { ids: list.join(","), status });
      location.reload();
    },
  };
}

// Live agents: worker cards with incremental logs + orchestrator chat.
function agentsApp() {
  return {
    state: { workers: [], running: false, queued: 0, history: [] }, logs: {}, after: {}, jobOf: {}, follow: {},
    open: {}, hist: {},
    async toggle(id) {
      this.open[id] = !this.open[id];
      if (this.open[id] && !this.hist[id]) this.hist[id] = await getJSON(`/agents/events?job=${id}`);
    },
    chat: [], chatAfter: 0, chatBusy: false, msg: "", sending: false,
    async poll() {
      this.state = await getJSON("/agents/state");
      for (const w of this.state.workers) {
        const job = w.job ? w.job.id : w.last_job;
        if (!job) { this.logs[w.n] = []; this.jobOf[w.n] = null; this.after[w.n] = 0; continue; }   // idle: reset
        if (this.jobOf[w.n] !== job) { this.jobOf[w.n] = job; this.logs[w.n] = []; this.after[w.n] = 0; this.follow[w.n] = true; }
        const box = document.getElementById("log-" + w.n);
        const stick = nearBottom(box);
        const evs = await getJSON(`/agents/events?job=${job}&after=${this.after[w.n] || 0}`);
        if (evs.length) {
          this.logs[w.n] = [...(this.logs[w.n] || []), ...evs].slice(-400);
          this.after[w.n] = evs[evs.length - 1].id;
          if (stick) this.$nextTick(() => toBottom(document.getElementById("log-" + w.n)));
        }
        this.follow[w.n] = stick;
      }
    },
    async pollChat() {
      const box = this.$refs.chat; const stick = nearBottom(box);
      const d = await getJSON(`/chat.json?after=${this.chatAfter}`);
      if (d.messages.length) { this.chat.push(...d.messages); this.chatAfter = d.messages[d.messages.length - 1].id; }
      this.chatBusy = d.busy;
      if (stick || d.messages.length) this.$nextTick(() => toBottom(box));
    },
    async send() {
      const t = this.msg.trim(); if (!t || this.chatBusy) return;
      this.sending = true; this.msg = "";
      await postForm("/chat", { text: t }); this.sending = false; this.pollChat();
    },
    async resetChat() { if (!confirm("Clear the conversation?")) return; await postForm("/chat/reset"); this.chat = []; this.chatAfter = 0; },
    async act(action) {
      if (action === "stop" && !confirm("Stop all workers now? Their jobs go back to the queue.")) return;
      await fetch(`/agents/${action}`, { method: "POST" }); this.poll();
    },
    async kill(n) { if (!confirm(`Stop worker ${n}?`)) return; await fetch(`/agents/kill/${n}`, { method: "POST" }); this.poll(); },
    async show(n) { await postForm(`/browser/open/${n}`, { next: "/agents" }); },
    jump(n) { toBottom(document.getElementById("log-" + n)); this.follow[n] = true; },
    tokens(s) { s = s || {}; return (s.input || 0) + (s.output || 0) + (s.cache_read || 0) + (s.cache_write || 0); },
    tok(n) { n = n || 0; return n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(1) + "k" : String(n); },
    dur(s) { if (!s) return "—"; const m = Math.floor(s / 60); return m ? `${m}m ${String(s % 60).padStart(2, "0")}s` : `${s}s`; },
    needsYou(c) { return (c["ready-for-review"] || 0) + (c["pending-user"] || 0); },
    async dismiss() { await fetch("/agents/dismiss-summary", { method: "POST" }); this.poll(); },
    elapsed(s) { return s ? `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, "0")}s` : ""; },
    time(ts) { return (ts || "").slice(11, 19); },
    init() {
      this.poll(); this.pollChat();
      setInterval(() => this.poll(), 2000); setInterval(() => this.pollChat(), 2500);
    },
  };
}
