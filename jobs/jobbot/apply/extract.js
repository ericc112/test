// Runs inside the application page. Finds every question on the form, tags its
// element(s) with data-jobbot="<key>" (or "<key>:<option index>") so Python can
// target them, and reports page-level signals (captcha, success, errors).
// Argument: {onlyNew: bool} - skip elements tagged by an earlier pass.
(args) => {
  const onlyNew = !!(args && args.onlyNew);
  const clean = (s) => (s || "").replace(/\s+/g, " ").replace(/\s*[*✱]+\s*$/, "").trim();
  const text = (el) => (el ? (el.innerText || el.textContent || "") : "");
  const hasReqMark = (s) => /[*✱]\s*$/.test((s || "").trim());

  function visible(el) {
    if (!el || !el.isConnected) return false;
    const st = getComputedStyle(el);
    if (st.display === "none" || st.visibility === "hidden") return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }

  // Pick the form that holds the application (the one with the most fields).
  const controlSel = "input:not([type=hidden]), select, textarea";
  let root = document.body;
  let best = 0;
  for (const f of document.querySelectorAll("form")) {
    const n = [...f.querySelectorAll(controlSel)].filter(visible).length;
    if (n > best) { best = n; root = f; }
  }
  if (best < 2) root = document.body;

  let counter = 0;
  const existing = [...document.querySelectorAll("[data-jobbot]")]
    .map((e) => parseInt((e.getAttribute("data-jobbot").match(/^q(\d+)/) || [])[1] || "0", 10));
  counter = existing.length ? Math.max(...existing) + 1 : 0;
  const newKey = () => "q" + counter++;
  const tagged = (el) => el.hasAttribute("data-jobbot");

  const NOISE = /^(attach|upload|upload file|choose file|browse|dropbox|google drive|enter manually|or|select|select\s*\.\.\.|--+|click here.*)$/i;
  const HINT = /^(accepted file types|supported (file )?(types|formats)|max(imum)? (file )?size|file size|\(optional\)$)/i;
  // A line is usable when something remains after removing option texts and widget
  // words; inline siblings like <button>Yes</button><button>No</button> read as "YesNo".
  const usable = (l, exclude) => {
    if (!l || exclude.has(l.toLowerCase()) || NOISE.test(l) || HINT.test(l)) return false;
    let rest = l.toLowerCase();
    for (const x of exclude) if (x) rest = rest.split(x).join(" ");
    rest = rest.replace(/attach|upload( file)?|choose file|browse|dropbox|google drive|enter manually|\bor\b/g, " ");
    return rest.trim().length > 0;
  };

  function firstLine(el, exclude) {
    for (const l of text(el).split("\n").map(clean)) {
      if (usable(l, exclude)) return l;
    }
    return "";
  }

  // Option texts of a select, so a wrapping label isn't read as "Question Opt1 Opt2".
  const optionTexts = (el) => new Set(el.tagName === "SELECT" ? [...el.options].map((o) => clean(o.text).toLowerCase()) : []);

  const LABELISH = "legend, label, [class*=label], [class*=Label], [class*=question], [class*=Question], [class*=title], h1, h2, h3, h4, h5, h6";

  // Walk up from the field until a container holds a heading-like element but no
  // other fields. Works for Lever cards, Ashby entries, fieldsets, upload widgets.
  function containerLabel(els, exclude) {
    const own = new Set(els);
    const ownLabels = new Set(els.flatMap((e) => (e.labels ? [...e.labels] : [])));
    let a = els[0].parentElement;
    for (let depth = 0; a && a !== document.body && depth < 8; depth++, a = a.parentElement) {
      const foreign = [...a.querySelectorAll(controlSel)].some(
        (c) => !own.has(c) && visible(c) && c.type !== "file"
      );
      if (foreign) return "";
      const legend = a.matches("fieldset") ? a.querySelector("legend") : null;
      if (legend && clean(text(legend))) return text(legend).trim();
      for (const c of a.querySelectorAll(LABELISH)) {
        if (ownLabels.has(c) || els.some((e) => c.contains(e)) || !visible(c)) continue;
        const raw = text(c).trim();
        const first = raw.split("\n").map(clean).find((l) => usable(l, exclude));
        if (first) return raw.split("\n").length > 1 && /[*✱]/.test(raw) ? first + " *" : first;
      }
      const line = firstLine(a, exclude);
      if (line) return line;
    }
    return "";
  }

  function labelFor(el, exclude) {
    exclude = exclude || new Set();
    const lb = el.getAttribute("aria-labelledby");
    if (lb) {
      const t = lb.split(/\s+/).map((id) => text(document.getElementById(id))).join(" ").trim();
      if (t) return t;
    }
    const labs = [];
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l) labs.push(l);
    }
    if (el.labels && !["radio", "checkbox"].includes(el.type)) labs.push(...el.labels);
    for (const l of labs) {
      const raw = text(l).trim();
      const first = raw.split("\n").map(clean).find((x) => usable(x, exclude));
      if (first) return /[*✱]/.test(raw) ? first + " *" : first;
    }
    const al = el.getAttribute("aria-label");
    if (al) return al;
    return "";
  }

  function requiredOf(els, label) {
    for (const el of els) {
      if (el.required || el.getAttribute("aria-required") === "true") return true;
    }
    if (hasReqMark(label)) return true;
    const box = els[0].closest("li, fieldset, .field, [class*=field], [class*=question]");
    if (box) {
      const lab = box.querySelector("label, legend, [class*=label]");
      if (lab && (/[*✱]/.test(text(lab)) || /required/i.test(lab.className || ""))) return true;
    }
    return false;
  }

  function optionLabel(el) {
    if (el.labels && el.labels.length) return clean(text(el.labels[0]));
    const wrap = el.closest("label");
    if (wrap) return clean(text(wrap));
    const al = el.getAttribute("aria-label");
    if (al) return clean(al);
    const next = el.nextElementSibling;
    if (next && clean(text(next))) return clean(text(next));
    return clean(el.value);
  }

  const questions = [];
  const seenNames = new Set();
  const all = [...root.querySelectorAll("input, select, textarea, [role=combobox]")];

  for (const el of all) {
    if (onlyNew && tagged(el)) continue;
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || (tag === "input" ? "text" : tag)).toLowerCase();
    if (["hidden", "submit", "button", "image", "reset", "password"].includes(type)) continue;
    if (type === "file") {
      if (el.disabled) continue;
      let label = labelFor(el);
      if (!label || /^(attach|upload|choose|browse|select)\b/i.test(clean(label)) || clean(label).length < 3) {
        label = containerLabel([el], new Set()) || label;
      }
      const key = newKey();
      el.setAttribute("data-jobbot", key);
      questions.push({ key, kind: "file", label: clean(label), required: requiredOf([el], label),
        options: [], input_type: "file", name: el.name || el.id || "", multi: el.multiple,
        value: el.files && el.files.length ? el.files[0].name : null });
      continue;
    }
    const picker = el.classList && el.classList.contains("oracletaleocwsv2-multiselect-input");  // read-only, filled from its list
    if (!visible(el) || el.disabled || (el.readOnly && !picker)) continue;
    if (el.getAttribute("aria-hidden") === "true") continue;
    if (el.closest("[aria-hidden=true]")) continue;
    // Greenhouse renders tiny unlabeled "required" proxy inputs next to selects.
    if (tag === "input" && el.tabIndex === -1 && !labelFor(el)) continue;

    if (type === "radio" || type === "checkbox") {
      const name = el.name;
      if (name && seenNames.has(name)) continue;
      const group = name
        ? [...root.querySelectorAll(`input[type=${type}][name="${CSS.escape(name)}"]`)].filter(visible)
        : [el];
      if (name) seenNames.add(name);
      if (!group.length) continue;
      const opts = group.map(optionLabel);
      const exclude = new Set(opts.map((o) => o.toLowerCase()));
      const key = newKey();
      if (type === "checkbox" && group.length === 1) {
        const own = optionLabel(el);
        let label = own;
        if (own.length < 30) {
          const ctx = containerLabel(group, exclude);
          if (ctx) label = ctx + (own ? " — " + own : "");
        }
        el.setAttribute("data-jobbot", key);
        questions.push({ key, kind: "checkbox", label: clean(label), required: requiredOf(group, label),
          options: [], input_type: type, name: name || "", multi: false, value: el.checked ? "Yes" : null });
        continue;
      }
      // The question lives on the group (legend / card heading), not on an option's own label.
      const label = containerLabel(group, exclude) || labelFor(group[0]);
      group.forEach((g, i) => g.setAttribute("data-jobbot", `${key}:${i}`));
      const checked = group.filter((g) => g.checked).map(optionLabel);
      questions.push({ key, kind: type === "radio" ? "radio" : "checkboxes", label: clean(label),
        required: requiredOf(group, label), options: opts, input_type: type, name: name || "",
        multi: type === "checkbox", value: type === "radio" ? (checked[0] || null) : (checked.length ? checked : null) });
      continue;
    }

    const key = newKey();
    el.setAttribute("data-jobbot", key);
    const opts0 = optionTexts(el);
    let label = labelFor(el, opts0) || containerLabel([el], opts0) || el.placeholder || el.name || "";
    if (tag === "select") {
      const opts = [...el.options].filter((o) => o.value !== "" && clean(o.text) && !/^(select|choose|please select|--)/i.test(clean(o.text)))
        .map((o) => clean(o.text));
      const sel = el.selectedIndex >= 0 ? el.options[el.selectedIndex] : null;
      questions.push({ key, kind: "select", label: clean(label), required: requiredOf([el], label), options: opts,
        input_type: "select", name: el.name || el.id || "", multi: el.multiple,
        value: sel && sel.value !== "" ? clean(sel.text) : null });
      continue;
    }
    // Taleo's "Select All That Apply…" picker: a read-only box whose choices are checkboxes in a popup next to it.
    const pickerBoxes = el.classList && el.classList.contains("oracletaleocwsv2-multiselect-input") && el.closest(".form-group")
      ? [...el.closest(".form-group").querySelectorAll(".oracletaleocwsv2-multiselect-popup input[type=checkbox]")] : [];
    if (pickerBoxes.length) {
      const btn = el.closest(".form-group").querySelector("button[aria-label]");
      const plabel = (btn && btn.getAttribute("aria-label")) || label;
      pickerBoxes.forEach((b, i) => b.setAttribute("data-jobbot", `${key}:${i}`));
      // A choice's text is the label beside its box; its value can be an id ("1370" for "No").
      const choice = (b) => clean(text(b.closest(".checkbox") ? b.closest(".checkbox").querySelector("label") || b : b)) || clean(b.value);
      const picked = pickerBoxes.filter((b) => b.checked).map(choice);
      questions.push({ key, kind: "checkboxes", label: clean(plabel), required: el.required || requiredOf([el], plabel),
        options: pickerBoxes.map(choice), input_type: "popup", name: el.name || el.id || "",
        multi: true, value: picked.length ? picked : null });
      continue;
    }
    if (el.getAttribute("role") === "combobox") {
      const box = el.closest("[class*=select__control], [class*=container], div");
      const shown = box ? box.querySelector("[class*=single-value], [class*=singleValue]") : null;
      questions.push({ key, kind: "combobox", label: clean(label), required: requiredOf([el], label), options: [],
        input_type: "combobox", name: el.name || el.id || "", multi: false,
        value: (shown && clean(text(shown))) || el.value || null });
      continue;
    }
    questions.push({ key, kind: tag === "textarea" ? "textarea" : "text", label: clean(label),
      required: requiredOf([el], label), options: [], input_type: type, name: el.name || el.id || "",
      multi: false, value: el.value || null });
  }

  // Button groups (Ashby Yes/No and similar custom single-choice widgets).
  const groups = new Map();
  for (const b of root.querySelectorAll("button[aria-pressed], [role=radio]:not(input), button[data-option]")) {
    if (!visible(b) || (onlyNew && tagged(b))) continue;
    const parent = b.parentElement;
    if (!groups.has(parent)) groups.set(parent, []);
    groups.get(parent).push(b);
  }
  for (const [parent, btns] of groups) {
    if (btns.length < 2 || btns.length > 8) continue;
    const opts = btns.map((b) => clean(text(b)) || clean(b.getAttribute("aria-label")));
    const label = containerLabel(btns, new Set(opts.map((o) => o.toLowerCase())));
    const hidden = parent.querySelector("input");
    const key = newKey();
    btns.forEach((b, i) => b.setAttribute("data-jobbot", `${key}:${i}`));
    const pressed = btns.find((b) => b.getAttribute("aria-pressed") === "true" || b.getAttribute("aria-checked") === "true");
    let required = hidden ? requiredOf([hidden], label) : hasReqMark(label);
    const entry = parent.closest("[class*=field-entry], [class*=fieldEntry], fieldset, li");
    if (!required && entry) {
      const lab = entry.querySelector("label, legend");
      if (lab && (/required/i.test(lab.className || "") || /[*✱]/.test(text(lab)))) required = true;
    }
    questions.push({ key, kind: "buttons", label: clean(label), required, options: opts, input_type: "button",
      name: "", multi: false, value: pressed ? clean(text(pressed)) : null });
  }

  // Which repeated block a field sits in, so "End date year" can mean graduation (education)
  // or a past job (employment).
  for (const q of questions) {
    const el = document.querySelector(`[data-jobbot="${q.key}"], [data-jobbot^="${q.key}:"]`);
    const box = el && el.closest("[class*=employment], [class*=experience], [class*=work-history], [class*=workHistory], [class*=education], [class*=Education]");
    q.section = !box ? "" : /education/i.test(box.className) ? "education" : "employment";
  }

  // Page-level signals.
  const bodyText = text(document.body).slice(0, 20000);
  const frames = [...document.querySelectorAll("iframe")].filter(visible).map((f) => f.src || "");
  const captcha = frames.some((s) => /recaptcha\/(api2|enterprise)\/bframe|hcaptcha\.com.*(challenge|hcaptcha-challenge)|challenges\.cloudflare\.com/.test(s))
    || [...document.querySelectorAll("iframe[title*=challenge i]")].some(visible);
  const success = /thank(s| you) for (your )?(appl|submitting|interest)|application (has been |was )?(submitted|received|sent)|we('ve| have) received your application|successfully (submitted|applied)/i.test(bodyText);
  const errors = [...document.querySelectorAll("[role=alert], [aria-live=assertive], .error, [class*=error-message], [class*=errorMessage], [class*=field-error], [class*=helper-text--error]")]
    .filter(visible).map((e) => clean(text(e))).filter((t) => t && t.length < 300).slice(0, 10);
  const invalid = [...document.querySelectorAll("[aria-invalid=true]")].filter(visible)
    .map((e) => e.getAttribute("data-jobbot")).filter(Boolean);
  const login = [...document.querySelectorAll("input[type=password]")].some(visible);
  const botwall = /verify you are human|performing security verification|checking (if the site connection is secure|your browser)|just a moment\.\.\.|are you a robot|press (&|and) hold/i.test(document.title + " " + bodyText.slice(0, 3000))
    || frames.some((s) => /challenges\.cloudflare\.com|captcha-delivery\.com|perimeterx|hcaptcha\.com/.test(s)) && questions.length < 3;
  const submit = [...root.querySelectorAll("button, input[type=submit], [role=button]")]
    .filter(visible).some((b) => /^(submit|submit application|apply|apply now|send application|submit your application)$/i.test(clean(text(b) || b.value)));
  return { questions, page: { url: location.href, title: document.title, captcha, success, errors, invalid, login, botwall, submit } };
}
