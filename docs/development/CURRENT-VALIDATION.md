# Blender dirt/grass/rubbish pass — validation

18 October 2026. Node 24.19.0, Chromium 154.0.8037.57, Blender 4.3.2, Three.js 0.186.1, Rapier 0.21.0.
This pass follows local checkpoint `e768260`. Its measurements and images are retained in
[the previous validation record](VALIDATION-e768260.md); those numbers are not measurements of this pass.

## What is running

`index.html` uses actual WWB Player, Physics, Input, GameLoop, Arsenal, Bot, effects and round-rule
modules through ONSITE's encounter wrapper. One Rapier world and the existing layered navigation
remain in charge. This pass changes presentation, not collision, combat damage or navigation.

The Blender estate now has **3,010 editable render objects**, including **869 detail objects**:
600 separate chipped paving slabs, 3,404 grass blades in 209 clumps, folded litter, crushed cans,
fallen leaves, ground/wall grime and maintenance markings. Export batches these to **21 material
meshes**, **13,520,528 bytes**. The new asphalt colour image is generated; ambientCG supplies
separately credited dirt/damp colour, normal and roughness maps. The asphalt combines with existing
CC0 normal/ARM maps and is an approximate hybrid, not a matched scan.

Twelve individually verified Poly Haven prop models from IRONLINE are now used in 20 placements,
alongside the existing two WWB/Poly Haven props and original bench. The credited IRONLINE M4/hands
were finished in Blender: continued sleeve ends, preserved PBR maps and skin weights. The active
weapon derivative is **3,546,756 bytes**, with an editable `.blend`; ONSITE's original reload reach
still follows WWB's reload clock. No donor motion clips or Claudefare code/assets were added.

See [donor map](DONOR-MAP.md), [Blender dressing/reproduction](DIRT-PASS.md),
[asset notices](../../public/licenses/DONOR-ASSETS.md) and [current handoff](HANDOFF.md).

## Checks

- `npm run typecheck`: passed.
- `npm test`: **20 tests passed**. Ten retained legacy regressions, seven current WWB physics/nav
  tests, and three asset/collision tests. Physical tests exercise the actual bot brain and player
  capsules on both stairs. New assertions catch inverted paving faces, lost vertex alpha, missing
  weapon colour/normal maps, altered provenance hashes and accidental motion-clip imports.
- `npm run build`: passed. Main JS **5,116.97 kB / 1,880.38 kB gzip**. The >500 kB chunk warning
  remains. Full `dist` is approximately **46 MB**, including retained legacy and unused original
  donor payloads. It is not an optimized download budget.
- `node scripts/capture-detail.mjs`: passed four fixed-camera views and three frozen reload phases.
  No page/HTTP errors. Extraction-phase left-hand/magazine reach is within 1.5 cm; transforms finite.
  Visual inspection caught and fixed inverted slab tops and texture loss during Blender packing.
- The continuous browser stair route was not repeated in this presentation-only pass. Its earlier
  evidence remains labelled separately. The layout SHA is unchanged and the physical bot/player
  stair regressions passed again.

- Production-preview browser check: **10 checks passed**, **no page errors or failed/HTTP-error requests**.
  Actual pointer lock/mouse look, centred ADS, automatic fire/recoil/timed reload, pause/resume,
  jump/landing, lobby doorway movement, live combat, capture/victory and round reset.
  **Three bots eliminated, 76 health remaining, 26 shots / 12 hits**. The automation uses ordinary
  mouse/keyboard input and read-only snapshots/route queries; no teleport, damage or health hooks.

## Current performance measurement

The input-driven production-preview run used **SwiftShader software rendering**, a **1100×700**
viewport at **0.5 pixel ratio**, no MSAA or shadows, and four local world lights. Mean wall-clock
frame duration was **461.57 ms across 141 active samples (~2.17 FPS)**. Final counters were
**76 draw calls / 233,111 triangles**, summed across world and weapon passes. No other browser or
Blender render ran alongside it. Automation and screenshot overhead are included, so this is not
a controlled benchmark.

This is slower than the previous visual pass's 402.84 ms sample and is not smooth or suitable as
a performance target. Detail, lighting and weapon export all changed; this measurement does not
isolate their costs. Real-GPU profiling and payload/geometry optimization remain required.

## Actual runtime images

- [Courtyard and rifle](evidence/dirt-pass/court.png), [rubbish/grass/paving](evidence/dirt-pass/rubbish.png),
  [upper gallery](evidence/dirt-pass/gallery.png), [stair A](evidence/dirt-pass/stair.png).
- [Reload 35%](evidence/dirt-pass/reload-35.png), [55%](evidence/dirt-pass/reload-55.png),
  [85%](evidence/dirt-pass/reload-85.png), [inspection report](evidence/dirt-pass/report.json).
- [Input-driven gameplay video](evidence/dirt-pass/combat-input.webm),
  [ADS](evidence/dirt-pass/aiming.png), [combat](evidence/dirt-pass/combat.png),
  [victory](evidence/dirt-pass/victory.png), [combat report](evidence/dirt-pass/combat-report.json).
- [Prior courtyard image](evidence/dirt-before.png), copied unchanged from checkpoint `e768260`.
- [As-built plan](evidence/as-built.svg) and [exact collision/spawn data](evidence/layout.json).

The new inspection stills use the actual Three.js renderer at **1280×800, pixel ratio 1, sun
shadows and four warm local lights**, with bots disabled and a labelled fixed camera. They are
neither concept art nor an input-driven gameplay/performance sample. Software mode has no MSAA.

## Limits and next work

No real GPU is available in this cloud session. Hardware mode enables MSAA and sun shadows at
up to 1.5 pixel ratio; real-GPU appearance, frame time and sustained play feel remain unverified.
The original stylised hooded bot still needs a detailed black hoodie/joggers/trainers rig and
animation. Facades/rooms remain repetitive; hand/reload polish and payload optimization also need
work. This pass adds visible authored detail but does not establish concept-art fidelity or a
production-ready game.

Original concepts, textures, Blender sources and tests are preserved. All three pinned donor
clones were verified clean and ignored, with no nested trees in Git's index. Their SHAs and licence
boundaries are in `research/SOURCES.json`. No push, merge, deploy or cloud configuration publication.
