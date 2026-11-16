# T3 Code themes

Animated background themes for T3 Code. The theme files in `themes/` are ready to install.

T3 loads at most 196,608 bytes of theme files in total and silently skips the rest, so only some of these can be installed at once (the Ghibli themes are ~20 KB each, Nyx · Aurora Ocean ~49 KB).

## Nyx

![Nyx · Aurora Ocean](nyx/previews/aurora-ocean.png)

Motion layers on top of the [Nyx theme](https://github.com/Deepusleepy/t3-nyx-theme) by Deepusleepy (MIT, kept in `nyx/base/` with its license). Each one makes the sky breathe and the stars twinkle, adds its own effect, and keeps the background dark enough to read on.

- `themes/nyx-aurora-ocean.json` (**Nyx · Aurora Ocean**): a flowing, hue-shifting aurora glow with local flares on the nebula, and a particle ocean along the bottom. The ocean is a dense dotted swell with a cross-hatch mesh, crossed by two seas whose waves come in irregular sets.
- `themes/nyx-animated.json` (**Nyx · Aurora Pulse**): the aurora glow pulsing across the whole cloud.
- `themes/nyx-wave-streams.json` (**Nyx · Data Streams**): three neon wave lines flowing along the cloud.

Install one with `t3 theme set themes/<file>.json` (the file name is the theme id).

Source, in `nyx/`:
- `nyx-aurora-ocean.css`, `nyx-common.css`, `variant-*.css`: the motion CSS, appended after the stock Nyx CSS.
- `gen_ocean.py`: generates the ocean, an animated SVG data URI. Its comments explain the wave model and why the rows are drawn the way they are (performance).
- `build.py`: rebuilds all three themes into `themes/` (`python -I nyx/build.py`). `build_nyx_animated.py` does the merge and enforces T3's 50,000-character CSS limit.
- `tools/render_ocean.py`: renders the ocean at given times in headless Chrome (`python -I nyx/tools/render_ocean.py nyx/out/variant-ocean.css <absolute out dir> 2 4 6`). `tools/perf.mjs` measures its frame rate (`node nyx/tools/perf.mjs nyx/out/variant-ocean.css 8`).

## Ghibli pixel art

Personal fan-art themes: each one sets T3 Code's chat background to an animated pixel-art scene from a Studio Ghibli film. Not affiliated with Studio Ghibli; for personal use only.

- `themes/`: the installed theme files (`ghibli-<film>.json`), ready to drop into `~/.t3/userdata/themes/`.
- `scenes/`: the scene source, one Python file per film.
- `build_scene.py <slug> [times...]`: builds a scene, renders preview frames to `out/<slug>/`, writes `theme.json`, and checks the 20,000-character limit and T3's url() rule.
- `install.py <slug>`: writes a built theme into T3's theme folder. `verify.py <slug>` checks the installed copy matches the build.
- `lib.py`: shared pixel-art helpers. `BRIEF.md`: the rules every scene follows.

Status: Spirited Away, Totoro, Ponyo, Kiki, Howl, Nausicaä, Mononoke and Castle in the Sky done; The Boy and the Heron and The Wind Rises paused; Slag Ravine shelved and removed (it's in the git history).
