// Workday application steps: one entry per question block ([data-automation-id^="formField-"]).
// Workday draws its own widgets (listbox buttons, search prompts, date spin boxes), so the
// generic extractor can't read them. Never touches the "beecatcher" honeypot.
() => {
  const visible = (el) => !!(el && el.offsetParent !== null && getComputedStyle(el).visibility !== "hidden");
  const clean = (t) => (t || "").replace(/\s+/g, " ").replace(/\*\s*$/, "").trim();
  let n = 0;
  const out = [];
  const seenAuto = {};
  const blocks = [...document.querySelectorAll('[data-automation-id^="formField-"]')].filter(visible);
  for (const box of blocks) {
    if (box.parentElement && box.parentElement.closest('[data-automation-id^="formField-"]')) continue; // nested
    if (box.querySelector('[data-automation-id="beecatcher"]')) continue;
    const id = box.getAttribute("data-automation-id");
    const legend = box.querySelector("legend");
    const lab = box.querySelector("label");
    const label = clean((legend && legend.innerText) || (lab && lab.innerText) || box.getAttribute("aria-label") || "");
    const required = /\*/.test((legend || lab || {}).innerText || "") || !!box.querySelector("[aria-required=true],[required]");
    const key = "wd" + n++;
    box.setAttribute("data-jobbot", key);
    const nth = seenAuto[id] = (id in seenAuto) ? seenAuto[id] + 1 : 0;  // Workday's own name: survives re-renders
    const q = { key, label, required, section: "", options: [], value: null, auto: id, nth };
    const sec = box.closest('[data-automation-id$="Section"],[role=group][aria-labelledby]');
    if (sec && /education/i.test(sec.getAttribute("data-automation-id") || "")) q.section = "education";
    if (sec && /workExperience/i.test(sec.getAttribute("data-automation-id") || "")) q.section = "employment";
    const file = box.querySelector('input[type=file]');
    const radios = [...box.querySelectorAll('input[type=radio]')];
    const checks = [...box.querySelectorAll('input[type=checkbox]')];
    const listbox = box.querySelector('button[aria-haspopup="listbox"]');
    const prompt = box.querySelector('[data-automation-id="multiselectInputContainer"], [data-automation-id="searchBox"]');
    const month = box.querySelector('[data-automation-id="dateSectionMonth-input"]');
    const year = box.querySelector('[data-automation-id="dateSectionYear-input"]');
    const area = box.querySelector("textarea");
    const text = box.querySelector('input[type=text], input[type=email], input[type=tel], input:not([type])');
    if (file) { q.kind = "file"; }
    else if (radios.length) {
      q.kind = "radio";
      q.options = radios.map((r) => clean((box.querySelector(`label[for="${r.id}"]`) || r.parentElement).innerText));
      const on = radios.find((r) => r.checked); q.value = on ? q.options[radios.indexOf(on)] : null;
    } else if (listbox) {
      q.kind = "select";  // options are read by opening the list (see workday.py)
      q.input_type = "wd_listbox";
      const shown = clean(listbox.innerText);
      q.value = /^select one$/i.test(shown) ? null : shown;
    } else if (prompt) {
      q.kind = "select"; q.input_type = "wd_prompt";
      const chosen = [...box.querySelectorAll('[data-automation-id="selectedItem"]')].map((e) => clean(e.innerText));
      q.value = chosen.length ? chosen.join(", ") : null;
    } else if (month || year) {
      q.kind = "text"; q.input_type = month ? "month" : "wd_year";
      q.value = [month && month.value, year && year.value].filter(Boolean).join("/") || null;
    } else if (checks.length === 1) {
      q.kind = "checkbox"; q.value = checks[0].checked;
      if (!q.label) q.label = clean((box.querySelector(`label[for="${checks[0].id}"]`) || box).innerText);
    } else if (checks.length > 1) {
      q.kind = "checkboxes";
      q.options = checks.map((c) => clean((box.querySelector(`label[for="${c.id}"]`) || c.parentElement).innerText));
    } else if (area) { q.kind = "textarea"; q.value = area.value || null; }
    else if (text && text.getAttribute("data-automation-id") !== "beecatcher") { q.kind = "text"; q.value = text.value || null; q.input_type = text.type || ""; }
    else continue;
    out.push(q);
  }
  const step = document.querySelector('[data-automation-id="progressBarActiveStep"]');
  const errors = [...document.querySelectorAll('[data-automation-id="errorMessage"], [data-automation-id="inputAlert"], [role=alert]')]
    .filter(visible).map((e) => clean(e.innerText)).filter((t) => t && t.length < 300);
  const next = document.querySelector('[data-automation-id="bottom-navigation-next-button"], [data-automation-id="pageFooterNextButton"]');
  const bodyText = document.body.innerText.slice(0, 20000);
  return {
    questions: out,
    step: step ? clean(step.innerText).replace(/^current step \d+ of \d+\s*/i, "") : "",
    errors,
    next: next ? clean(next.innerText) : "",
    signIn: !!document.querySelector('[data-automation-id="email"]') && !!document.querySelector('[data-automation-id="password"]'),
    createAccount: !!document.querySelector('[data-automation-id="verifyPassword"]'),
    verify: /verify (your )?(email|account)|verification (email|link)|check your (email|inbox)/i.test(bodyText),
    submitted: /application (was |has been )?(successfully )?submitted|thank you for (applying|your application)|congratulations.{0,40}submitted/i.test(bodyText),
    captcha: [...document.querySelectorAll("iframe")].some((f) => /captcha|challenges\.cloudflare/.test(f.src || "")),
  };
}
