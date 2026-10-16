"use strict";

// ------------------------------------------------------------------ helpers
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const enc = encodeURIComponent;
// Listing data comes from third parties: only ever link to http(s) URLs.
const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : "#");

async function api(path, opts = {}) {
  // The server rejects writes without this header, which stops other websites from posting to it.
  const init = { method: opts.method || "GET", headers: { "X-JobBot": "1" } };
  if (opts.body instanceof FormData) init.body = opts.body;
  else if (opts.body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(opts.body);
  }
  const r = await fetch(path, init);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : r.statusText);
  return data;
}

let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 3200);
}

async function guard(fn) {
  try { return await fn(); } catch (e) { toast(e.message || String(e)); }
}

const SOURCE_LABELS = {
  greenhouse: "Greenhouse", lever: "Lever", ashby: "Ashby", remotive: "Remotive", remoteok: "Remote OK",
  jobicy: "Jobicy", himalayas: "Himalayas", arbeitnow: "Arbeitnow", themuse: "The Muse",
};
const DIRECT = new Set(["greenhouse", "lever", "ashby"]);
const STATUS = {
  new: ["New", ""], queued: ["Queued", "accent"], preparing: ["Filling…", "accent"],
  ready: ["Ready to submit", "good"], needs_input: ["Needs you", "warn"], blocked: ["Blocked", "warn"],
  manual: ["Apply on site", ""], submitting: ["Submitting…", "accent"], applied: ["Applied", "good"],
  unconfirmed: ["Unconfirmed", "warn"], error: ["Error", "bad"], skipped: ["Skipped", ""], duplicate: ["Duplicate", ""],
};
const SOURCE_KIND = {
  profile: ["Profile", ""], bank: ["Answer bank", "accent"], user: ["You", "good"], ai: ["AI", "ai"],
  file: ["File", ""], human: ["Needs you", "warn"], skip: ["Left blank", ""], "": ["—", ""],
};

const statusChip = (s) => { const [t, c] = STATUS[s] || [s, ""]; return `<span class="chip ${c}">${esc(t)}</span>`; };
const sourceChip = (s) => { const [t, c] = SOURCE_KIND[s] || [s, ""]; return `<span class="chip ${c}">${esc(t)}</span>`; };
function scoreBox(n) {
  n = Math.round(n || 0);
  return `<div class="score ${n >= 75 ? "high" : n >= 55 ? "mid" : ""}" title="Match score">${n}</div>`;
}
function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 90) return "just now";
  if (s < 3600) return `${Math.round(s / 60)}m ago`;
  if (s < 86400) return `${Math.round(s / 3600)}h ago`;
  return `${Math.round(s / 86400)}d ago`;
}
const fmtTime = (iso) => (iso ? new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "");

// ------------------------------------------------------------------ global state
let STATE = null;
let onState = null;

async function refreshState() {
  try { STATE = await api("/api/state"); } catch { return; }
  const c = STATE.counts;
  $("#nav-new").textContent = c.new || "";
  const review = (c.ready || 0) + (c.needs_input || 0) + (c.blocked || 0) + (c.unconfirmed || 0);
  $("#nav-review").textContent = review || "";
  $("#nav-applied").textContent = c.applied || "";
  const a = STATE.automation;
  const pill = $("#auto-pill");
  if (a.enabled) {
    const next = STATE.next_run_sec;
    pill.className = "pill good";
    pill.textContent = next != null ? `Auto on · next search in ${next > 3600 ? Math.round(next / 3600) + "h" : Math.max(1, Math.round(next / 60)) + "m"}` : "Auto on";
  } else {
    pill.className = "pill";
    pill.textContent = "Automation off";
  }
  const q = STATE.queue;
  $("#worker-status").textContent = q.current
    ? `Working: ${q.current[1] === "submit" ? "submitting" : "filling"} 1 application${q.pending.length ? `, ${q.pending.length} waiting` : ""}`
    : q.pending.length ? `${q.pending.length} waiting` : "Idle";
  const btn = $("#btn-search");
  btn.disabled = STATE.search_running;
  btn.textContent = STATE.search_running ? "Searching…" : "Search now";
  if (onState) onState(STATE);
}

$("#btn-search").addEventListener("click", () => guard(async () => {
  const r = await api("/api/search", { method: "POST", body: { force: true } });
  toast(r.started ? "Searching all sources…" : r.reason);
  refreshState();
}));

// ------------------------------------------------------------------ job rows
function jobRow(j, { select = false } = {}) {
  const direct = DIRECT.has(j.ats);
  const canFill = ["new", "error", "blocked", "needs_input", "manual"].includes(j.status) && j.ats !== "manual";
  return `<div class="job" data-id="${esc(j.id)}">
    ${select ? `<input type="checkbox" class="sel" aria-label="Select ${esc(j.title)}">` : ""}
    ${scoreBox(j.score)}
    <div class="main">
      <div class="title">${esc(j.title)}</div>
      <div class="meta">
        <strong>${esc(j.company)}</strong>
        ${j.location ? `<span>${esc(j.location.slice(0, 60))}</span>` : ""}
        ${j.salary_text ? `<span>${esc(j.salary_text)}</span>` : ""}
        ${j.posted_at ? `<span>${ago(j.posted_at)}</span>` : ""}
        <span>via ${esc(SOURCE_LABELS[j.source] || j.source)}</span>
        ${direct ? `<span class="chip accent" title="JobBot can fill and submit this form">Direct apply</span>` : ""}
        ${j.status !== "new" ? statusChip(j.status) : ""}
      </div>
      ${j.status_note && !["new", "skipped", "duplicate"].includes(j.status) ? `<div class="small muted">${esc(j.status_note)}</div>` : ""}
    </div>
    <div class="actions">
      ${canFill ? `<button class="btn sm" data-act="prepare">${j.status === "new" ? "Fill" : "Fill again"}</button>` : ""}
      ${j.status === "ready" ? `<button class="btn sm primary" data-act="submit">Submit</button>` : ""}
      ${j.status === "new" ? `<button class="btn sm" data-act="skip">Skip</button>` : ""}
    </div>
  </div>`;
}

function bindJobList(container, reload) {
  container.addEventListener("click", (e) => {
    const row = e.target.closest(".job");
    if (!row || e.target.matches("input.sel")) return;
    const act = e.target.closest("[data-act]");
    if (act) {
      e.stopPropagation();
      guard(async () => { if (await doAction(row.dataset.id, act.dataset.act)) reload && reload(); });
      return;
    }
    openJob(row.dataset.id);
  });
}

