# Current validation: ONSITE whole-game tranche

19 October 2026. Continue from `codex/onsite-game-foundation` and read the
[whole-game goal](../ONSITE-GOAL.md) and [implementation/evidence log](WHOLE-GAME-PROGRESS.md).
The log supersedes the historical results below. No merge or deployment.

**84 tests**, typecheck and production build pass at runtime source `3284c4d`.
The production player flow and isolated keyboard/persistence fixture pass. Both
full input-driven encounters pass: Court **10 checks / three bots**, Reach **nine
checks / six bots**, followed by capture, exactly-once local results and reset.
Software frame means are **518.33 ms Court / 694.25 ms Reach** (roughly 1–2 FPS).
Real-GPU performance remains unverified. The final-shot/deadline freeze found during
Reach verification is fixed and regression-tested; the original failure is retained.

# Previous validation: Heron Reach scene depth

19 October 2026. Current review branch: `codex/heron-reach-scene-depth`, stacked on
`codex/heron-reach-textures-dressing`. The [scene-depth work log](../maps/heron-reach-32/art/SCENE-DEPTH-2026-10-19.md)
records exact source checkpoints, sources, matched screenshots, costs and all reports.
Nothing from this pass has been merged or deployed by this session.

- **55 tests passed**, no skips; typecheck and production build passed.
- Nine DPR 0.5 and four DPR 1 fixed-camera views passed without page/console/request
  errors. Before/after requested camera poses match exactly. These are inspection
  fixtures rendered by Chromium 154 / ANGLE SwiftShader. Correction: the earlier
  “frozen bots” label was inaccurate; inspection mode leaves them active.
- **Heron Reach: 9 checks passed**, six bots defeated, capture and reset. 76 health,
  82 shots / 37 hits. Final 360 active samples: **676.45 ms/frame (~1.48 FPS)**.
- **Heron Court: 10 checks passed**, three bots defeated, capture and reset. 84 health,
  27 shots / 12 hits. Final 135 active samples: **588.57 ms/frame (~1.70 FPS)**.
- An initial Reach run died after five kills. Its state/log/screenshot are retained.
  The verifier had held fire through extra snapshots and aim updates; the corrected
  normal-input burst loop preserves the full victory assertion. Final 28 bursts
  averaged 2.93 shots, maximum three. No game state was altered by the verifier.
- The physical solids, navigation and WWB gameplay modules remain unchanged.
  New render assets add 621,826 bytes and 5,888 triangles. Fifteen exported primitives
  exceed the initial twelve-batch target by three; eight material slots do not mean
  eight draws.

These slow software runs include automation overhead. **Real-GPU performance remains
unverified and explicitly deferred.** Local point lights remain unshadowed; scene
reflections and richer interior/character presentation are unfinished. Passing
checks does not establish AAA appearance, smooth play or 32-player online readiness.

## Previous seven-item art pass — historical results

### Heron Reach visual pass

19 October 2026. The current art work is on `codex/heron-reach-textures-dressing`,
with seven focused review branches. Nothing from this pass has been merged or deployed by this
session. See the [visual work log](../maps/heron-reach-32/art/ART-PUSH-2026-10-19.md) for the review
stack, exact software-rendered evidence and current results. The residential report below is
historical and does not describe the combined Heron Reach build.

Final combined source: all 43 tests, typecheck and production build passed; eight matched
inspection views and the three-mode texture/fallback probe passed. Both final input-driven
encounters passed: Heron Reach nine checks/six bots and Heron Court
ten checks/three bots, each capturing and resetting without page/request errors. Software frame
means were 680.89 ms and 563.57 ms respectively, around 1–2 FPS.
Real-GPU benchmarking is explicitly deferred and remains unverified.

## Earlier South London residential pass — validation

18 October 2026. Blender 4.3.2, Node 24.19.0, Chromium 154, Three.js 0.186.1, Rapier 0.21.0.
Baseline: `0ce5a14`; [previous results](VALIDATION-0ce5a14.md) retain that pass's screenshots and
461.57 ms timing. They are not measurements of this expanded scene.

## Implemented

The existing WWB runtime and single Rapier/layered-navigation architecture remain active. The
Blender residential pass replaces upper window boxes with stock-brick homes, deeper openings,
white frames, curtains/blinds, ribbed concrete, 20 balconies and closed rear elevations. Six
terraced houses and two point blocks expand the visual surroundings. An original overcast sky
dome replaces the rural background while the credited HDRI remains the lighting source.

**One accessible home** occupies the former north-west plant room: kitchen/living area, bedroom,
plaster finishes, radiators and original furniture. Its furniture and partition use authoritative
collision solids; existing court/lobby doors remain connected. The playable bounds remain
**36×30 m**, with both stairs and the continuous 3 m gallery. Higher private balconies and the
surrounding houses are visual-only; do not claim they are traversable neighbourhood routes.

Final estate: **6,773 editable render objects → 25 material meshes**, **17,791,304-byte GLB**.
Original art and previous dressing remain. Generated stock-brick colour is reused from the
project's original texture pack, with recorded source/runtime hashes. Four South London
photographs were visually studied; no photograph pixels or unlicensed donor assets were imported.
See [reference and Blender workflow](SOUTH-LONDON-HOMES.md).

