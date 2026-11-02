// Demo mode: on GitHub Pages (or after opening a page with ?demo in the address) the pages run without
// the Python server. Starter data comes from demo-data.json, and everything a visitor changes is kept
// only in their own browser.
const REPO_URL = "https://github.com/zoe-ya/motherload";
const DEMO_KEY = "demo-state";

try { if (new URLSearchParams(location.search).has("demo")) sessionStorage.setItem("demo", "1"); } catch {}
window.DEMO = location.hostname.endsWith("github.io") || (() => { try { return sessionStorage.getItem("demo") === "1"; } catch { return false; } })();

let demoSeed = null;

// Answers the same requests the server does, using the visitor's browser storage.
async function demoApi(path, body) {
  if (!demoSeed) demoSeed = await (await fetch("demo-data.json", { cache: "no-store" })).json();
  let state = null;
  try { state = JSON.parse(localStorage.getItem(DEMO_KEY)); } catch {}
  // When the starter data changes (new players or items), returning visitors start fresh so they see it.
  const seedSig = JSON.stringify([demoSeed.settings.kids, demoSeed.items.map((i) => i.id)]);
  if (!state || state.seed !== seedSig) state = { seed: seedSig, items: demoSeed.items, kids: demoSeed.settings.kids, layout: demoSeed.settings.layout, done: {} };
  const save = () => { try { localStorage.setItem(DEMO_KEY, JSON.stringify(state)); } catch {} };
  const view = () => ({ items: state.items, done: state.done, verses: demoSeed.verses, settings: { kids: state.kids, layout: state.layout, hasPin: false } });

  if (body === undefined) return view();
  if (path === "/api/done") {
    const k = `${body.date}|${body.item}|${body.kid}`;
    if (body.done) state.done[k] = true; else delete state.done[k];
    save();
    return { ok: true };
  }
  if (path === "/api/login") return { ok: true };
  if (path === "/api/save") {
    const d = body.data || {};
    if (d.items) state.items = d.items;
    if (d.kids) state.kids = d.kids;
    if (d.layout) state.layout = d.layout;
    save();
    return view();
  }
  throw new Error("Not available in the demo");
}

// A strip across the top of the page explaining the demo, with a link to the other page.
function demoBanner(otherPageLink) {
  if (!window.DEMO) return;
  const bar = document.createElement("div");
  bar.className = "demobar";
  bar.innerHTML = `<b>DEMO</b> Try anything! Changes are saved only in your browser. ${otherPageLink}
    · <a href="#" id="demoReset">Start over</a> · <a href="${REPO_URL}" target="_blank" rel="noopener">Get your own on GitHub</a>`;
  document.body.prepend(bar);
  bar.querySelector("#demoReset").onclick = (e) => {
    e.preventDefault();
    if (!confirm("Start the demo over? This clears everything you changed.")) return;
    try { localStorage.clear(); } catch {}
    location.reload();
  };
}
