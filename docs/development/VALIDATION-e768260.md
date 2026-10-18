# Blender estate / WWB integration validation

18 October 2026. Node 24.19.0, Chromium 154.0.8037.57, Blender 4.3.2, Three.js 0.186.1 and Rapier 0.21.0.
This records the Blender/donor visual pass after checkpoint `d5faf61`; it supersedes that checkpoint's screenshots and timing figures.

## What is running

`index.html` loads the actual WWB Player, Physics, Input, GameLoop, Arsenal, Bot, effects and round rules through the ONSITE encounter wrapper. The architecture now comes from an editable Blender estate, exported to a 7,934,856-byte GLB: 2,145 editable architecture objects, merged to 14 material meshes. Render geometry, collision guides, navigation guides and donor dressing are separate. Five PBR texture sets cover six material roles; the original 118 MB reference PNG pack is not served at runtime.

The active rifle and posed hands are individually credited IRONLINE art derivatives, with original ONSITE reload IK driven by WWB's reload clock. Seven individually verified Poly Haven prop models and one HDRI are also imported through IRONLINE. The original hooded bot model remains unfinished. Claudefare stays reference-only. See [donor map](DONOR-MAP.md), [Blender workflow](BLENDER-LEVEL.md) and [asset notices](../../public/licenses/DONOR-ASSETS.md).

## Results

- `npm run typecheck`: passed, including both browser fixtures.
- `npm test`: **20 tests passed**. Ten retained legacy tests are regressions for the old prototype, not proof of the current runtime. Seven current tests exercise layered paths, actual WWB bots and player capsules up/down both stairs, doorway traversal, wall collision/spawn protection and a continuous ground/gallery route. Three new tests check render-only GLB export/occlusion/layout provenance, imported hashes/external rifle textures and actual player collision with the donor car.
- `npm run build`: passed. Main JS 5.114 MB / 1.880 MB gzip; Vite's >500 kB chunk warning remains. Full `dist` is about 31 MB. Preserved legacy runtime maps still copy into `dist`; payload cleanup remains outstanding.
- Production-preview browser run: **10 recorded checks passed**, no page errors or failed/HTTP-error requests. Actual pointer lock/mouse look, imported rifle/ADS alignment, automatic fire/recoil/reload, pause/resume, jump/landing, doorway movement, live combat, capture/victory and reset. All **three opponents eliminated**, **64 health** remaining, **33 shots / 12 hits**, victory at 27.47 simulation seconds. Input automation uses normal mouse/keyboard events and read-only state/route probes; no damage, teleport or health hooks.
- The full-round check now requires victory; a run with only two kills cannot pass. An earlier attempt ended with two kills and player death. That death screen/report is retained separately. Automation was corrected to track moving targets without an extra aim-then-fire frame delay on slow software rendering. Combat difficulty and damage were not changed for the successful rerun.
- Separate continuous physical browser route passed: court → stair A → gallery → stair B → ground, 3,630 ticks, no page errors. Same WWB player/collision and renderer, bots explicitly disabled. No teleports after spawn. Bot ascent/descent is covered separately by the actual-brain simulation tests.
- Frozen-pose presentation check passed at idle and 35%, 55%, 85% of the real reload clock. Finite transforms, visible magazine extraction and left-hand reach within 1.5 cm at both extraction phases. This caught and fixed the imported rig's independent hand-control branch. Pose images are inspection fixtures, not a live reload recording.

## Performance and limitations

The successful combat run used **SwiftShader software rendering**, a 1100×700 viewport at 0.5 render pixel ratio, no MSAA, shadows or world point lights. Mean wall-clock frame duration was **402.84 ms over 143 active samples (~2.48 FPS)**. Final recorded render counters: **64 calls, 171,648 triangles**, summed across world and weapon passes. No other browser/render capture ran alongside that measurement. Interaction and screenshot overhead remain included; this is not a controlled benchmark.

This is slow and unsuitable as a performance target. The richer scene is more expensive than the earlier simplified checkpoint. Hardware mode uses a higher pixel ratio, sun shadows and local lights; **no real-GPU performance or visual pass has been verified**. Do not describe the cloud capture as smooth or production-ready.

The physical route's final 180-sample software mean was **385.17 ms (~2.60 FPS)**, with 26 calls / 133,860 triangles. It was captured before the final leaf detail and reload-pose adjustments; collision/layout did not change. The latest combat and presentation images include those final visual changes. The high-resolution courtyard presentation still uses a 1280×800 viewport at pixel ratio 1 with sun shadows enabled for inspection; it is not the configuration measured in the combat sample.

## Actual runtime evidence

- [Courtyard and imported weapon](evidence/courtyard-weapon.png): actual Three.js view, labelled presentation fixture, bots disabled.
- [First-person](evidence/first-person.png), [aiming](evidence/aiming.png), [combat](evidence/combat.png), [victory](evidence/victory.png), [interaction report](evidence/report.json).
- [Input-driven gameplay video](evidence/combat-input.webm): the successful production-preview run, including real cloud frame pacing. No generated images or cinematic render.
- [Reload 35%](evidence/reload-35.png), [55%](evidence/reload-55.png), [85%](evidence/reload-85.png), [pose report](evidence/presentation-report.json).
- [Stair A detail](evidence/stair-detail.png): fixed inspection position in the same runtime renderer, bots disabled. [Continuous route stair A](evidence/stairs.png), [upper gallery](evidence/upper-route.png), [stair B](evidence/stair-b.png), [route report](evidence/route-report.json).
- [Observed death](evidence/observed-death.png) and [failed-attempt report](evidence/observed-death.json), kept distinct from the passing run.
- [As-built plan](evidence/as-built.svg) and [exact geometry/spawn data](evidence/layout.json), generated from collision solids including measured donor obstacles.

Remaining work: detailed black hoodie/joggers/trainers character rig and animation; first-person sleeve/cuff refinement; local grime and architectural variation; human combat/play-feel feedback; real-GPU profiling and payload reduction. The current scene is an improved playable foundation, below the original concept-art target.

## Recovery and setup

All prior unpublished work was committed as `d5faf61` before this pass. Original concepts, models, textures, tests and research are preserved. Full donor trees are clean, ignored, and absent from the index and production bundle. Their pinned commits and per-source boundaries are in `research/SOURCES.json`.

Reusable cloud install/start instructions were saved to the environment configuration draft earlier. That draft remains unpublished and fresh-task restoration has not been verified. No push, merge, environment publication or site deployment was performed. See [handoff](HANDOFF.md) for commands and next work.
