# A02 Movie Recommender

This repository contains the audited MovieLens 100K content-based recommender, repaired prompt, regenerated implementation, deployment copy, and analysis scripts.

## Six Defects

1. **Wrong `u.item` charset:** The browser decoded Latin-1 `u.item` bytes as UTF-8, producing U+FFFD replacement characters such as `�` in Icelandic and other titles.
2. **Genre-field offset:** MovieLens has 19 flag fields, with `unknown` at field 5 and the 18 named genres at fields 6–23. The starter used only 18 names beginning with `Action`, shifting every label and dropping `Western`.
3. **Wrong item-to-item metric:** The starter ranked candidates with Jaccard similarity instead of cosine similarity on the binary genre vectors.
4. **Wrong result count:** The starter returned `slice(0, 2)` instead of the required Top-5.
5. **Incomplete candidate exclusion:** The starter excluded only the selected movie ID, so a different row with the same title could be recommended.
6. **Missing profile mode:** The starter had no three-movie profile workflow using a mean genre vector and cosine ranking.

## Files

| Path | Purpose |
| --- | --- |
| `site/index.html` | Deployable UI with item-to-item and profile controls |
| `site/style.css` | Deployable responsive layout and control styling |
| `site/data.js` | Latin-1 `u.item` loading, 19-label parsing, and rating parsing |
| `site/script.js` | Item-to-item cosine Top-5 and profile cosine Top-5 logic |
| `site/u.item` | MovieLens movie metadata and 19 genre flags |
| `site/u.data` | MovieLens user ratings used by the audit/profile checks |
| `prompt_fixed.md` | Corrected specification used to regenerate the four deployable code files |
| `audit_genres.py` | Compares the MovieLens layout with the starter mapping |
| `similarity_lab.py` | Reproduces Jaccard, dot-product, and cosine rankings |
| `profile_check.py` | Reproduces profile ranking and four profile checks |
| `app_probe.py` | Runs the real page in Chromium and compares it with the Python reference |

## Reproduction Commands

Run these commands from the project directory. The pure Python audit and ranking scripts use `python3`. The browser probe requires Playwright in the project virtual environment, so use `./.venv/bin/python` for that command if system `python3` reports `No module named 'playwright'`.

### Data and Encoding

```bash
python3 audit_genres.py --show "Star Wars (1977)" "101 Dalmatians (1996)" "Unforgiven (1992)" "Misérables, Les (1995)"
python3 audit_genres.py --show "Á köldum klaka (Cold Fever) (1994)"
```

The corrected 19-label mapping can be checked with:

```bash
python3 - <<'PY'
from audit_genres import parse, flags, TRUE_GENRES

rows, _ = parse('u.item')
fixed = lambda row: {TRUE_GENRES[i] for i, value in enumerate(flags(row)) if value}
mismatches = [row for row in rows if fixed(row) != {TRUE_GENRES[i] for i, value in enumerate(flags(row)) if value}]
print(f'fixed mapping mismatches: {len(mismatches)}/{len(rows)}')
PY
```

Expected result:

```text
fixed mapping mismatches: 0/1682
```

### Similarity

```bash
python3 similarity_lab.py --movie "101 Dalmatians (1996)" --k 5
python3 similarity_lab.py --movie "Star Wars (1977)" --k 5 --measure dot
python3 similarity_lab.py --movie "Star Wars (1977)" --k 5 --measure cosine
python3 similarity_lab.py --movie "Chasing Amy (1997)" --k 5 --measure cosine
python3 similarity_lab.py --movie "Á köldum klaka (Cold Fever) (1994)" --k 2 --measure jaccard
```

### Profile Checks

```bash
python3 profile_check.py --titles "Star Wars (1977)" "Return of the Jedi (1983)" "Empire Strikes Back, The (1980)"
python3 profile_check.py --titles "Star Wars (1977)" "Return of the Jedi (1983)" "Empire Strikes Back, The (1980)" --keep-watched
python3 profile_check.py --titles "Toy Story (1995)" "Scream (1996)" "Sense and Sensibility (1995)"
```

### Browser Probe

```bash
./.venv/bin/python app_probe.py --dir ../regen --movies "Unforgiven (1992)" "Star Wars (1977)" "Chasing Amy (1997)" --k 5 --measure cosine
```

This reproduces the zero-mojibake result and the three `match: YES` comparisons against the Python cosine reference.

### Popularity Counts

This prints the `u.data` rating counts for the item-to-item Star Wars Top-5:

```bash
python3 - <<'PY'
from collections import Counter

rows = [line.split('\t') for line in open('u.data') if line.strip()]
popularity = Counter(int(row[1]) for row in rows)
movies = {
    181: 'Return of the Jedi (1983)',
    172: 'Empire Strikes Back, The (1980)',
    271: 'Starship Troopers (1997)',
    498: 'African Queen, The (1951)',
    62: 'Stargate (1994)',
}
print([(title, popularity[item_id]) for item_id, title in movies.items()])
PY
```

Expected counts are `[507, 367, 211, 152, 127]`. The profile check prints `[211, 152, 127, 261, 429]` and the catalog median `27` directly.

## Analysis Answers

### 1. Item-to-Item vs Profile

For `Star Wars (1977)` alone, cosine item-to-item Top-5 is `Return of the Jedi (1983)`, `Empire Strikes Back, The (1980)`, `Starship Troopers (1997)`, `African Queen, The (1951)`, and `Stargate (1994)`, with scores `1.000`, `0.913`, `0.894`, `0.894`, and `0.775`. The trilogy profile removes the three watched movies and returns `Starship Troopers (1997) (0.885)`, `African Queen, The (1951) (0.885)`, `Stargate (1994) (0.766)`, `Jurassic Park (1993) (0.766)`, and `Independence Day (ID4) (1996) (0.766)`. The profile changes the query from one five-genre vector to a mean vector with `Action`, `Adventure`, `Romance`, `Sci-Fi`, and `War` at `1.0` and `Drama` at `0.33`, while excluding the watched trilogy.

### 2. Bias Mitigation

For Star Wars, dot product gives `Empire Strikes Back, The (1980)` and `Return of the Jedi (1983)` both `5.000`, with `|x|=6` and `|x|=5` respectively, followed by `Starship Troopers` and `African Queen` at `4.000` with `|x|=4`, and `Stargate` at `3.000` with `|x|=3`. Cosine changes the scores to `Return of the Jedi` `1.000`, `Empire Strikes Back` `0.913`, `Starship Troopers` `0.894`, `African Queen` `0.894`, and `Stargate` `0.775`; normalizing by `|x|` removes the raw dot product's preference for longer genre vectors.

### 3. Catalog Discovery

The item-to-item Star Wars Top-5 has popularity counts `[507, 367, 211, 152, 127]`, while the trilogy profile Top-5 has `[211, 152, 127, 261, 429]`; the lists share `Starship Troopers`, `African Queen`, and `Stargate`, while the profile swaps the two franchise sequels at `507` and `367` for `Independence Day` at `429` and `Jurassic Park` at `261`. Both lists are far above the catalog median of `27` ratings: the observed counts range from roughly `5x` to `19x` the median, so neither approach discovers long-tail items from the 19 binary genre flags alone. The profile spreads mainstream picks slightly more evenly, but catalog discovery needs a signal outside the genre vector, such as a popularity penalty or richer item features.