const ACTION_MSG = {
  prepare: "Queued: filling the application (nothing is sent)", submit: "Queued: submitting the application",
  skip: "Skipped", restore: "Moved back to New", mark_applied: "Marked as applied", manual: "Marked to apply on the company site",
};

async function doAction(id, action) {
  if (action === "submit" && !confirm("Submit this application now?\n\nJobBot will fill the form with the answers you reviewed and press Submit on the employer's site.")) return false;
  await api(`/api/jobs/${enc(id)}/action`, { method: "POST", body: { action } });
  toast(ACTION_MSG[action] || "Done");
  refreshState();
  return true;
}

// ------------------------------------------------------------------ views
const TITLES = {
  dashboard: "Dashboard", jobs: "Jobs", review: "Review queue", applied: "Applied", profile: "Profile",
  answers: "Answer bank", search: "Search setup", settings: "Automation & AI", activity: "Activity",
};

async function viewDashboard(el) {
  await refreshState();
  const s = STATE, c = s.counts, setup = s.setup;
  const steps = [
    [setup.profile, "Fill in your profile", "#/profile", "Name, contact details, work authorization."],
    [setup.resume, "Upload your resume", "#/profile", "Attached to every application."],
    [setup.keywords, "Choose job titles to search for", "#/search", ""],
    [setup.companies, "Add companies to watch", "#/search", "Their Greenhouse, Lever or Ashby boards can be applied to directly."],
    [setup.automation, "Turn on automation", "#/settings", "Searches on a schedule and fills applications for you."],
  ];
  const [top, events] = await Promise.all([api("/api/jobs?status=new&limit=6&sort=score"), api("/api/events?limit=10")]);
  const needs = (c.needs_input || 0) + (c.blocked || 0) + (c.unconfirmed || 0);
  const tile = (n, label, href) => `<a class="tile" href="${href}"><div class="num">${esc(n)}</div><div class="label">${esc(label)}</div></a>`;
  const done = steps.filter((x) => x[0]).length;
  el.innerHTML = `
    ${done === steps.length ? "" : `<div class="card" style="margin-bottom:16px">
      <div class="card-head"><h2>Get set up</h2><span class="muted small">${done} of ${steps.length} done</span></div>
      <ul class="checklist">${steps.map(([ok, t, href, hint]) => `<li><span class="dot ${ok ? "done" : ""}">${ok ? "✓" : ""}</span>
        <div><a href="${href}">${esc(t)}</a> <span class="muted small">${esc(hint)}</span></div></li>`).join("")}</ul></div>`}
    <div class="tiles">
      ${tile(c.new || 0, "New matches", "#/jobs")}
      ${tile(c.ready || 0, "Ready to submit", "#/review")}
      ${tile(needs, "Need your input", "#/review")}
      ${tile(s.applied_7d, "Applied this week", "#/applied")}
      ${tile(`${s.applied_24h} / ${s.daily_limit}`, "Today / daily limit", "#/settings")}
    </div>
    <div class="grid grid-2" style="margin-top:16px">
      <div class="card">
        <div class="card-head"><h2>Top new matches</h2><a href="#/jobs">All jobs →</a></div>
        <div class="job-list" id="top">${top.jobs.length ? top.jobs.map((j) => jobRow(j)).join("")
          : `<div class="empty">No new matches yet.<br>Set your <a href="#/search">search</a>, then press <b>Search now</b>.</div>`}</div>
      </div>
      <div class="stack">
        <div class="card">
          <div class="card-head"><h2>Run it</h2><span class="chip ${s.automation.enabled ? "good" : ""}">${s.automation.enabled ? "Automation on" : "Automation off"}</span></div>
          <p class="muted small" style="margin-top:0">Search every enabled source, then fill the best matches so they're waiting in your review queue.
            ${s.automation.auto_submit ? "<b>Auto-submit is on</b> for direct-apply jobs scoring " + s.automation.submit_min_score + "+." : "Nothing is submitted until you press Submit."}</p>
          <div class="btn-row">
            <button class="btn primary" id="run-all">Search &amp; fill top matches</button>
            <button class="btn" id="clear-q">Clear queue</button>
          </div>
          <div class="small muted" id="queue-line" style="margin-top:10px"></div>
        </div>
        <div class="card">
          <div class="card-head"><h2>Recent activity</h2><a href="#/activity">All →</a></div>
          ${eventList(events)}
        </div>
      </div>
    </div>`;
  bindJobList($("#top", el), () => route());
  $("#run-all", el).onclick = () => guard(async () => {
    const r = await api("/api/search", { method: "POST", body: { force: true, queue: true } });
    toast(r.started ? "Searching; top matches will be filled next" : r.reason);
    refreshState();
  });
  $("#clear-q", el).onclick = () => guard(async () => { const r = await api("/api/queue/clear", { method: "POST" }); toast(`Removed ${r.cleared} from the queue`); });
  onState = (st) => {
    const q = st.queue;
    const line = $("#queue-line");
    if (line) line.textContent = st.search_running ? "Searching job boards…" : q.current ? `Working on 1 application, ${q.pending.length} waiting.` : q.pending.length ? `${q.pending.length} waiting.` : "Queue is empty.";
  };
  onState(STATE);
}

function eventList(events) {
  if (!events.length) return `<div class="empty">Nothing yet.</div>`;
  return `<ul class="events">${events.map((e) => `<li class="${esc(e.level)}"><time>${fmtTime(e.ts)}</time>
    <span class="msg">${e.job_id ? `<a href="#" data-job="${esc(e.job_id)}">${esc(e.message)}</a>` : esc(e.message)}</span></li>`).join("")}</ul>`;
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("a[data-job]");
  if (a) { e.preventDefault(); openJob(a.dataset.job); }
});

