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
2,145 editable architecture objects export to 14 material meshes, with metric UVs and vertex occlusion.
Editable render, collision guides, navigation guides, donor dressing and review-lighting collections
are separate. Runtime lighting is rebuilt in Three.js; Blender lamps do not automatically transfer.

The first-person model is IRONLINE's M4A1 + DJMaesen/Cransh posed hands, with author/source/CC BY
records and both external WebP arm textures. `src/onsite/DonorRifle.ts` adapts the art to WWB's Arsenal;
ammo, hitscan, timing, recoil and reload completion remain WWB-owned. The original two-bone reload
reach uses no Fab motion tracks. The original procedural weapon stays available in the source.

Seven individually verified Poly Haven props and the Bambanani Sunset HDRI were imported through
IRONLINE. The car, bins and gallery barrier have colliders measured by Blender; routes must remain
height-aware. `dressing.json` drives both visible placement and separate collider dimensions. Existing
WWB-sourced utility boxes/security lights and original Blender benches remain. Exact notices at
`public/licenses/DONOR-ASSETS.md`, provenance/hashes at `public/models/donors/provenance.json`.
The original 118 MB PNG reference pack is preserved outside runtime delivery.

The stylised original hooded opponent remains unfinished; do not claim a donor character rig was
integrated. No Claudefare implementation, Fab clips, donor Tripo/Manus models or donor audio imported.

## Commands

Node 24, Chromium, Blender 4.3.2 available in this session. `npm ci`; `npm run dev` (port 5173). `npm run typecheck`; `npm test`; `npm run build`. For input-driven browser validation, start `npm run preview -- --port 4173`, then `ONSITE_URL=http://127.0.0.1:4173 npm run test:browser`. Video requires `npx playwright install ffmpeg`. `npm run evidence:layout` regenerates the plan. `npm run evidence:route` requires dev server and drives a test-only physical route fixture with bots disabled. It does not ship in the production bundle.

## Highest-value next work

1. Controlled real-GPU profiling and player feedback. Cloud SwiftShader is slow; no smooth-play claim. Current adaptive software mode disables MSAA, shadows and world point lights and uses half pixel ratio. Hardware mode retains shadows/local lighting. Distinguish both visually and quantitatively.
2. Art pass against the original concept: local grime and facade variation, a convincing black-clothed character rig, and improved first-person sleeve cuffs/hand anatomy. Planted cover and detailed facade/rail components are implemented; current result is improved but not concept-art fidelity.
3. Human combat tuning: three-bot pressure, readable reaction windows, recoil recovery, movement speed and clear hit/death feedback. Browser automation proves mechanics, not satisfaction.
4. Expand physical navigation regression scenarios for multi-bot separation at doorways, cover, stairs and damage while transitioning floors. Existing tests cover isolated ascent/descent; not every crowd case.
5. Reduce the large Rapier/Three.js JS payload and unused preserved legacy runtime asset delivery. Networking stays deferred. Modern Claudefare is an unlicensed reference only; architecture notes in DONOR-MAP.
