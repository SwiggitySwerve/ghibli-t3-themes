# Ghibli pixel-art themes for T3 Code

Personal fan-art themes: each one sets T3 Code's chat background to an animated pixel-art scene from a Studio Ghibli film. Not affiliated with Studio Ghibli; for personal use only.

- `themes/`: the installed theme files (`ghibli-<film>.json`), ready to drop into `~/.t3/userdata/themes/`.
- `scenes/`: the scene source, one Python file per film.
- `build_scene.py <slug> [times...]`: builds a scene, renders preview frames to `out/<slug>/`, writes `theme.json`, and checks the 20,000-character limit and T3's url() rule.
- `install.py <slug>`: writes a built theme into T3's theme folder. `verify.py <slug>` checks the installed copy matches the build.
- `lib.py`: shared pixel-art helpers. `BRIEF.md`: the rules every scene follows.

Status: Spirited Away, Totoro, Ponyo, Kiki, Howl, Nausicaä and Mononoke done; Castle in the Sky in review; The Boy and the Heron and The Wind Rises paused; Slag Ravine shelved.