async function viewJobs(el) {
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  const sources = await api("/api/sources");
  el.innerHTML = `
    <div class="filters">
      <input type="search" id="f-q" placeholder="Search title, company, location" aria-label="Search">
      <select id="f-status" aria-label="Status">
        <option value="new">New</option><option value="queued,preparing,submitting">In progress</option>
        <option value="ready">Ready to submit</option><option value="needs_input,blocked,error">Needs you</option>
        <option value="applied,unconfirmed">Applied</option><option value="manual">Apply on site</option>
        <option value="skipped,duplicate">Skipped</option><option value="">All</option>
      </select>
      <select id="f-source" aria-label="Source"><option value="">All sources</option>
        ${sources.map((s) => `<option value="${esc(s.name)}">${esc(s.label)}</option>`).join("")}</select>
      <select id="f-min" aria-label="Minimum score"><option value="">Any score</option><option value="50">50+</option>
        <option value="60">60+</option><option value="70">70+</option><option value="80">80+</option></select>
      <select id="f-sort" aria-label="Sort"><option value="score">Best match</option><option value="newest">Newest</option><option value="company">Company</option></select>
      <label class="check"><input type="checkbox" id="f-direct"> Direct apply only</label>
    </div>
    <div class="btn-row" style="margin-bottom:10px">
      <button class="btn sm" id="sel-all">Select all</button>
      <button class="btn sm" id="bulk-prepare">Fill selected</button>
      <button class="btn sm" id="bulk-skip">Skip selected</button>
      <span class="muted small" id="total"></span>
    </div>
    <div class="job-list" id="list"></div>
    <div style="text-align:center;margin-top:12px"><button class="btn" id="more" hidden>Load more</button></div>`;
  if (params.get("status") !== null) $("#f-status").value = params.get("status");
  let offset = 0;
  const list = $("#list", el);
  async function load(reset = true) {
    if (reset) offset = 0;
    const qs = new URLSearchParams({
      status: $("#f-status").value, q: $("#f-q").value, source: $("#f-source").value,
      sort: $("#f-sort").value, limit: 50, offset,
    });
    if ($("#f-min").value) qs.set("min_score", $("#f-min").value);
    if ($("#f-direct").checked) qs.set("ats_filter", "any");
    const r = await api(`/api/jobs?${qs}`);
    const html = r.jobs.map((j) => jobRow(j, { select: true })).join("");
    if (reset) list.innerHTML = html || `<div class="empty">No jobs here. Try another filter, or press <b>Search now</b>.</div>`;
    else list.insertAdjacentHTML("beforeend", html);
    offset += r.jobs.length;
    $("#total").textContent = `${r.total} job${r.total === 1 ? "" : "s"}`;
    $("#more").hidden = offset >= r.total;
  }
  let t;
  $("#f-q").addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => load(), 250); });
  $$("#f-status, #f-source, #f-min, #f-sort, #f-direct", el).forEach((x) => x.addEventListener("change", () => load()));
  $("#more").onclick = () => load(false);
  $("#sel-all").onclick = () => { const boxes = $$("input.sel", list); const on = boxes.some((b) => !b.checked); boxes.forEach((b) => (b.checked = on)); };
  const selected = () => $$("input.sel:checked", list).map((b) => b.closest(".job").dataset.id);
  $("#bulk-prepare").onclick = () => guard(async () => {
    const ids = selected(); if (!ids.length) return toast("Select some jobs first");
    await api("/api/bulk", { method: "POST", body: { ids, action: "prepare" } });
    toast(`Queued ${ids.length} to fill`); load();
  });
  $("#bulk-skip").onclick = () => guard(async () => {
    const ids = selected(); if (!ids.length) return toast("Select some jobs first");
    await api("/api/bulk", { method: "POST", body: { ids, action: "skip" } });
    toast(`Skipped ${ids.length}`); load();
  });
  bindJobList(list, () => load());
  let lastCounts = "";
  onState = (st) => { const k = JSON.stringify(st.counts); if (lastCounts && k !== lastCounts && !st.search_running) load(); lastCounts = k; };
  await load();
}

async function viewReview(el) {
  const tabs = [
    ["ready", "Ready to submit", "Filled and checked. Review the answers, then submit."],
    ["needs_input,blocked", "Needs you", "Questions JobBot couldn't answer, CAPTCHAs, or sites that need you."],
    ["unconfirmed,error", "Unconfirmed & errors", "Submitted without a clear confirmation, or something went wrong."],
    ["queued,preparing,submitting", "In progress", "Waiting for, or being handled by, the browser worker."],
  ];
  const st0 = STATE || (await api("/api/state"));
  const countOf = (k, st) => k.split(",").reduce((a, s) => a + (st.counts[s] || 0), 0);
  let active = new URLSearchParams(location.hash.split("?")[1] || "").get("tab")
    || (tabs.find(([k]) => countOf(k, st0)) || tabs[0])[0];
  el.innerHTML = `<div class="tabs" role="tablist">${tabs.map(([k, t]) => `<button role="tab" data-tab="${k}">${esc(t)} <span class="count" data-count="${k}"></span></button>`).join("")}</div>
    <p class="muted small" id="tab-help"></p>
    <div class="btn-row" style="margin-bottom:10px" id="tab-actions"></div>
    <div class="job-list" id="list"></div>`;
  const list = $("#list", el);
  async function load() {
    $$(".tabs button", el).forEach((b) => b.classList.toggle("active", b.dataset.tab === active));
    $("#tab-help").textContent = tabs.find((t) => t[0] === active)[2];
    const r = await api(`/api/jobs?status=${enc(active)}&sort=updated&limit=200`);
    list.innerHTML = r.jobs.map((j) => jobRow(j)).join("") || `<div class="empty">Nothing here right now.</div>`;
    $("#tab-actions").innerHTML = active === "ready" && r.jobs.length
      ? `<button class="btn primary" id="submit-all">Submit all ${r.jobs.length}</button>` : "";
    const sa = $("#submit-all");
    if (sa) sa.onclick = () => guard(async () => {
      if (!confirm(`Submit ${r.jobs.length} applications now? Each one is filled again and submitted on the employer's site.`)) return;
      await api("/api/bulk", { method: "POST", body: { ids: r.jobs.map((j) => j.id), action: "submit" } });
      toast(`Queued ${r.jobs.length} to submit`); load();
    });
  }
  $$(".tabs button", el).forEach((b) => (b.onclick = () => { active = b.dataset.tab; load(); }));
  bindJobList(list, load);
  let last = "";
  onState = (st) => {
    for (const [k] of tabs) {
      const c = $(`[data-count="${k}"]`); if (c) c.textContent = countOf(k, st) || "";
    }
    const key = JSON.stringify(st.counts);
    if (last && key !== last) load();
    last = key;
  };
  onState(st0);
  await load();
}

async function viewApplied(el) {
  const r = await api("/api/jobs?status=applied,unconfirmed&sort=updated&limit=500");
  el.innerHTML = r.jobs.length ? `<div class="card"><table>
      <thead><tr><th>Applied</th><th>Job</th><th>Company</th><th>Status</th><th></th></tr></thead>
      <tbody>${r.jobs.map((j) => `<tr>
        <td class="small">${fmtTime(j.applied_at)}</td>
        <td><a href="#" data-job="${esc(j.id)}">${esc(j.title)}</a></td>
        <td>${esc(j.company)}</td><td>${statusChip(j.status)}</td>
        <td><a href="${esc(safeUrl(j.url))}" target="_blank" rel="noopener">Listing ↗</a></td></tr>`).join("")}</tbody></table></div>`
    : `<div class="empty">No applications yet. Submitted applications show up here.</div>`;
}

