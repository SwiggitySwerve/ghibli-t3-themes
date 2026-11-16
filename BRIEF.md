# Ghibli scene brief (shared by every scene agent)

## Polish round (current task)
The user asked every scene agent to **clean up its scene, add more references and characters from the film, and tighten things up**. Do it in this order.

1. **Clean up first, to free budget.** Delete dead code and unused sprites, defs, classes and keyframes. Merge same-colour paths and drop redundant animations. Fix stray or isolated pixels, jaggy or inconsistent outlines, muddy colour clusters and off-palette colours. Scenes sit at about 21–23K of 50K.
2. **Add references and characters** that a fan would recognise: a secondary character, a creature, a prop, or an iconic moment from the film (your message has ideas, but use your own judgment). Prefer a few that read clearly at this size over many specks. A new character should have idle life, or come through as a "moment" in the existing cycle.
3. **Tighten:** composition and readability under the dark overlay; animation timing (stagger the moments so something happens through a ~2-minute window without crowding); loop seams; whole-pixel stepping.
4. **Keep everything that is already right:**
   - **Depth order** from the water audit: water effects first, nearer static occluders redrawn over moving sprites, distant things behind near things.
   - `THEME["position"]`, and the scene must still work in `wide.png`, a new 1680x780 pane with the message box outlined, plus `theme.png`, `portrait.png` and `app.png`.
   - No `url(#id)`; ≤ 50,000 with no `VALIDATOR FAIL` or `SVG XML FAIL`.
   - Any change the user made or approved, as listed in your message.
5. Edit only your own scene file. Don't run install.py; the main session installs and verifies.

**Report back:**
- what you cleaned up and how much it saved;
- what you added, with timings;
- what you tightened;
- the final budget line;
- the path to the best frame.

You are making an animated pixel-art background scene for a personal desktop-app theme (fan art, for the user's own use). In T3 Code, the scene fills the chat area behind the conversation.

**Current phase: full budget. Each scene is now its own theme**, so your scene gets the whole theme to itself, roughly 4× the earlier compact budget. The user wants to see **the best each scene can be** before anything gets trimmed back down. You are free to rework your scene, compose it again from scratch, or build on what's there.

## The bar
- Someone who has seen the film should know it within a second, through its characters plus its signature setting, as clean, deliberate pixel art with Ghibli's painterly colour: a soft gradient sky, distinct atmospheric depth layers and warm/cool contrast.
- With the extra room, aim higher on every axis:
  - Fix your scene's known weak spots first: the faces and details you had to fake, the generic shapes, the flat areas.
  - Make the characters richer, add secondary characters, and give them idle life: blinks, breathing, hair and cloth flutter, a head turn.
  - Add parallax depth layers, lighting, and texture where it earns its place.
  - Add more and better animation: layered ambient loops plus several "moments" staggered so something different happens through a ~2-minute window.
- Keep it **calm and tasteful**. It sits behind text people read all day, so richer doesn't mean busier.

`scenes/spirited_away.py` is the original pilot and reference for technique.

## Files and tools (all in this folder)
- `lib.py`: Canvas helpers.
  - `bands`: dithered vertical gradient.
  - `ridge`: wavy fill-below for hills.
  - `blob`: shaded circles.
  - `rect`.
  - `paint`: stamps ASCII pixel art into the static layer.
  - `sprite()`: turns ASCII art into SVG paths.
  - `Canvas(w, h)` takes any size.
- `scenes/_example.py` shows the scene-file format: NAME, COLORS, draw(), SPRITES, CSS.
- Two optional attributes:
  - `SIZE = (w, h)`: canvas size, default 240x135. You may go to 320x180 (or 384x216) if finer detail clearly helps. It must stay 16:9, and `draw()` must return a canvas of that size. Smaller pixels read as finer art but cost more bytes; judge it in app.png.
  - `THEME = {"canvas": "#hex", "accent": "#hex", "overlay": "#hex", "colors": {...}}`: the theme's colours, see below.
- Don't edit lib.py, build_scene.py, _example.py, or anyone else's scene. Write **only your own scene file**, and put any helpers you need inside it.
- Every CSS class, id and @keyframes name must start with your prefix.
- Build with `python build_scene.py <slug> t1 t2 t3 t4` (times in seconds). Outputs go to `out/<slug>/`:
  - `still.png`: the static layer.
  - `sheet.png`: 2x2 frames.
  - `frame_<t>.png`: each frame at full 1200x675.
  - `theme.png` / `portrait.png`: the real theme CSS in a wide and a narrow window. Magenta means the image failed to load.
  - **`app.png`**: a mock T3 Code window wearing your full theme, with sidebar, header, chat text, user bubble, code block and composer.
  - `theme.json`: the publishable theme.
  - The build prints the budget and warns about unpainted pixels.
- **After every build, Read the images and critique them honestly**, like an art director. Is it recognizable? Do the silhouettes read? Is anything muddy, misaligned, floating, clipped, or popping between frames? Is the chat text in app.png still comfortable to read? Iterate until it's genuinely the best you can make it.

## Theme colours (THEME)
These colours give the whole app (sidebar, buttons, inputs, borders) a palette that matches your scene.
- `canvas`: a dark tone from your scene, used as the base for the app's derived palette and as the fill behind the image.
- `accent`: your scene's signature colour (lantern red, Kiki's bow, Totoro grey-blue...). It's used for buttons and focus rings with dark text on top, so it must be light and saturated enough for that.
- `overlay`: optional. It tints the dark wash over the image and the glass behind the composer, user bubble and code blocks; it defaults to canvas.
- `colors`: optional overrides of single roles, so the chrome feels like part of the scene. Most useful: `sidebar`, `sidebarRowSelected`, `sidebarBorder`, `surface`, `border`, `text`, `textMuted`. Full role list: canvas, chrome, toolbar, surface, surfaceRaised, surfaceOverlay, text, textMuted, border, input, focus, accent, accentForeground, secondary, muted, mutedForeground, sidebar, sidebarForeground, sidebarMutedForeground, sidebarRowHover, sidebarRowActive, sidebarRowSelected, sidebarBorder, codeBackground, codeForeground, terminalBackground, terminalForeground, terminalCursor, terminalSelection.
- The appearance is dark. Check text contrast in app.png.

