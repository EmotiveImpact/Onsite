# Current WWB integration validation

18 October 2026. Node 24.19.0, Chromium 154.0.8037.57, Blender 4.3.2, Three.js 0.186.1 and Rapier 0.21.0.

## Results

- `npm run typecheck`: passed for the actual WWB integration and route fixture.
- `npm test`: retained 10 legacy simulation regressions; current suite adds 7 tests for layered paths, real WWB bot ascent/descent of both stairs, real WWB player ascent/descent, lobby doorway traversal, outer-wall collision/spawn protection and continuous court → stair A → gallery → stair B traversal. The legacy tests are not counted as proof of the new weapon/bot runtime.
- `npm run build`: passed. Main JS approximately 5.08 MB / 1.87 MB gzip; Vite's >500 kB chunk warning remains. No claim that the payload is optimized. Preserved original procedural textures remain in public and are copied into dist even though the active game loads the newer PBR maps.
- Production-preview Chromium interaction run passed **10 recorded checks**, no page errors and no failed requests. Loaded models/materials, actual pointer lock and mouse look, ADS, automatic fire/recoil/reload, pause/resume, jump/landing, doorway movement, live combat, capture/victory and reset. The player eliminated all 3 bots with normal mouse/keyboard events and ended with **76 health**. No teleport/damage hooks were used in that run.
- Earlier development-server attempts had aborted dependency requests; production preview isolates that development pipeline and had no failures. Earlier combat attempts ended in player death, which was observed, but did not satisfy the full interaction run. Encounter tuning changed from omniscient wave hunting to normal perception/roaming, and automation aim tracking was corrected. Those failed attempts are not reported as passed checks.

## Performance, honestly

The successful combat run used **SwiftShader software rendering**, 1100×700 viewport at 0.5 render pixel ratio, MSAA/shadows/world point lights disabled. Mean wall-clock frame duration **203.95 ms over 244 active samples (~4.9 FPS)**. Final recorded render counters: **36 calls, 40,994 triangles**, summed across world and weapon passes. This is slow and not an acceptable performance target. The sample includes interaction and screenshot overhead and is not a controlled GPU benchmark. It is not directly comparable to the older 324 ms result with different scene/settings.

Hardware mode retains shadows/local lights and a higher pixel ratio. **No real-GPU performance or visual pass has been verified.** A controlled GPU profile remains the highest-priority performance task. The renderer and route capture must not be described as smooth or production-ready.

The separate continuous route capture completed all five positions with no page errors: court, stair A, upper gallery, stair B and return to ground. Its final 180-sample software mean was 214.44 ms; this is another software measurement, not GPU validation. The fixture initially had a TypeScript syntax error, which was corrected and added to the typecheck scope before successful completion.

## Actual runtime evidence

- [First-person weapon](evidence/first-person.png), [aiming](evidence/aiming.png), [live combat](evidence/combat.png), [victory](evidence/victory.png).
- [Gameplay recording](evidence/combat-input.webm): automated real pointer-lock input in the active production build; shows the actual low cloud frame rate. Not a generated image or cinematic render.
- [Interaction report](evidence/report.json).
- [As-built plan](evidence/as-built.svg) and [geometry/spawn data](evidence/layout.json), generated from `src/onsite/level.ts`.
- Courtyard/stair/gallery screenshots come from `tests/route-harness.html`, explicitly labelled **scripted walking, bots disabled**. It drives the same WWB physical player, geometry and renderer through a continuous route; it is not a human combat session or a substitute for the separate combat recording. In this fixture the weapon remains lowered while the route runs; the first-person/ADS screenshots above show normal gameplay presentation.

The art is improved but still below the supplied concept-art quality. The stylised hooded character is not a final rig; architecture still needs variety and finer detail, and human playtesting is needed to judge weapon/combat feel. These limits are recorded, not hidden by the mechanical test results.

## Setup persistence

`npm ci`, typecheck, all 17 tests and build were rerun successfully after integration. Reusable `install_script` and `start_skill` were saved to the cloud environment configuration draft. The draft is unpublished; applying it to future environments requires review/save and environment publication in settings. No environment publication, site deployment, push or merge was performed. Fresh-task restoration has not been verified.