async function viewActivity(el) {
  const events = await api("/api/events?limit=300");
  el.innerHTML = `<div class="card">${eventList(events)}</div>`;
}

// ------------------------------------------------------------------ job drawer
function closeDrawer() {
  $("#drawer").hidden = true;
  $("#drawer-backdrop").hidden = true;
  drawerJob = null;
}
$("#drawer-backdrop").onclick = closeDrawer;
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("#drawer").hidden) closeDrawer(); });
let drawerJob = null;
let drawerStatus = null;

function answerInput(m, i, value) {
  const name = `a${i}`;
  const opts = m.options || [];
  if (m.kind === "file") return `<a class="small" href="#/profile">Upload it in Profile →</a>`;
  if (m.kind === "checkboxes" && opts.length) {
    const sel = new Set(Array.isArray(value) ? value : []);
    return `<div class="tags">${opts.map((o) => `<label class="check"><input type="checkbox" name="${name}" value="${esc(o)}" ${sel.has(o) ? "checked" : ""}> ${esc(o)}</label>`).join("")}</div>`;
  }
  if (["select", "radio", "buttons", "combobox"].includes(m.kind) && opts.length)
    return `<select name="${name}"><option value="">Choose…</option>${opts.map((o) => `<option ${o === value ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
  if (m.kind === "checkbox") return `<select name="${name}"><option value="">Choose…</option><option ${value === "Yes" ? "selected" : ""}>Yes</option><option ${value === "No" ? "selected" : ""}>No</option></select>`;
  if (m.kind === "textarea") return `<textarea name="${name}">${esc(value || "")}</textarea>`;
  return `<input type="text" name="${name}" value="${esc(value || "")}">`;
}

function collectAnswers(form, items) {
  const out = {};
  items.forEach((m, i) => {
    const els = $$(`[name="a${i}"]`, form);
    if (!els.length) return;
    let v;
    if (els[0].type === "checkbox") v = els.filter((x) => x.checked).map((x) => x.value);
    else v = els[0].value.trim();
    if (v && (!Array.isArray(v) || v.length)) out[m.label] = v;
  });
  return out;
}

async function openJob(id) {
  const j = await guard(() => api(`/api/jobs/${enc(id)}/detail`));
  if (!j) return;
  drawerJob = id;
  drawerStatus = j.status;
  const latest = j.attempts[0];
  const withFields = j.attempts.find((a) => (a.fields || []).length);
  const missingQs = latest && ["needs_input", "blocked"].includes(j.status) ? latest.missing || [] : [];
  const busy = ["queued", "preparing", "submitting"].includes(j.status) || j.in_queue;
  const direct = DIRECT.has(j.ats);
  const canFill = !busy && !["applied"].includes(j.status) && j.ats !== "manual";
  const d = $("#drawer");
  d.innerHTML = `
    <div class="drawer-head">
      <button class="btn sm close" id="d-close" aria-label="Close">✕</button>
      <h2 style="padding-right:40px">${esc(j.title)}</h2>
      <div class="muted">${esc(j.company)}${j.location ? " · " + esc(j.location) : ""}${j.salary_text ? " · " + esc(j.salary_text) : ""}</div>
      <div class="btn-row" style="margin-top:8px">
        ${statusChip(j.status)}
        <span class="chip">Score ${Math.round(j.score || 0)}</span>
        ${direct ? `<span class="chip accent">Direct apply (${esc(SOURCE_LABELS[j.ats])})</span>` : j.ats === "generic" ? `<span class="chip warn">Unrecognised form, review before submitting</span>` : j.ats === "manual" ? `<span class="chip">Apply on the company site</span>` : ""}
        ${j.url ? `<a href="${esc(safeUrl(j.url))}" target="_blank" rel="noopener">View listing on ${esc(SOURCE_LABELS[j.source] || j.source)} ↗</a>` : ""}
        ${j.apply_url && j.apply_url !== j.url ? `<a href="${esc(safeUrl(j.apply_url))}" target="_blank" rel="noopener">Application form ↗</a>` : ""}
      </div>
    </div>
    <div class="drawer-body stack">
      ${j.status_note ? `<div class="notice ${{ ready: "good", applied: "good", needs_input: "warn", blocked: "warn", unconfirmed: "warn", error: "bad" }[j.status] || ""}">${esc(j.status_note)}</div>` : ""}
      <div class="btn-row">
        ${canFill ? `<button class="btn ${j.status === "ready" ? "" : "primary"}" data-act="prepare">${latest ? "Fill again" : "Fill application"}</button>` : ""}
        ${j.status === "ready" ? `<button class="btn primary" data-act="submit">Submit application</button>` : ""}
        ${["needs_input", "blocked"].includes(j.status) && latest && STATE && !STATE.automation.headless ? `<button class="btn" data-act="submit" title="Opens the form in a browser window so you can finish it">Finish in browser window</button>` : ""}
        ${j.status === "error" && latest ? `<button class="btn" data-act="submit">Retry submit</button>` : ""}
        ${j.status !== "applied" ? `<button class="btn" data-act="mark_applied">I applied myself</button>` : ""}
        ${["new", "ready", "needs_input", "blocked", "error", "manual"].includes(j.status) ? `<button class="btn danger" data-act="skip">Skip</button>` : ""}
        ${["skipped", "duplicate", "manual"].includes(j.status) ? `<button class="btn" data-act="restore">Move back to New</button>` : ""}
        ${busy ? `<span class="muted small">Working on it…</span>` : ""}
      </div>
      ${missingQs.length ? `<form class="card" id="missing-form">
        <div class="card-head"><h3>${missingQs.length} question${missingQs.length > 1 ? "s" : ""} need${missingQs.length > 1 ? "" : "s"} you</h3></div>
        <div class="stack">${missingQs.map((m, i) => `<label class="field">${esc(m.label)}
          ${m.note && m.kind !== "file" ? `<span class="hint">${esc(m.note)}</span>` : ""}${answerInput(m, i, null)}</label>`).join("")}</div>
        ${missingQs.some((m) => m.kind !== "file") ? `<div class="btn-row" style="margin-top:14px">
          <button class="btn primary" type="submit">Save &amp; fill again</button>
          <label class="check small"><input type="checkbox" name="remember" checked> Remember these answers for future applications</label>
        </div>` : ""}</form>` : ""}
      ${withFields ? `<div class="card">
        <div class="card-head"><h3>Answers ${withFields === latest ? "" : "(from an earlier fill)"}</h3>
          <button class="btn sm" id="edit-answers">Edit answers</button></div>
        <form id="answers-form"><table><thead><tr><th style="width:45%">Question</th><th>Answer</th><th>From</th></tr></thead><tbody>
        ${withFields.fields.map((f, i) => `<tr><td>${esc(f.label || "(unlabeled)")}${f.required ? ' <span class="muted">*</span>' : ""}</td>
          <td class="answer" data-i="${i}">${f.answer == null || (Array.isArray(f.answer) && !f.answer.length) ? '<span class="muted">—</span>' : esc(Array.isArray(f.answer) ? f.answer.join(", ") : f.answer)}
            ${f.note ? `<div class="small muted">${esc(f.note)}</div>` : ""}</td>
          <td>${sourceChip(f.source)}${f.required && !f.resolved ? ' <span class="chip warn">missing</span>' : ""}</td></tr>`).join("")}
        </tbody></table>
        <div class="btn-row" id="edit-save" hidden style="margin-top:12px"><button class="btn primary" type="submit">Save &amp; fill again</button>
          <label class="check small"><input type="checkbox" name="remember"> Also save to answer bank</label></div></form>
      </div>` : ""}
      ${latest && latest.screenshot ? `<div class="card"><div class="card-head"><h3>What the form looked like</h3>
          <span class="small muted">${esc(latest.kind)} · ${fmtTime(latest.finished_at || latest.started_at)}</span></div>
        <a href="/shots/${enc(latest.screenshot)}" target="_blank" rel="noopener"><img class="shot" src="/shots/${enc(latest.screenshot)}" alt="Screenshot of the filled application form"></a></div>` : ""}
      ${(j.score_reasons || []).length ? `<div class="card"><h3 class="section-title">Why it matched</h3><ul style="margin:0;padding-left:18px">${j.score_reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul></div>` : ""}
      ${j.description ? `<div class="card"><h3 class="section-title">Description</h3><div class="desc">${esc(j.description)}</div></div>` : ""}
      ${j.attempts.length ? `<div class="card"><h3 class="section-title">History</h3><table><tbody>${j.attempts.map((a) => `<tr>
        <td class="small">${fmtTime(a.started_at)}</td><td>${a.kind === "submit" ? "Submit" : "Fill"}</td><td>${statusChip(a.result)}</td><td class="small">${esc(a.message || "")}</td></tr>`).join("")}</tbody></table></div>` : ""}
    </div>`;
  d.hidden = false;
  $("#drawer-backdrop").hidden = false;
  $("#d-close").onclick = closeDrawer;
  $$("[data-act]", d).forEach((b) => (b.onclick = () => guard(async () => {
    if (await doAction(id, b.dataset.act)) { openJob(id); if (currentView !== "dashboard") route(); }
  })));
  const mf = $("#missing-form");
  if (mf) mf.onsubmit = (e) => {
    e.preventDefault();
    guard(async () => {
      const answers = collectAnswers(mf, missingQs);
      if (!Object.keys(answers).length) return toast("Answer at least one question");
      await api(`/api/jobs/${enc(id)}/answers`, { method: "POST", body: { answers, remember: mf.remember.checked } });
      toast("Saved. Filling the form again…");
      openJob(id);
    });
  };
  const eb = $("#edit-answers");
  if (eb) eb.onclick = () => {
    const form = $("#answers-form");
    withFields.fields.forEach((f, i) => {
      const cell = $(`td[data-i="${i}"]`, form);
      if (f.kind === "file" || f.source === "skip") return;
      cell.innerHTML = answerInput(f, i, f.answer);
    });
    $("#edit-save").hidden = false;
    eb.hidden = true;
    form.onsubmit = (e) => {
      e.preventDefault();
      guard(async () => {
        const all = collectAnswers(form, withFields.fields);
        const changed = {};
        withFields.fields.forEach((f) => {
          const v = all[f.label];
          if (v !== undefined && JSON.stringify(v) !== JSON.stringify(f.answer)) changed[f.label] = v;
        });
        if (!Object.keys(changed).length) return toast("Nothing changed");
        await api(`/api/jobs/${enc(id)}/answers`, { method: "POST", body: { answers: changed, remember: form.remember.checked } });
        toast("Saved. Filling the form again…");
        openJob(id);
      });
    };
  };
}

// Keep an open drawer fresh while the worker is busy with that job.
setInterval(() => {
  if (!drawerJob || $("#drawer").hidden) return;
  if (["queued", "preparing", "submitting"].includes(drawerStatus)) {
    api(`/api/jobs/${enc(drawerJob)}/detail`).then((j) => { if (j.status !== drawerStatus) openJob(drawerJob); }).catch(() => {});
  }
}, 3000);

// ------------------------------------------------------------------ profile
const PROFILE_SECTIONS = [
  ["Contact", [["first_name", "First name"], ["last_name", "Last name"], ["preferred_name", "Preferred name"], ["pronouns", "Pronouns"],
    ["email", "Email", "email"], ["phone", "Phone", "tel"]]],
  ["Location", [["city", "City"], ["state", "State / region"], ["postal_code", "ZIP / postal code"], ["country", "Country"],
    ["address", "Street address", "text", "", "wide"]]],
  ["Links", [["linkedin", "LinkedIn URL", "url"], ["github", "GitHub URL", "url"], ["website", "Website / portfolio", "url"], ["twitter", "X / Twitter", "url"]]],
  ["Experience", [["current_company", "Current or most recent employer"], ["current_title", "Current or most recent title"],
    ["years_experience", "Years of experience", "number"], ["skills", "Skills", "textarea", "Comma-separated. Used to rank jobs, e.g. Python, AWS, React."],
    ["summary", "Short professional summary", "textarea", "One or two sentences. Used in your cover letter template.", "wide"]]],
  ["Education", [["school", "School"], ["degree", "Highest degree", "text", "e.g. Bachelor's, Master's, PhD"], ["discipline", "Field of study"], ["graduation_year", "Graduation year"]]],
  ["Work eligibility & preferences", [
    ["work_authorized", "I'm legally authorized to work in the countries I'm applying to", "bool"],
    ["needs_sponsorship", "I need (or will need) visa sponsorship", "bool"],
    ["willing_to_relocate", "I'm willing to relocate", "bool"],
    ["remote_preference", "Work style", "select", "", "", [["any", "Open to remote, hybrid or on-site"], ["remote", "Remote"], ["hybrid", "Hybrid"], ["onsite", "On-site"]]],
    ["salary_expectation", "Salary expectation", "text", "Typed into salary questions, e.g. $150,000"],
    ["availability", "Availability / notice period"], ["how_heard", "How you found the job", "text", "Used for 'How did you hear about us?'"],
    ["languages", "Languages", "text", "Comma-separated"]]],
  ["Voluntary self-identification", [
    ["eeo_gender", "Gender", "eeo"], ["eeo_race", "Race / ethnicity", "eeo"], ["eeo_hispanic", "Hispanic or Latino", "eeo"],
    ["eeo_veteran", "Veteran status", "eeo"], ["eeo_disability", "Disability status", "eeo"]],
    "“decline” picks the “I don't wish to answer” option. Type something else (e.g. Female, No) to answer instead."],
  ["Consents", [
    ["accept_privacy_terms", "Tick required privacy-notice and acknowledgement boxes", "bool"],
    ["marketing_opt_in", "Opt in to recruiting texts, WhatsApp and newsletters", "bool"]]],
];

function fieldHtml([key, label, type = "text", hint = "", cls = "", options], value) {
  const h = hint ? `<span class="hint">${esc(hint)}</span>` : "";
  if (type === "bool") return `<label class="check ${cls} wide"><input type="checkbox" name="${key}" ${value ? "checked" : ""}> ${esc(label)}</label>`;
  if (type === "textarea") return `<label class="field ${cls || "wide"}">${esc(label)}${h}<textarea name="${key}">${esc(value)}</textarea></label>`;
  if (type === "select") return `<label class="field ${cls}">${esc(label)}${h}<select name="${key}">${options.map(([v, t]) => `<option value="${v}" ${v === value ? "selected" : ""}>${esc(t)}</option>`).join("")}</select></label>`;
  if (type === "eeo") return `<label class="field ${cls}">${esc(label)}<input type="text" name="${key}" list="eeo-list" value="${esc(value)}"></label>`;
  return `<label class="field ${cls}">${esc(label)}${h}<input type="${type}" name="${key}" value="${esc(value)}"></label>`;
}

async function viewProfile(el) {
  const p = await api("/api/settings/profile");
  el.innerHTML = `<form id="pf" class="stack">
    <div class="card">
      <h2 class="section-title">Documents</h2>
      <div class="grid grid-2">
        <div><label class="field">Resume <span class="hint">PDF works best: JobBot reads it to rank jobs and to ground AI answers.</span>
          <input type="file" id="resume-file" accept=".pdf,.doc,.docx,.txt,.rtf,.odt"></label>
          <div class="small" style="margin-top:6px">${p.resume_file ? `Current: <b>${esc(p.resume_file)}</b> · ${p.resume_text ? `${p.resume_text.length.toLocaleString()} characters of text read` : "no text extracted (use a PDF for AI answers)"}` : '<span class="muted">No resume uploaded yet.</span>'}</div></div>
        <div><label class="field">Cover letter file <span class="hint">Optional. Used when a form asks for a cover letter upload.</span>
          <input type="file" id="cl-file" accept=".pdf,.doc,.docx,.txt,.rtf,.odt"></label>
          <div class="small" style="margin-top:6px">${p.cover_letter_file ? `Current: <b>${esc(p.cover_letter_file)}</b>` : '<span class="muted">None.</span>'}</div></div>
      </div>
    </div>
    ${PROFILE_SECTIONS.map(([title, fields, note]) => `<div class="card"><h2 class="section-title">${esc(title)}</h2>
      ${note ? `<p class="muted small" style="margin-top:-6px">${esc(note)}</p>` : ""}
      <div class="form-grid">${fields.map((f) => fieldHtml(f, p[f[0]] ?? "")).join("")}</div></div>`).join("")}
    <div class="card"><h2 class="section-title">Cover letter template</h2>
      <p class="muted small" style="margin-top:-6px">Typed into cover-letter text boxes. Placeholders: <code>{company}</code> <code>{title}</code> <code>{name}</code> <code>{summary}</code>. With AI turned on, a tailored letter is written instead.</p>
      <textarea name="cover_letter" style="min-height:180px">${esc(p.cover_letter)}</textarea></div>
    <datalist id="eeo-list"><option value="decline"></option></datalist>
    <div class="sticky-save"><button class="btn primary" type="submit">Save profile</button></div>
  </form>`;
  const form = $("#pf", el);
  form.onsubmit = (e) => {
    e.preventDefault();
    guard(async () => {
      const out = { ...p };
      for (const [, fields] of PROFILE_SECTIONS) for (const [key, , type] of fields) {
        const input = form.elements[key];
        out[key] = type === "bool" ? input.checked : input.value.trim();
      }
      out.cover_letter = form.elements.cover_letter.value;
      await api("/api/settings/profile", { method: "PUT", body: out });
      toast("Profile saved");
      refreshState();
    });
  };
  const upload = (input, kind) => input.addEventListener("change", () => guard(async () => {
    if (!input.files.length) return;
    const fd = new FormData();
    fd.append("file", input.files[0]);
    const r = await api(`/api/upload/${kind}`, { method: "POST", body: fd });
    toast(kind === "resume" ? `Resume saved${r.text_chars ? ` (${r.text_chars.toLocaleString()} characters read)` : ""}` : "Cover letter saved");
    route();
  }));
  upload($("#resume-file"), "resume");
  upload($("#cl-file"), "cover_letter");
}

async function viewAnswers(el) {
  let bank = await api("/api/settings/answers");
  function render() {
    el.innerHTML = `<div class="card">
      <p class="muted" style="margin-top:0">When a question's text contains a pattern below, JobBot uses your answer. These win over everything except answers you type for a specific job.
      Answers you give in the review screen can be saved here automatically.</p>
      <form id="bank"><table><thead><tr><th style="width:45%">Question contains</th><th>Your answer</th><th>Regex</th><th></th></tr></thead><tbody>
      ${bank.map((b, i) => `<tr><td><input type="text" name="q${i}" value="${esc(b.q)}"></td>
        <td><textarea name="a${i}" style="min-height:38px">${esc(b.a)}</textarea></td>
        <td><input type="checkbox" name="r${i}" ${b.regex ? "checked" : ""} aria-label="Pattern is a regular expression"></td>
        <td><button type="button" class="btn sm danger" data-del="${i}" aria-label="Delete">✕</button></td></tr>`).join("")}
      </tbody></table>
      <div class="btn-row" style="margin-top:12px"><button type="button" class="btn" id="add">Add answer</button><button class="btn primary" type="submit">Save answers</button></div></form></div>`;
    const form = $("#bank", el);
    const read = () => bank.map((b, i) => ({ q: form.elements[`q${i}`].value.trim(), a: form.elements[`a${i}`].value, regex: form.elements[`r${i}`].checked }));
    $("#add", el).onclick = () => { bank = read(); bank.push({ q: "", a: "", regex: false }); render(); $$("input[type=text]", el).pop().focus(); };
    $$("[data-del]", el).forEach((b) => (b.onclick = () => { bank = read(); bank.splice(+b.dataset.del, 1); render(); }));
    form.onsubmit = (e) => {
      e.preventDefault();
      guard(async () => {
        bank = read().filter((b) => b.q);
        for (const b of bank) if (b.regex) { try { new RegExp(b.q); } catch { throw new Error(`Invalid regex: ${b.q}`); } }
        await api("/api/settings/answers", { method: "PUT", body: bank });
        toast("Answers saved");
        render();
      });
    };
  }
  render();
}

// ------------------------------------------------------------------ search setup
async function viewSearch(el) {
  const [s, sources] = await Promise.all([api("/api/settings/search"), api("/api/sources")]);
  const lines = (a) => (a || []).join("\n");
  const ATS = [["greenhouse", "Greenhouse"], ["lever", "Lever"], ["ashby", "Ashby"]];
  el.innerHTML = `<form id="sf" class="stack">
    <div class="card"><h2 class="section-title">What you're looking for</h2>
      <div class="form-grid">
        <label class="field">Job titles <span class="hint">One per line. A job matches when every word of a line is in its title.</span><textarea name="keywords">${esc(lines(s.keywords))}</textarea></label>
        <label class="field">Exclude titles containing <span class="hint">One per line, e.g. intern, principal, manager</span><textarea name="exclude">${esc(lines(s.exclude))}</textarea></label>
        <label class="field">Locations <span class="hint">One per line. Include “Remote” to accept remote jobs.</span><textarea name="locations">${esc(lines(s.locations))}</textarea></label>
        <div class="stack">
          <label class="field">Remote / on-site<select name="remote">
            ${[["any", "Remote or on-site"], ["remote_only", "Remote only"], ["onsite_only", "On-site / hybrid only"]].map(([v, t]) => `<option value="${v}" ${s.remote === v ? "selected" : ""}>${t}</option>`).join("")}</select></label>
          <label class="field">Minimum salary (yearly) <span class="hint">Jobs that list lower pay are hidden. 0 = no minimum.</span><input type="number" name="min_salary" value="${esc(s.min_salary)}"></label>
          <label class="field">Ignore jobs older than (days)<input type="number" name="max_age_days" value="${esc(s.max_age_days)}"></label>
        </div>
      </div></div>
    <div class="card"><div class="card-head"><h2>Companies to watch</h2></div>
      <p class="muted small" style="margin-top:-6px">Company job boards on Greenhouse, Lever and Ashby are where JobBot can fill <i>and</i> submit applications. Add a company by name or paste a link to one of its job posts.</p>
      <div class="btn-row"><input type="text" id="co-name" placeholder="e.g. Stripe, Notion, or https://jobs.lever.co/…" style="max-width:420px"><button type="button" class="btn" id="co-add">Find &amp; add</button><span class="small muted" id="co-msg"></span></div>
      <div class="grid grid-3" style="margin-top:14px">${ATS.map(([k, t]) => `<div><h3 style="margin-bottom:6px">${t}</h3>
        <div class="tags" data-ats="${k}">${(s.companies[k] || []).map((c) => `<span class="tag">${esc(c)}<button type="button" data-rm="${k}|${esc(c)}" aria-label="Remove ${esc(c)}">×</button></span>`).join("") || '<span class="muted small">None yet</span>'}</div></div>`).join("")}</div>
    </div>
    <div class="card"><h2 class="section-title">Sources</h2>
      <div class="grid grid-2">${sources.map((src) => {
        const runs = src.runs || [];
        const lastRun = runs[0];
        const err = runs.find((r) => !r.ok);
        return `<label class="check"><input type="checkbox" name="src_${src.name}" ${s.sources[src.name] ? "checked" : ""}>
          <span>${esc(src.label)} ${src.direct_apply ? '<span class="chip accent">Direct apply</span>' : ""}
          <span class="hint">${lastRun ? `Last fetched ${ago(lastRun.ts)} · ${runs.reduce((a, r) => a + (r.count || 0), 0)} matching` : "Not fetched yet"}${err ? ` · <span style="color:var(--bad)">${esc(err.error || "error")}</span>` : ""}</span></span></label>`;
      }).join("")}</div>
      <p class="muted small" style="margin-bottom:0">Listings come from each site's public API and link back to the original post. Remotive asks for no more than a few requests a day, so JobBot refreshes it at most every 6 hours.</p>
    </div>
    <div class="sticky-save"><button class="btn primary" type="submit">Save search</button></div>
  </form>`;
  const form = $("#sf", el);
  const split = (v) => v.split(/\n|,/).map((x) => x.trim()).filter(Boolean);
  const save = async (msg) => {
    const out = {
      ...s,
      keywords: split(form.keywords.value), exclude: split(form.exclude.value), locations: split(form.locations.value),
      remote: form.remote.value, min_salary: +form.min_salary.value || 0, max_age_days: +form.max_age_days.value || 0,
      sources: Object.fromEntries(sources.map((src) => [src.name, form.elements[`src_${src.name}`].checked])),
    };
    await api("/api/settings/search", { method: "PUT", body: out });
    Object.assign(s, out);
    if (msg) toast(msg);
  };
  form.onsubmit = (e) => { e.preventDefault(); guard(() => save("Search saved. Scores updated.")); };
  $$("[data-rm]", el).forEach((b) => (b.onclick = () => guard(async () => {
    const [k, c] = b.dataset.rm.split("|");
    s.companies[k] = (s.companies[k] || []).filter((x) => x !== c);
    await save(`Removed ${c}`);
    viewSearch(el);
  })));
  const add = () => guard(async () => {
    const name = $("#co-name").value.trim();
    if (!name) return;
    $("#co-msg").textContent = "Looking…";
    await save();
    const r = await api("/api/companies/detect", { method: "POST", body: { name, add: true } });
    $("#co-msg").textContent = "";
    if (!r.found.length) return toast(`No Greenhouse, Lever or Ashby board found for “${name}”. Try a link to one of its job posts.`);
    toast(`Added ${r.found.map((f) => `${f.slug} (${SOURCE_LABELS[f.ats]})`).join(", ")}`);
    viewSearch(el);
  });
  $("#co-add").onclick = add;
  $("#co-name").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); add(); } });
}

