// Shared helpers for the kid and parent pages.
const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const DAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function ymd(d) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function addDays(d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

// Does this item happen on this date, for this kid?
function happensOn(item, date, kidId) {
  // "who" is "all", one player's id, or a list of ids.
  if (kidId && item.who !== "all" && ![].concat(item.who).includes(kidId)) return false;
  const w = item.when || {};
  if (w.kind === "daily") return true;
  if (w.kind === "weekly") return (w.days || []).includes(date.getDay());
  if (w.kind === "date") return w.date === ymd(date);
  return false;
}

function fmtTime(hhmm) {
  if (!hhmm) return "";
  const [h, m] = hhmm.split(":").map(Number);
  const ampm = h >= 12 ? "PM" : "AM";
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, "0")} ${ampm}`;
}

function describeWhen(item) {
  const w = item.when || {};
  if (w.kind === "daily") return "Every day";
  if (w.kind === "weekly") {
    const days = (w.days || []).slice().sort();
    if (days.join() === "1,2,3,4,5") return "Weekdays";
    return "Every " + days.map((d) => DAY_SHORT[d]).join(", ");
  }
  if (w.kind === "date") {
    const d = new Date(w.date + "T00:00");
    return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  }
  return "";
}

function byTime(a, b) {
  return (a.time || "99").localeCompare(b.time || "99");
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function api(path, body) {
  if (window.DEMO) return demoApi(path, body);
  const res = await fetch(path, body === undefined ? { cache: "no-store" } : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Something went wrong");
  return json;
}

// Escapes text and turns any web addresses in it into links that open in a new tab.
function linkify(text) {
  return String(text ?? "").split(/(https?:\/\/[^\s]+)/g).map((part, i) => {
    if (i % 2 === 0) return esc(part);
    let label = part;
    try { label = new URL(part).hostname.replace(/^www\./, ""); } catch {}
    return `<a class="link" href="${esc(part)}" target="_blank" rel="noopener">🔗 ${esc(label)}</a>`;
  }).join("");
}

// The page's widgets and where they go unless the parent moves them.
const WIDGETS = {
  kids: "👀 Kids Today (grown-ups only)",
  verse: "📖 Verse of the Week",
  tasks: "✅ Today's Tasks",
  events: "📅 Happening Today",
  reminders: "📌 Reminders",
  timer: "⏱️ Timer",
  doodle: "🎨 Doodle Pad / 🪨 Zen Garden",
  week: "🗓️ This Week",
};
const ZONES_ORDER = ["left", "right", "wide", "hidden"];
const DEFAULT_LAYOUT = { left: ["kids", "verse", "tasks", "events", "reminders"], right: ["timer", "doodle"], wide: ["week"], hidden: [] };

// Makes sure every widget shows up exactly once, even if new widgets were added since the layout was saved.
function normalizeLayout(layout) {
  const out = { left: [], right: [], wide: [], hidden: [] }, seen = new Set();
  for (const z of ZONES_ORDER) for (const w of (layout?.[z] || [])) {
    if (WIDGETS[w] && !seen.has(w)) { out[z].push(w); seen.add(w); }
  }
  // New widgets go where they'd sit in the default layout (so "kids" lands at the top).
  for (const z of ZONES_ORDER) DEFAULT_LAYOUT[z].forEach((w, i) => { if (!seen.has(w)) out[z].splice(i, 0, w); });
  return out;
}

// Week 1 of the year shows verse 1, week 2 shows verse 2, and so on.
function verseOfWeek(verses, date = new Date()) {
  if (!verses?.length) return null;
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const week = Math.ceil(((d - Date.UTC(d.getUTCFullYear(), 0, 1)) / 86400000 + 1) / 7);
  return { ...verses[(week - 1) % verses.length], week };
}
