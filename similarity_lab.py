#!/usr/bin/env python3
"""
similarity_lab.py — reference implementation of item-to-item scoring on the 19-genre multi-hot vectors.

For one liked movie prints the Top-K under three measures — Jaccard (what the starter uses), raw dot product,
and cosine — plus how many candidates tie at the top score. Use it (a) to reproduce the starter's output
independently of the browser, (b) to show why ties make Jaccard/Top-2 arbitrary, and (c) to show the
dot-vs-cosine difference on a many-genre movie (bias-mitigation evidence).

    python3 similarity_lab.py --movie "101 Dalmatians (1996)" --k 5
    python3 similarity_lab.py --movie "Star Wars (1977)" --k 5 --measure all
"""
import argparse, math, collections
from audit_genres import parse, flags, TRUE_GENRES

def vec(fields): return flags(fields)
def jaccard(a, b):
    inter = sum(1 for x, y in zip(a, b) if x and y); union = sum(1 for x, y in zip(a, b) if x or y)
    return inter / union if union else 0.0
def dot(a, b): return float(sum(x * y for x, y in zip(a, b)))
def cosine(a, b):
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot(a, b) / (na * nb) if na and nb else 0.0

MEASURES = {"jaccard": jaccard, "dot": dot, "cosine": cosine}

def top_k(rows, liked, k, measure, exclude_ids=(), exclude_titles=()):
    lv = vec(liked)
    scored = [(MEASURES[measure](lv, vec(r)), int(r[0]), r[1], sum(vec(r))) for r in rows
              if int(r[0]) not in exclude_ids and r[1] not in exclude_titles and r is not liked]
    scored.sort(key=lambda t: (-t[0], t[1]))         # stable: ties keep id order, like Array.prototype.sort
    return scored[:k], scored

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", default="u.item"); ap.add_argument("--movie", required=True)
    ap.add_argument("--k", type=int, default=5); ap.add_argument("--measure", default="all", choices=["all", *MEASURES])
    ap.add_argument("--drop-duplicate-title", action="store_true", help="exclude candidates with the liked movie's title")
    a = ap.parse_args()
    rows, _ = parse(a.item)
    liked = next((r for r in rows if r[1] == a.movie), None)
    if not liked: raise SystemExit(f"movie not found: {a.movie}")
    print(f"liked: {liked[1]}  genres={[g for g, v in zip(TRUE_GENRES, vec(liked)) if v]}  |x|={sum(vec(liked))}")
    for m in (MEASURES if a.measure == "all" else [a.measure]):
        top, allscored = top_k(rows, liked, a.k, m, exclude_titles=[liked[1]] if a.drop_duplicate_title else ())
        best = top[0][0]; ties = sum(1 for s in allscored if abs(s[0] - best) < 1e-12)
        print(f"\n[{m}] top-{a.k} (candidates tied at the best score {best:.3f}: {ties})")
        for s, i, t, n in top: print(f"  {s:6.3f}  id={i:<5} |x|={n}  {t}")

if __name__ == "__main__":
    main()