// ------------------------------------------------------------------ automation & AI
async function viewSettings(el) {
  const [a, llm] = await Promise.all([api("/api/settings/automation"), api("/api/settings/llm")]);
  el.innerHTML = `<form id="af" class="stack">
    <div class="card"><h2 class="section-title">Automation</h2>
      <div class="form-grid">
        <label class="check wide"><input type="checkbox" name="enabled" ${a.enabled ? "checked" : ""}>
          <span>Search automatically while JobBot is running<span class="hint">Runs every enabled source on the interval below.</span></span></label>
        <label class="field">Search every (hours)<input type="number" min="1" name="interval_hours" value="${esc(a.interval_hours)}"></label>
        <span></span>
        <label class="check"><input type="checkbox" name="auto_prepare" ${a.auto_prepare ? "checked" : ""}>
          <span>Fill applications for strong matches<span class="hint">Fills the form and takes a screenshot. Nothing is sent.</span></span></label>
        <label class="field">…when the score is at least<input type="number" min="0" max="100" name="prepare_min_score" value="${esc(a.prepare_min_score)}"></label>
        <label class="check"><input type="checkbox" name="auto_submit" ${a.auto_submit ? "checked" : ""}>
          <span>Submit automatically<span class="hint">Only for Greenhouse, Lever and Ashby forms where every required question was answered.</span></span></label>
        <label class="field">…when the score is at least<input type="number" min="0" max="100" name="submit_min_score" value="${esc(a.submit_min_score)}"></label>
        <label class="check wide"><input type="checkbox" name="auto_submit_ai_answers" ${a.auto_submit_ai_answers ? "checked" : ""}>
          <span>Auto-submit even when some answers were written by AI<span class="hint">Off: applications with AI answers wait for you to read them.</span></span></label>
        <label class="field">Daily application limit<input type="number" min="1" name="daily_limit" value="${esc(a.daily_limit)}"></label>
        <label class="field">Max applications per company (30 days)<input type="number" min="1" name="company_limit_30d" value="${esc(a.company_limit_30d)}"></label>
      </div></div>
    <div class="card"><h2 class="section-title">Browser</h2>
      <div class="form-grid">
        <label class="check wide"><input type="checkbox" name="headless" ${a.headless ? "checked" : ""}>
          <span>Run the browser in the background (headless)<span class="hint">Turn this off to watch JobBot fill forms. When a site shows a CAPTCHA or a question only you can answer, JobBot waits for you to finish in that window.</span></span></label>
        <label class="field">Wait for you this long (minutes)<input type="number" min="1" name="assist_timeout_min" value="${esc(a.assist_timeout_min)}"></label>
      </div></div>
    <div class="card"><h2 class="section-title">AI answers (optional)</h2>
      <p class="muted small" style="margin-top:-6px">Uses Claude to answer required questions your profile can't cover, and to tailor cover letters.
        It only uses facts from your profile and resume and leaves a question for you rather than guess. AI answers are labelled in the review screen.</p>
      <div class="form-grid">
        <label class="check wide"><input type="checkbox" name="llm_enabled" ${llm.enabled ? "checked" : ""}> Use Claude for open questions</label>
        <label class="field">Anthropic API key <span class="hint">${llm.has_key ? "A key is saved. Leave blank to keep it." : llm.env_key ? "Using ANTHROPIC_API_KEY from the environment." : "Get one at console.anthropic.com. Stored only in your local database."}</span>
          <input type="password" name="api_key" autocomplete="off" placeholder="${llm.has_key ? "••••••••" : "sk-ant-…"}"></label>
        <label class="field">Model<input type="text" name="model" value="${esc(llm.model)}"></label>
        <label class="check"><input type="checkbox" name="answer_questions" ${llm.answer_questions ? "checked" : ""}> Answer required questions</label>
        <label class="check"><input type="checkbox" name="answer_optional" ${llm.answer_optional ? "checked" : ""}> Also answer optional “Why us?” questions</label>
        <label class="check"><input type="checkbox" name="cover_letters" ${llm.cover_letters ? "checked" : ""}> Write tailored cover letters</label>
        ${llm.has_key ? `<label class="check"><input type="checkbox" name="clear_key"> Remove the saved key</label>` : ""}
      </div></div>
    <div class="sticky-save"><button class="btn primary" type="submit">Save settings</button></div>
  </form>`;
  const f = $("#af", el);
  f.onsubmit = (e) => {
    e.preventDefault();
    guard(async () => {
      const num = (n) => +f.elements[n].value || 0;
      const auto = {
        ...a, enabled: f.enabled.checked, interval_hours: Math.max(1, num("interval_hours")),
        auto_prepare: f.auto_prepare.checked, prepare_min_score: num("prepare_min_score"),
        auto_submit: f.auto_submit.checked, submit_min_score: num("submit_min_score"),
        auto_submit_ai_answers: f.auto_submit_ai_answers.checked, daily_limit: Math.max(1, num("daily_limit")),
        company_limit_30d: Math.max(1, num("company_limit_30d")), headless: f.headless.checked,
        assist_timeout_min: Math.max(1, num("assist_timeout_min")),
      };
      if (auto.auto_submit && !a.auto_submit && !confirm("Turn on automatic submission?\n\nJobBot will submit applications without asking, within your daily and per-company limits.")) return;
      await api("/api/settings/automation", { method: "PUT", body: auto });
      await api("/api/settings/llm", { method: "PUT", body: {
        enabled: f.llm_enabled.checked, api_key: f.api_key.value.trim(), model: f.model.value.trim() || "claude-opus-5-5",
        answer_questions: f.answer_questions.checked, answer_optional: f.answer_optional.checked,
        cover_letters: f.cover_letters.checked, clear_key: f.clear_key ? f.clear_key.checked : false,
      } });
      toast("Settings saved");
      refreshState();
      viewSettings(el);
    });
  };
}

// ------------------------------------------------------------------ router
const VIEWS = {
  dashboard: viewDashboard, jobs: viewJobs, review: viewReview, applied: viewApplied, profile: viewProfile,
  answers: viewAnswers, search: viewSearch, settings: viewSettings, activity: viewActivity,
};
let currentView = null;

async function route() {
  const name = (location.hash.replace(/^#\/?/, "") || "dashboard").split("?")[0];
  const v = VIEWS[name] ? name : "dashboard";
  $$("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === v));
  $("#view-title").textContent = TITLES[v];
  document.title = `${TITLES[v]} · JobBot`;
  currentView = v;
  onState = null;
  const el = $("#view");
  try { await VIEWS[v](el); } catch (e) { el.innerHTML = `<div class="notice bad">${esc(e.message)}</div>`; }
}

window.addEventListener("hashchange", route);
refreshState();
route();
setInterval(refreshState, 4000);
