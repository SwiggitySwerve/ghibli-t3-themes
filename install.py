"""Write a built theme byte-exact into T3's theme store, replacing the copy published via t3_theme_set.

    python install.py <slug>...

Publishing through t3_theme_set means retyping ~18K characters of base64, which corrupts it. So each theme is
first published through the tool (which registers the id), then this overwrites the stored file with the exact
build output in the same format T3 writes (2-space JSON, UTF-8, no trailing newline). Only touches
ghibli-<slug>.json files that the tool already created.
"""
import json, os, sys

STORE = os.path.expanduser(os.path.join("~", ".t3", "userdata", "themes"))
HERE = os.path.dirname(os.path.abspath(__file__))

for slug in sys.argv[1:]:
    dest = os.path.join(STORE, f"ghibli-{slug.replace('_', '-')}.json")
    if not os.path.exists(dest):
        sys.exit(f"{dest} does not exist; publish it with t3_theme_set first")
    theme = json.load(open(os.path.join(HERE, "out", slug, "theme.json"), encoding="utf-8"))
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(theme, indent=2, ensure_ascii=False))
    print(f"installed {slug} -> {dest} ({len(theme['css'])} css chars)")
