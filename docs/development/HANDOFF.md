# ONSITE continuation handoff

## Direction and active entry

London browser FPS, bots first. The user's attached ground/upper floor plans were reviewed in chat and treated as proposals. Their 36×30 m footprint, 24×18 m court, 3 m gallery, central 18×12 m void and two stair cores guide the implementation. [As-built plan](evidence/as-built.svg) and [exact solids/spawns](evidence/layout.json) are generated from code, not the attached artwork. Stair door offsets and room openings were adjusted for physical circulation. No claim that the proposed image itself is an as-built drawing.

Active: `index.html` → `src/onsite/main.ts`. Actual WWB runtime modules in `src/wwb`; original ONSITE `Encounter`, `View`, `level` and `navigation` adapters in `src/onsite`. Read [DONOR-MAP.md](DONOR-MAP.md) for exact reuse. The old prototype remains at `/legacy.html` during development. Do not restart with another controller or replace working combat with a toy implementation.

## Recovery and preserved work

[CHECKPOINT.md](CHECKPOINT.md) records the verified ~993 MB pre-integration archive outside this checkout and safe restore commands. The full pre-visual-pass playable is also committed as `d5faf61`. All original concept art, generated images, original Blender sources, original PBR sets and tests remain. No merge/push/deploy. Three full reference trees remain ignored in `research/reference-clones`, with exact commits in `research/SOURCES.json`. Never recursively stage that folder. The local archive is not remotely backed up.

## Current interaction

WASD, mouse, LMB automatic carbine, RMB ADS, R reload, Shift sprint, Space jump, C crouch/slide, Escape pause. Three opponents use WWB's normal perception/roaming/cover/combat state machine, targeting the player only. Clear all three then stand within 4 m of the centre on ground level for 2.5 s. Death or 180 s timeout loses the encounter. Reset restores actors/ammo/timer. No cloud backend, duel or multiplayer implementation.

Bot navigation is original layered geometry-derived nodes at 0.375 m horizontal spacing. Paths retain floor height. One Rapier world owns player and bot capsules. Bots use character-controller collision rather than height teleportation. Tests run real bot brains and real player capsules up/down both stairs. Only cardinal graph edges; no unsafe 2D path smoothing across the open void. Larger maps will need navigation optimization and robust replanning around dynamic blockers.

## Art and presentation

The active architecture is now an actual Blender-authored level: `assets/blender/onsite-heron-court.blend`
→ `public/models/onsite-heron-court.glb`. Read [BLENDER-LEVEL.md](BLENDER-LEVEL.md) before editing.
The estate now has 6,773 editable render objects, exporting to 25 material meshes. The retained 869 detail objects include paving, grass and litter. New South London homes add stock brick, recessed windows, 20 balconies, six surrounding terraces and two background point blocks; see SOUTH-LONDON-HOMES.md. The north-west ground-floor room is now a furnished accessible flat with authoritative furniture/partition colliders. Upper homes and surrounding buildings remain visual-only.
Editable render, collision guides, navigation guides, donor dressing and review-lighting collections
are separate. Runtime lighting is rebuilt in Three.js; Blender lamps do not automatically transfer.

The first-person model is IRONLINE's M4A1 + DJMaesen/Cransh posed hands, with author/source/CC BY
records and both external WebP arm textures. The active `onsite-carbine.glb` is a Blender-finished derivative with sleeve continuations and preserved PBR maps. `src/onsite/DonorRifle.ts` adapts the art to WWB's Arsenal;
ammo, hitscan, timing, recoil and reload completion remain WWB-owned. The original two-bone reload
reach uses no Fab motion tracks. The original procedural weapon stays available in the source.

Twelve individually verified Poly Haven props and the Bambanani Sunset HDRI were imported through
IRONLINE. The car, bins and gallery barrier have colliders measured by Blender; routes must remain
height-aware. `dressing.json` drives both visible placement and separate collider dimensions. Existing
WWB-sourced utility boxes/security lights and original Blender benches remain. Exact notices at
`public/licenses/DONOR-ASSETS.md`, provenance/hashes at `public/models/donors/provenance.json`.
The original 118 MB PNG reference pack is preserved outside runtime delivery. The current ground also uses an original generated asphalt colour, plus individually credited ambientCG dirt/damp maps. Current framing corrects the exposed upper sleeve ends of the first visual pass.

The stylised original hooded opponent remains unfinished; do not claim a donor character rig was
integrated. No Claudefare implementation, Fab clips, donor Tripo/Manus models or donor audio imported.

## Commands

Node 24, Chromium, Blender 4.3.2 available in this session. `npm ci`; `npm run dev` (port 5173). `npm run typecheck`; `npm test`; `npm run build`. For input-driven browser validation, start `npm run preview -- --port 4173`, then `ONSITE_URL=http://127.0.0.1:4173 npm run test:browser`. Video requires `npx playwright install ffmpeg`. `npm run evidence:layout` regenerates the plan. `npm run evidence:route` requires dev server and drives a test-only physical route fixture with bots disabled. It does not ship in the production bundle.

Latest residential pass: typecheck/build and **22 tests passed**; continuous flat traversal passed (1,915 ticks). The final input-driven encounter eliminated all three bots, captured and reset, with 88 health. Software mean **589.91 ms / ~1.70 FPS**, 149 frames; real GPU unverified. Results and evidence are in [CURRENT-VALIDATION.md](CURRENT-VALIDATION.md). The preceding dirt-pass captures/timing are retained under `evidence/dirt-pass/` and VALIDATION-0ce5a14.md. Do not present those as measurements of the expanded homes.

## Highest-value next work

1. Controlled real-GPU profiling and player feedback. Cloud SwiftShader is slow; no smooth-play claim. Current adaptive software mode disables MSAA and shadows and uses half pixel ratio. Four courtyard and two interior local lights are shared with hardware mode. Hardware enables MSAA and sun shadows. Distinguish both visually and quantitatively.
2. Art pass against the original concept: complete the flat bathroom and domestic materials, more facade/room variation, a convincing black-clothed character rig, and further first-person hand/reload refinement. The dirty floor, grass, litter and sleeve continuation are implemented; see DIRT-PASS.md. Planted cover and detailed facade/rail components are implemented; current result is improved but not concept-art fidelity.
3. Human combat tuning: three-bot pressure, readable reaction windows, recoil recovery, movement speed and clear hit/death feedback. Browser automation proves mechanics, not satisfaction.
4. Expand physical navigation regression scenarios for multi-bot separation at doorways, cover, stairs and damage while transitioning floors. Existing tests cover isolated ascent/descent; not every crowd case.
5. Reduce the large Rapier/Three.js JS payload and unused preserved legacy runtime asset delivery. Networking stays deferred. Modern Claudefare is an unlicensed reference only; architecture notes in DONOR-MAP.