## Verification

- `npm run typecheck`: passed. `npm test`: **22 passed**, no skips (10 retained legacy,
  9 current WWB navigation/physics tests, 3 asset/collision tests). Actual bot/player capsules
  traverse both stairs and the furnished flat; bed collision stops the player.
- `npm run build`: passed. Main JS **5,119.15 kB / 1,881.14 kB gzip**. The >500 kB chunk
  warning remains.
- Visual review caught UV/colour-layer corruption and missing rear enclosure. Both were fixed.
  Export now snapshots corner colours safely and supplies white tint for untinted geometry
  before joining. An asset regression checks stock facade colour neutrality and opacity.
- Early inspection attempts caught aborted Vite dependency requests. The longstanding dev server
  was restarted to clear stale optimized dependency URLs. The final five-view inspection passed
  with no page or failed/HTTP-error requests.
- The first full-round run reached victory at 28.58 simulation seconds, 76 health, before the
  automation's exact capture waypoint. The old route helper wrongly threw on that round end.
  It now accepts `won` while preserving the mandatory victory assertion and reset check.
  [Original automation failure/state](evidence/homes/capture-before-waypoint.json) shows the game
  had already won; it is kept separate from the final passing run.
- Blender commands use `--python-exit-code 1`; exceptions now fail the build command.
- The full builder was not rerun destructively from an empty scene. The incremental homes
  builder and final export were executed on the preserved estate. Manual changes should be
  preserved before rebuilding either authored collection.

## Evidence contexts

The `homes/` evidence directory contains the final five fixed-camera inspection stills: homes,
living room, bedroom, gallery and neighbourhood. These use the actual renderer, bots disabled,
1280×800, pixel ratio 1 with sun shadows. The neighbourhood image is an elevated inspection
camera, not an accessible player position. These stills are not performance measurements.

[Courtyard homes](evidence/homes/homes.png) · [Living/kitchen](evidence/homes/living.png) ·
[Bedroom](evidence/homes/bedroom.png) · [Gallery](evidence/homes/gallery.png) ·
[Neighbourhood inspection](evidence/homes/neighbourhood.png) · [Inspection report](evidence/homes/report.json).

A separate physical route fixture continuously walks the shipped WWB player from its normal
spawn, through Flat 01 and back out. It has bots disabled and does not teleport after spawn.
The route passed all four checkpoints in **1,915 ticks**, with no page/request errors.
Its final 180-sample software mean was **611.46 ms (~1.64 FPS)** at 1280×800 / 0.5 pixel ratio,
no MSAA/sun shadows, six local world lights; 33 final calls / 215,051 triangles. This is slow,
includes capture overhead, and is not a hardware benchmark.

[Continuous flat walk video](evidence/homes/flat-walk.webm) · [Physical route report](evidence/homes/route-report.json).
The final normal mouse/keyboard production-preview run passed **10 checks**: loading, pointer
lock/look, ADS alignment, automatic fire/recoil/reload, pause/resume, jump/landing, doorway
movement, three-bot combat, capture/victory and reset. **88 health**, **41 shots / 14 hits**;
victory at **29.20 simulation seconds**. Reset report confirms player health 100 and all
three bots alive at 100 health. No page errors or failed/HTTP-error requests.

Current combat software measurement: **589.91 ms/frame (~1.70 FPS)** over **149 active samples**,
1100×700 viewport at 0.5 pixel ratio, no MSAA/sun shadows, six local world lights. Final counters:
**81 calls / 240,710 triangles** across world and weapon passes. Other browser/Blender jobs had
finished before this measurement. Automation/capture overhead is included. This is slower than
the prior pass's 461.57 ms sample; it is not smooth, controlled benchmarking or real-GPU evidence.

[Input-driven combat video](evidence/homes/combat-input.webm) · [Combat report](evidence/homes/combat-report.json) ·
[ADS](evidence/homes/aiming.png) · [Victory](evidence/homes/victory.png).

[As-built arena plan](evidence/as-built.svg) · [Flat 01 plan](evidence/home-plan.svg) ·
[Exact collision/spawn data](evidence/layout.json).

## Limits

The cloud uses SwiftShader software rendering, not a real GPU. Hardware mode enables MSAA and
sun shadows and has not been profiled. The 51 MB production directory still includes
unused retained legacy assets and original donor copies; download/memory optimization remains.

The home is a first furnished interior: bathroom, working doors/appliances, domestic fabric/wood
textures and interactions remain unfinished. The original hooded bot visual still needs a
proper character rig. Surrounding house exteriors and point blocks are context geometry; a
larger accessible neighbourhood would require a separate collision/nav/gameplay expansion.
No production-quality or smooth-performance claim is made.

These runtime checks preceded publication. For the subsequent user-requested Claude handoff,
typecheck, all 22 tests and the production build were rerun successfully against `debebb4`;
only documentation changed afterward. Browser results above were not rerun for that documentation
change. No GitHub Actions workflows were configured at publication inspection. Deployment was
not requested. Previous checkpoints and all original reference material remain.
