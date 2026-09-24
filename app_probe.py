#!/usr/bin/env python3
"""
app_probe.py — drives the real page in headless Chromium and compares it with the Python reference.

Serves the folder over a local HTTP server (fetch() needs http, not file://), opens index.html, waits for the
dropdown to fill, selects the given movies one by one, clicks the button and records the result text.
Also reports: how many dropdown titles contain U+FFFD (mojibake from decoding latin-1 as UTF-8), whether
any recommendation repeats a title or the liked title, and whether the page matches similarity_lab.py.

    python3 app_probe.py --movies "101 Dalmatians (1996)" "Star Wars (1977)" --k 2 --measure jaccard
    python3 app_probe.py --dir ../fixed --movies "Star Wars (1977)" --k 5 --measure cosine
"""
import argparse, http.server, socketserver, threading, functools, os, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_genres import parse
from similarity_lab import top_k

def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    handler = functools.partial(Quiet, directory=directory)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler); httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/index.html"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="."); ap.add_argument("--movies", nargs="+", required=True)
    ap.add_argument("--k", type=int, default=2); ap.add_argument("--measure", default="jaccard")
    ap.add_argument("--select-id", default="movie-select"); ap.add_argument("--result-id", default="result")
    a = ap.parse_args()
    rows, _ = parse(os.path.join(a.dir, "u.item"))
    httpd, url = serve(os.path.abspath(a.dir))
    with sync_playwright() as pw:
        b = pw.chromium.launch(); page = b.new_page()
        logs = []; page.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        page.goto(url)
        page.wait_for_function(f"document.querySelectorAll('#{a.select_id} option').length > 100", timeout=30000)
        titles = page.evaluate(f"[...document.querySelectorAll('#{a.select_id} option')].map(o => o.textContent)")
        bad = [t for t in titles if "�" in t]
        print(f"dropdown: {len(titles)} options; titles with U+FFFD (mojibake): {len(bad)} e.g. {bad[:3]}")
        for name in a.movies:
            opt_value = page.evaluate(f"[...document.querySelectorAll('#{a.select_id} option')].find(o => o.textContent === {name!r})?.value")
            if opt_value is None:
                print(f"\n{name}: not in dropdown (encoding?)"); continue
            page.select_option(f"#{a.select_id}", opt_value)
            page.click("button"); page.wait_for_timeout(600)
            text = page.evaluate(f"document.getElementById({a.result_id!r}).textContent")
            print(f"\n{name}\n  page: {text}")
            liked = next(r for r in rows if r[1] == name)
            ref, _ = top_k(rows, liked, a.k, a.measure)
            ref_titles = [t for _, _, t, _ in ref]
            print(f"  reference ({a.measure}, top-{a.k}): {ref_titles}")
            tail = text.split("recommend:")[-1] if "recommend:" in text else ""
            got = sorted([t for t in {r[1] for r in rows} if t in tail], key=lambda t: tail.index(t))  # titles contain commas
            print(f"  match: {'YES' if got == ref_titles else 'NO'}  | repeats liked title: {name in got}  | duplicate titles in list: {len(got) != len(set(got))}")
        if logs: print("\nconsole:", logs[:5])
        b.close()
    httpd.shutdown()

if __name__ == "__main__":
    main()