## Hard constraints
- **The theme's whole css must be ≤ 50,000 characters.** The build prints `theme css N / 50000`, and the chat-chrome rules take about 1,000 of that. Stay a couple of hundred under to leave room for later tweaks.
- **Safe zone.** The image is `cover`, anchored at the bottom. The composer hides the bottom ~13% of the canvas, and narrow windows crop the sides (check portrait.png). Keep hero characters within the middle ~42% of the width (x ≈ 70–170 of 240), landmarks within the middle ~67%, and everything important between ~18% and ~83% of the height.
- **Performance.** The SVG is a CSS background, so every animation tick re-rasterizes the image, and this runs all day. Keep the number of simultaneously animating elements moderate (tens, not hundreds). Never animate `filter` or large blurred or translucent areas, and avoid full-canvas animated layers. Prefer steps() and long periods for ambient motion.
- Animation is CSS only: transform (or the individual `translate`/`rotate`/`scale` properties) and opacity. A static `filter` is fine. **Nothing may visibly jump at a loop point.**
- No new dependencies. Pillow and the Python standard library are available.

## Techniques from the first round
- Everything static is cheapest in the PNG. Use SPRITES for what moves and for anything a moving sprite must pass *behind*. Nested small PNGs inside SPRITES work well for a big detailed moving object (Laputa's island, Howl's castle).
- If more than 16 colours are really used, Pillow writes 8-bit indices, which can be *smaller* than a forced 16 (Howl went from 1844 to 1516). Measure both.
- Flat areas and ordered dither are nearly free; random speckle and isolated pixels are expensive.
- In SVG, `#` costs 3 chars (`%23`) and `%` costs 3 (`%25`): use 3-digit hex or named colours, and `from`/`to` keyframes.
- Same-colour sprite details merge into one `<path>`. A row of windows is one stroked path with `stroke-dasharray`. A repeated small shape can be a `<marker>` stamped on polyline vertices (Heron's warawara cost about 5 chars each) or a `<use>`.
- For long-period moments, park the sprite far off-canvas and loop a single `to{transform:translateX(N)}`. Mirror direction with a parent `matrix(-1 0 0 1 e f)`.
- For serpentine or ripple motion, give each segment `style='--d:N'` and use `animation-delay:calc(var(--d)*-.3s)`. Custom properties inherit, so reset them on nested groups.

## Report back (concise)
1. The final budget line.
2. What changed versus the previous version, what's in the scene, and what animates with what periods.
3. Your THEME choices.
4. An honest assessment: the weakest remaining spot.
5. Paths to the best frame and app.png.
