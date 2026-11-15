"""Compare a published T3 theme file against the build's theme.json. Usage: python verify.py <slug>..."""
import json, os, sys
for s in sys.argv[1:]:
    built = json.load(open(f"out/{s}/theme.json", encoding="utf-8"))
    try:
        pub = json.load(open(os.path.expanduser(f"~/.t3/userdata/themes/ghibli-{s.replace('_', '-')}.json"), encoding="utf-8"))
    except FileNotFoundError:
        print(f"{s}: not published"); continue
    diffs = [k for k in set(built) | set(pub) if k != "colors" and built.get(k) != pub.get(k)]
    cdiff = {k for k in built.get("colors", {}) if built["colors"][k] != pub.get("colors", {}).get(k)}
    if built["css"] != pub.get("css", ""):
        a, b = built["css"], pub.get("css", "")
        i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        print(f"{s}: CSS MISMATCH at char {i}: built ...{a[i-20:i+20]!r} vs published ...{b[i-20:i+20]!r} (len {len(a)} vs {len(b)})")
    print(f"{s}: {'EXACT MATCH' if not diffs and not cdiff else f'differs in {diffs} colors {cdiff}'}")
