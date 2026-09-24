#!/usr/bin/env python3
"""
audit_genres.py — data-layer audit of the starter Movie Recommender (week2).

Parses u.item the way MovieLens defines it (24 fields: id | title | release | video | url | 19 genre flags,
the first flag being "unknown") and the way the starter data.js does it (fields.slice(5, 24) mapped onto an
18-name list that starts at "Action"), then reports every disagreement. Also checks text encoding and
duplicate titles, and prints the genre table for a few named movies.

    python3 audit_genres.py                       # audit u.item in the current folder
    python3 audit_genres.py --show "Star Wars (1977)" "Toy Story (1995)"
"""
import argparse, collections, sys

TRUE_GENRES = ["unknown", "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime", "Documentary",
               "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
               "Thriller", "War", "Western"]                       # 19, as in the MovieLens README
APP_GENRES = TRUE_GENRES[1:]                                        # 18, as in the starter data.js

def parse(path):
    raw = open(path, "rb").read()
    try:
        raw.decode("utf-8"); enc = "utf-8"
    except UnicodeDecodeError as e:
        enc = f"NOT utf-8 (first bad byte at offset {e.start}: {raw[e.start-12:e.start+8]!r}); decoding as latin-1"
    rows = [l.split("|") for l in raw.decode("latin-1").splitlines() if l.strip()]
    return rows, enc

def flags(fields): return [int(x) for x in fields[5:24]]
def true_set(fields): return {TRUE_GENRES[i] for i, v in enumerate(flags(fields)) if v}
def app_set(fields):  # exactly what the starter computes: genreNames[index] for index in 0..18 where value==1
    return {APP_GENRES[i] for i, v in enumerate(flags(fields)) if v and i < len(APP_GENRES)}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", default="u.item"); ap.add_argument("--show", nargs="*", default=[])
    a = ap.parse_args()
    rows, enc = parse(a.item)
    print(f"u.item: {len(rows)} movies, fields per line: {dict(collections.Counter(len(r) for r in rows))}, encoding: {enc}")
    mis = [r for r in rows if true_set(r) != app_set(r)]
    print(f"movies whose genre labels differ between MovieLens layout and the starter's parse: {len(mis)}/{len(rows)}")
    tw = sum('Western' in true_set(r) for r in rows); aw = sum('Western' in app_set(r) for r in rows)
    print(f"Western: {tw} movies in the data, {aw} labelled 'Western' by the starter (those are actually War)")
    unk = [r[1] for r in rows if 'unknown' in true_set(r)]
    print(f"'unknown'-only movies: {unk} -> starter labels them {[sorted(app_set(r)) for r in rows if 'unknown' in true_set(r)]}")
    dup = [t for t, n in collections.Counter(r[1] for r in rows).items() if n > 1]
    print(f"duplicate titles (same title, different id): {len(dup)} e.g. {dup[:5]}")
    for name in a.show:
        r = next((r for r in rows if r[1] == name), None)
        if r: print(f"  {name:28} data: {sorted(true_set(r))}  |  starter: {sorted(app_set(r))}")
        else: print(f"  {name}: not found")
    sys.exit(1 if mis else 0)

if __name__ == "__main__":
    main()
