(async function () {
  const [cat, vers, plats] = await Promise.all([
    fetch("data/catalogue.json").then(r => r.json()),
    fetch("data/versions.json").then(r => r.json()).catch(() => ({ tools: {} })),
    fetch("data/platforms.json").then(r => r.json()),
  ]);
  const V = vers.tools || {};
  const PL = { ont: "Nanopore", hifi: "HiFi", sr: "Short read" };
  const today = new Date();
  const days = d => d ? (today - new Date(d)) / 864e5 : Infinity;
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmt = d => d ? new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";

  // state from URL hash
  const st = Object.fromEntries(new URLSearchParams(location.hash.slice(1)));
  const state = { p: st.p || "all", q: st.q || "", art: st.art === "1", leg: st.leg === "1" };
  const $ = id => document.getElementById(id);
  $("q").value = state.q; $("onlyArtefact").checked = state.art; $("showLegacy").checked = state.leg;

  const n = cat.tools.length, nv = cat.tools.filter(t => V[t.id]?.version).length;
  $("meta").innerHTML = `<b>${n}</b> tools · <b>${cat.steps.length}</b> steps · <b>${plats.length}</b> platforms<br>versions refreshed <b>${fmt(vers.updated) || "—"}</b><br>${nv}/${n} with a tracked release`;

  function activity(t) {
    const lc = V[t.id]?.last_commit || V[t.id]?.date;
    if (!lc) return "";
    const d = days(lc), cls = d < 183 ? "ok" : d < 730 ? "mid" : "";
    const label = d < 183 ? "active" : d < 730 ? "slowing" : "dormant";
    return `<span class="act" title="Last commit or release ${esc(lc)}"><span class="dot ${cls}"></span>${label}</span>`;
  }
  function card(t) {
    const v = V[t.id] || {};
    const isNew = days(v.date) < 30;
    const ver = v.version ? `<span class="ver ${isNew ? "new" : ""}" title="${esc(v.source || "")}">${esc(v.version)}${v.date ? " · " + fmt(v.date) : ""}</span>` : `<span class="ver">—</span>`;
    const chips = t.platforms.map(p => `<span class="chip">${PL[p]}</span>`).join("")
      + (t.flags.includes("artefact") ? `<span class="chip art">artefact</span>` : "")
      + (t.flags.includes("legacy") ? `<span class="chip leg">legacy</span>` : "");
    return `<article class="card ${t.flags.includes("legacy") ? "legacy" : ""}" id="t-${t.id}">
      <div class="top"><h3><a href="${esc(t.url)}" target="_blank" rel="noopener">${esc(t.name)}</a></h3>${ver}</div>
      <p class="desc">${esc(t.desc)}</p>${t.note ? `<p class="note">${esc(t.note)}</p>` : ""}
      <div class="foot">${chips}${activity(t)}</div></article>`;
  }
  function match(t) {
    if (state.p !== "all" && !t.platforms.includes(state.p)) return false;
    if (!state.leg && t.flags.includes("legacy")) return false;
    if (state.art && !t.flags.includes("artefact")) return false;
    if (state.q) {
      const hay = (t.name + " " + t.desc + " " + t.note + " " + t.step + " " + t.flags.join(" ")).toLowerCase();
      return state.q.toLowerCase().split(/\s+/).every(w => hay.includes(w));
    }
    return true;
  }
  function render() {
    document.querySelectorAll("#platformSeg button").forEach(b => b.setAttribute("aria-checked", b.dataset.p === state.p));
    const shown = cat.tools.filter(match);
    const byStep = s => shown.filter(t => t.step === s.id);
    $("rail").innerHTML = cat.steps.map(s => { const k = byStep(s).length; return `<a href="#s-${s.id}" class="${k ? "" : "dim"}" data-jump="${s.id}"><b>${k}</b>${esc(s.name)}</a>`; }).join("");
    $("steps").innerHTML = cat.steps.map((s, i) => {
      const ts = byStep(s); if (!ts.length) return "";
      const art = s.id === "trim";
      return `<section class="step ${art ? "art" : ""}" id="s-${s.id}"><div class="sec-head"><div class="tag">Step ${String(i + 1).padStart(2, "0")}${art ? " · artefacts" : ""}</div><h2>${esc(s.name)}</h2><p>${esc(s.desc)}</p></div>
        <div class="grid">${ts.map(card).join("")}</div></section>`;
    }).join("") || `<p class="empty">No tools match. Clear the search or switch platform.</p>`;
    const recent = shown.filter(t => days(V[t.id]?.date) < 30).sort((a, b) => (V[b.id].date > V[a.id].date ? 1 : -1));
    $("recentSec").hidden = !recent.length;
    $("recent").innerHTML = recent.map(t => `<a href="#t-${t.id}">${esc(t.name)}<span class="ver">${esc(V[t.id].version)}</span></a>`).join("");
    document.querySelectorAll(".pcard").forEach(c => {
      const g = c.dataset.id, grp = c.dataset.grp;
      c.classList.toggle("hidden", !(state.p === "all" || g === state.p || (state.p === "sr" && grp === "sr")));
    });
    const h = new URLSearchParams();
    if (state.p !== "all") h.set("p", state.p); if (state.q) h.set("q", state.q);
    if (state.art) h.set("art", "1"); if (state.leg) h.set("leg", "1");
    history.replaceState(null, "", h.toString() ? "#" + h : location.pathname);
  }
  $("pgrid").innerHTML = plats.map(p => `<article class="pcard" data-id="${p.id}" data-grp="${p.group}"><div class="grp">${p.group === "long" ? "Long read" : "Short read"}</div><h3>${esc(p.name)}</h3>
    <dl><dt>Chemistry</dt><dd>${esc(p.chem)}</dd><dt>Devices</dt><dd>${esc(p.devices)}</dd><dt>Reads</dt><dd>${esc(p.reads)}</dd><dt>Accuracy</dt><dd>${esc(p.accuracy)}</dd><dt>Output</dt><dd>${esc(p.raw)}</dd><dt>Base mods</dt><dd>${esc(p.mods)}</dd></dl><p>${esc(p.role)}</p></article>`).join("");

  $("platformSeg").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { state.p = b.dataset.p; render(); } });
  $("q").addEventListener("input", e => { state.q = e.target.value.trim(); render(); });
  $("onlyArtefact").addEventListener("change", e => { state.art = e.target.checked; render(); });
  $("showLegacy").addEventListener("change", e => { state.leg = e.target.checked; render(); });
  $("rail").addEventListener("click", e => { const a = e.target.closest("a[data-jump]"); if (a) { e.preventDefault(); document.getElementById("s-" + a.dataset.jump)?.scrollIntoView({ behavior: "smooth" }); } });
  render();
})();
