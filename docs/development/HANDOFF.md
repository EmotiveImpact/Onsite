# ONSITE continuation handoff

## Direction and active entry

London browser FPS, bots first. The user's attached ground/upper floor plans were reviewed in chat and treated as proposals. Their 36×30 m footprint, 24×18 m court, 3 m gallery, central 18×12 m void and two stair cores guide the implementation. [As-built plan](evidence/as-built.svg) and [exact solids/spawns](evidence/layout.json) are generated from code, not the attached artwork. Stair door offsets and room openings were adjusted for physical circulation. No claim that the proposed image itself is an as-built drawing.

Active: `index.html` → `src/onsite/main.ts`. Actual WWB runtime modules in `src/wwb`; original ONSITE `Encounter`, `View`, `level` and `navigation` adapters in `src/onsite`. Read [DONOR-MAP.md](DONOR-MAP.md) for exact reuse. The old prototype remains at `/legacy.html` during development. Do not restart with another controller or replace working combat with a toy implementation.

## Recovery and preserved work

[CHECKPOINT.md](CHECKPOINT.md) records the verified ~993 MB pre-integration archive outside this checkout and safe restore commands. All original concept art, generated images, original Blender sources, original PBR sets and tests remain. No merge/push/deploy. Three full reference trees remain ignored in `research/reference-clones`, with exact commits in `research/SOURCES.json`. Never recursively stage that folder. The local archive is not remotely backed up.

## Current interaction

WASD, mouse, LMB automatic carbine, RMB ADS, R reload, Shift sprint, Space jump, C crouch/slide, Escape pause. Three opponents use WWB's normal perception/roaming/cover/combat state machine, targeting the player only. Clear all three then stand within 4 m of the centre on ground level for 2.5 s. Death or 180 s timeout loses the encounter. Reset restores actors/ammo/timer. No cloud backend, duel or multiplayer implementation.

Bot navigation is original layered geometry-derived nodes at 0.375 m horizontal spacing. Paths retain floor height. One Rapier world owns player and bot capsules. Bots use character-controller collision rather than height teleportation. Tests run real bot brains and real player capsules up/down both stairs. Only cardinal graph edges; no unsafe 2D path smoothing across the open void. Larger maps will need navigation optimization and robust replanning around dynamic blockers.

## Art and presentation

WWB procedural rifle and black gloves/sleeves replace the old basic weapon. Original additional support-hand magazine choreography; separate 52-degree viewmodel camera; ADS sight centred independently of world FOV. Preserve shot timing in the fixed-step Arsenal, never put combat decisions into animation callbacks. IRONLINE was studied, but no code/assets/tracks were copied; keep its mixed provenance caveats.

Original Blender opponent remains stylised with simple limb motion, not a production character rig. Original benches are reused. Two CC0 Poly Haven GLBs (utility box/security light) were imported through the audited WWB fetch/build trail. Five direct CC0 PBR sets serve six roles, including tinted stock brick. Records in `public/materials/pbr/provenance.json` and `public/models/polyhaven-provenance.json`. No donor Tripo/Manus models, audio, rigs or clips. See public licence notices.

## Commands

Node 24, Chromium, Blender 4.3.2 available in this session. `npm ci`; `npm run dev` (port 5173). `npm run typecheck`; `npm test`; `npm run build`. For input-driven browser validation, start `npm run preview -- --port 4173`, then `ONSITE_URL=http://127.0.0.1:4173 npm run test:browser`. Video requires `npx playwright install ffmpeg`. `npm run evidence:layout` regenerates the plan. `npm run evidence:route` requires dev server and drives a test-only physical route fixture with bots disabled. It does not ship in the production bundle.

## Highest-value next work

1. Controlled real-GPU profiling and player feedback. Cloud SwiftShader is slow; no smooth-play claim. Current adaptive software mode disables MSAA, shadows and world point lights and uses half pixel ratio. Hardware mode retains shadows/local lighting. Distinguish both visually and quantitatively.
2. Art pass against the original concept: stronger estate facade composition, local grime, planted cover, more convincing black-clothed character rig and first-person sleeves/hand anatomy. Current result is improved but not concept-art fidelity.
3. Human combat tuning: three-bot pressure, readable reaction windows, recoil recovery, movement speed and clear hit/death feedback. Browser automation proves mechanics, not satisfaction.
4. Expand physical navigation regression scenarios for multi-bot separation at doorways, cover, stairs and damage while transitioning floors. Existing tests cover isolated ascent/descent; not every crowd case.
5. Reduce the large Rapier/Three.js JS payload and unused preserved legacy runtime asset delivery. Networking stays deferred. Modern Claudefare is an unlicensed reference only; architecture notes in DONOR-MAP.
