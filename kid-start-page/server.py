"""Homeschool home page server.

Run:  python server.py
Kids open  http://<this-computer>:8080/?kid=1  (or kid=2)
Parent opens  http://<this-computer>:8080/edit
"""
import glob
import json
import os
import re
import socket
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8080
HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
DATA_FILE = os.path.join(HERE, "data.json")
VERSES_FILE = os.path.join(HERE, "52.bible.verses.txt")
lock = threading.Lock()

DEFAULT_DATA = {
    "settings": {
        "pin": "",
        "kids": [
            {"id": "1", "name": "Kid 1", "color": "#3b82f6", "emoji": "🚀"},
            {"id": "2", "name": "Kid 2", "color": "#ec4899", "emoji": "🌟"},
        ],
    },
    # when: {"kind": "date", "date": "YYYY-MM-DD"} | {"kind": "weekly", "days": [0-6, Sun=0]} | {"kind": "daily"}
    "items": [
        {"id": "seed1", "type": "task", "title": "Piano practice", "who": "all",
         "when": {"kind": "weekly", "days": [1, 3, 5]}, "time": "", "note": "20 minutes of scales and songs"},
        {"id": "seed2", "type": "event", "title": "Soccer practice", "who": "all",
         "when": {"kind": "weekly", "days": [1, 3]}, "time": "16:00", "note": "Bring cleats and water"},
        {"id": "seed3", "type": "event", "title": "Soccer game", "who": "all",
         "when": {"kind": "weekly", "days": [6]}, "time": "09:00", "note": "Wear your team shirt"},
        {"id": "seed4", "type": "task", "title": "Math lesson", "who": "all",
         "when": {"kind": "weekly", "days": [1, 2, 3, 4, 5]}, "time": "", "note": "https://www.synthesis.com/tutor"},
        {"id": "seed5", "type": "task", "title": "Read for 30 minutes", "who": "all",
         "when": {"kind": "daily"}, "time": "", "note": ""},
        {"id": "seed6", "type": "reminder", "title": "Make your bed and brush your teeth", "who": "all",
         "when": {"kind": "daily"}, "time": "", "note": ""},
    ],
    "done": {},  # "YYYY-MM-DD|itemId|kidId": true
}


def load():
    if not os.path.exists(DATA_FILE):
        save(DEFAULT_DATA)
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


def load_verses():
    """One verse per line, written as: verse text — Reference"""
    path = VERSES_FILE if os.path.exists(VERSES_FILE) else next(iter(glob.glob(os.path.join(HERE, "*verse*.txt"))), None)
    if not path:
        return []
    verses = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            text, _, ref = line.rpartition(" — ")
            verses.append({"text": text, "ref": ref} if text else {"text": line, "ref": ""})
    return verses


def public(data):
    """Data without the PIN, for kids' browsers."""
    out = dict(data)
    out["verses"] = load_verses()
    out["settings"] = {k: v for k, v in data["settings"].items() if k != "pin"}
    out["settings"]["hasPin"] = bool(data["settings"].get("pin"))
    return out


# ---------- Stock and crypto prices for the grown-ups' Markets box ----------
# Prices come from Yahoo Finance's free public endpoints (no account or key). Only ticker symbols
# and search words are sent. Answers are cached so many open pages still make only a few requests.
YAHOO = "https://query1.finance.yahoo.com"
QUOTE_TTL = 120     # seconds a price is reused
SEARCH_TTL = 600
_cache = {}
_cache_lock = threading.Lock()
TICKER = re.compile(r"^[A-Za-z0-9.^=\-]{1,15}$")


def cached(key, ttl, fetch):
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
    value = fetch()
    with _cache_lock:
        _cache[key] = (time.time(), value)
        if len(_cache) > 500:
            _cache.clear()
    return value


def yahoo(path):
    req = urllib.request.Request(YAHOO + path, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=6) as r:
        return json.load(r)


def quote(symbol):
    def fetch():
        try:
            m = yahoo(f"/v8/finance/chart/{urllib.parse.quote(symbol)}?range=1d&interval=1d")["chart"]["result"][0]["meta"]
        except Exception:
            return {"symbol": symbol.upper(), "error": True}
        price, prev = m.get("regularMarketPrice"), m.get("chartPreviousClose")
        pct = m.get("regularMarketChangePercent")
        if pct is None and price and prev:
            pct = (price - prev) / prev * 100
        return {"symbol": m.get("symbol", symbol.upper()), "name": (m.get("shortName") or m.get("longName") or "").strip(),
                "price": price, "pct": pct, "currency": m.get("currency", ""), "type": m.get("instrumentType", "")}
    return cached("q:" + symbol.upper(), QUOTE_TTL, fetch)


def quotes(symbols):
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(quote, symbols))


def search(q):
    def fetch():
        try:
            found = yahoo("/v1/finance/search?" + urllib.parse.urlencode({"q": q, "quotesCount": 8, "newsCount": 0}))["quotes"]
        except Exception:
            return []
        keep = {"EQUITY", "ETF", "CRYPTOCURRENCY", "INDEX", "MUTUALFUND", "CURRENCY"}
        return [{"symbol": f["symbol"], "name": (f.get("shortname") or f.get("longname") or "").strip(), "type": f.get("typeDisp", "")}
                for f in found if f.get("quoteType") in keep and f.get("symbol")][:8]
    return cached("s:" + q.lower(), SEARCH_TTL, fetch)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB, **kwargs)

    def log_message(self, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/data":
            with lock:
                return self.send_json(public(load()))
        if path in ("/api/quotes", "/api/search"):
            args = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            if path == "/api/quotes":
                symbols = [s for s in (args.get("s", [""])[0]).split(",") if TICKER.match(s)][:12]
                return self.send_json(quotes(symbols))
            q = args.get("q", [""])[0].strip()[:40]
            return self.send_json(search(q) if len(q) >= 1 else [])
        # The edit page used to be called the parent page; old links still work.
        if path in ("/edit", "/edit/", "/parent", "/parent/", "/parent.html"):
            self.path = "/edit.html"
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            body = self.read_body()
        except ValueError:
            return self.send_json({"error": "bad request"}, 400)

        with lock:
            data = load()

            # Kids checking a task off (no PIN needed).
            if path == "/api/done":
                key = f"{body.get('date')}|{body.get('item')}|{body.get('kid')}"
                if body.get("done"):
                    data["done"][key] = True
                else:
                    data["done"].pop(key, None)
                save(data)
                return self.send_json({"ok": True})

            # Everything else is parent-only.
            pin = data["settings"].get("pin") or ""
            if pin and body.get("pin") != pin:
                return self.send_json({"error": "Wrong PIN"}, 403)

            if path == "/api/login":
                return self.send_json({"ok": True})

            if path == "/api/save":
                new = body.get("data") or {}
                if "items" in new:
                    data["items"] = new["items"]
                if "kids" in new:
                    data["settings"]["kids"] = new["kids"]
                if "layout" in new:
                    data["settings"]["layout"] = new["layout"]
                if "newPin" in body:
                    data["settings"]["pin"] = body["newPin"]
                save(data)
                return self.send_json(public(data))

        return self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    with lock:
        load()
    name = socket.gethostname()
    print("Homeschool home page is running.")
    print(f"  Kids:  http://{name}:8080/?kid=1   and   http://{name}:8080/?kid=2")
    print(f"  Edit page:   http://{name}:8080/edit")
    print("Leave this window open (you can minimize it). Close it to stop.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
