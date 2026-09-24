#!/usr/bin/env python3
"""
profile_check.py — profile-based recommendation and the three HW2 failure-mode checks.

Builds a user profile as the mean of the multi-hot genre vectors of the watched movies (given as titles, or
taken from u.data for a user id), ranks the catalog by cosine to the profile and prints Top-K. Then runs:
  1. overlap check      — Top-K ∩ watched must be empty (leakage: a watched movie scores highest for its own profile)
  2. distribution check — popularity (rating count in u.data) of every Top-K item; flags an all-mainstream list
  3. formula check      — Top-K under raw dot product vs cosine; shows the norm bias when they differ
  4. collapse check     — cosine of each watched movie to the profile vs the best catalog match; a profile
                          that matches none of its own inputs has averaged the taste away

    python3 profile_check.py --titles "Star Wars (1977)" "Return of the Jedi (1983)" "Empire Strikes Back, The (1980)"
    python3 profile_check.py --user 1 --n-watched 3 --k 5          # 3 top-rated movies of user 1
    python3 profile_check.py --titles "Toy Story (1995)" "Scream (1996)" "Sense and Sensibility (1995)"
"""
import argparse, collections, math
from audit_genres import parse, flags, TRUE_GENRES
from similarity_lab import cosine, dot

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", default="u.item"); ap.add_argument("--data", default="u.data")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--titles", nargs="+"); g.add_argument("--user", type=int)
    ap.add_argument("--n-watched", type=int, default=3); ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--keep-watched", action="store_true", help="do NOT filter watched items (reproduce the leakage)")
    a = ap.parse_args()

    rows, _ = parse(a.item)
    by_id = {int(r[0]): r for r in rows}
    ratings = [l.split("\t") for l in open(a.data).read().splitlines() if l.strip()]
    pop = collections.Counter(int(r[1]) for r in ratings)

    if a.titles:
        watched = [next(r for r in rows if r[1] == t) for t in a.titles]
    else:
        mine = sorted((r for r in ratings if int(r[0]) == a.user), key=lambda r: (-int(r[2]), int(r[3])))
        watched = [by_id[int(r[1])] for r in mine[:a.n_watched]]
        print(f"user {a.user}: {len(mine)} ratings; using the {len(watched)} top-rated")
    wid = {int(r[0]) for r in watched}; wtitles = {r[1] for r in watched}
    print("watched:", [(r[1], [g for g, v in zip(TRUE_GENRES, flags(r)) if v]) for r in watched])

    profile = [sum(v) / len(watched) for v in zip(*(flags(r) for r in watched))]
    print("profile:", {g: round(v, 2) for g, v in zip(TRUE_GENRES, profile) if v})

    cands = rows if a.keep_watched else [r for r in rows if int(r[0]) not in wid and r[1] not in wtitles]
    def rank(measure):
        s = [(measure(profile, flags(r)), int(r[0]), r[1]) for r in cands]
        s.sort(key=lambda t: (-t[0], t[1])); return s
    cos_rank, dot_rank = rank(cosine), rank(dot)
    print(f"\nTop-{a.k} by cosine{' (watched NOT filtered)' if a.keep_watched else ''}:")
    for s, i, t in cos_rank[:a.k]: print(f"  {s:6.3f}  id={i:<5} pop={pop[i]:<4} |x|={sum(flags(by_id[i]))}  {t}")

    # 1. overlap
    overlap = [t for _, i, t in cos_rank[:a.k] if i in wid or t in wtitles]
    print(f"\n1. overlap check: Top-{a.k} ∩ watched = {overlap or '∅'}  -> {'FAIL' if overlap else 'PASS'}")
    # 2. distribution
    med = sorted(pop.values())[len(pop) // 2]
    pops = [pop[i] for _, i, _ in cos_rank[:a.k]]
    print(f"2. distribution check: rating counts {pops} (catalog median {med}); "
          f"{'all above median -> mainstream-only, note as limitation' if all(p > med for p in pops) else 'mixed popularity'}")
    # 3. formula
    top_dot = [t for _, _, t in dot_rank[:a.k]]; top_cos = [t for _, _, t in cos_rank[:a.k]]
    diff = [t for t in top_dot if t not in top_cos]
    print(f"3. formula check: dot-product Top-{a.k} differs from cosine in {len(diff)} item(s): {diff[:3]}"
          + (f" (dot favours |x| = {[sum(flags(by_id[i])) for _, i, _ in dot_rank[:a.k]]})" if diff else " (no norm bias visible here)"))
    # 4. collapse
    sims = [(r[1], cosine(profile, flags(r))) for r in watched]
    best = cos_rank[0][0]
    print(f"4. collapse check: cos(watched, profile) = {[(t, round(s, 3)) for t, s in sims]}; best catalog match {best:.3f}"
          + ("  -> profile scores lower than every input: taste washed out" if all(s < best for _, s in sims) else ""))

if __name__ == "__main__":
    main()
