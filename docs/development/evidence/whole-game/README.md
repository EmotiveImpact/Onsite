# Whole-game tranche: runtime evidence

All captures use Chromium/ANGLE SwiftShader, **software rendering**. Real-GPU performance
remains unverified. The native-resolution stills use 1280 × 720 at DPR 1 through the
inspection override; input-driven combat uses 1100 × 700 at the normal DPR 0.5.

- `before/`: baseline `483cc0a`, frozen server 4183; reload fixture imports exact baseline source.
- `after/world/`: integrated assets and camera poses, captured before the final loader-only
  allocation correction. The correction changes which unused materials are allocated;
  it does not change visible geometry or material values. The separate operator-yard
  capture uses the final `3284c4d` build and starts at that viewpoint.
- `runtime-flow/`: actual production menu, original 3D kit, saved settings and map switching.
- `interface-fixture/`: isolated frontend with actual Input listeners and operator asset;
  synthetic round results only, **not combat evidence**. The final nine groups were
  rerun with the finished operator export after both encounter runs.
- `court/` and `reach/`: actual keyboard/mouse encounters. No camera placement or synthetic kills.
- `before/reload/` and `after/reload/`: frozen reload-clock presentation fixtures from the same
  camera, including actual weapon/hand rig probes. These are not gameplay captures.
- `checks/`: test/build/typecheck logs and intermediate branch compilation records.
- `failed-reach/`: preserved pre-fix failure at `267e349`: all six opponents were
  defeated, but donor score-race completion froze the timer/statistics before capture.
  Final capture-round regressions and encounter reports document the resolution.

## Correcting an inherited capture label

The old art-capture script called its actors “frozen”. Inspection of the runtime proved that
`?inspect` only enables camera placement: the bots continue updating. The original JSON reports
are retained untouched, but that label is incorrect. Fixed camera positions still match; actor
poses and time-of-day animation samples can differ. The script now records actor positions and
labels them active. The original multi-view after screenshot had an empty operator yard because
the bot had moved by the last view; the separate final operator capture starts at that view.

World screenshots are useful material/geometry evidence, not proof that a human traversed a
route. Use encounter reports and capsule/navigation tests for those claims. No image here is
concept artwork or a real-GPU benchmark.

## Matched viewpoints

| Change | Before | After |
| --- | --- | --- |
| Operator, same yard camera | [Baseline](before/world/operator-yard.png) | [Articulated operator](after/world/operator-yard.png) |
| Reload, 35% clock | [Baseline](before/reload/reload-35.png) | [Continuous reach](after/reload/reload-35.png) |
| The Corner interior | [Flat stock](before/world/corner-interior.png) | [Blender stock](after/world/corner-interior.png) |
| Washhouse grounding | [Baseline](before/world/washhouse-square.png) | [Contact patches](after/world/washhouse-square.png) |
| Player entry | [Baseline title](before/title.png) | [Current title](runtime-flow/title-reach.png) |

The title comparison demonstrates the changed interface and is not a fixed-camera
world-art comparison. The operator camera matches, but active bot poses may differ.
Menu views include the [default kit](runtime-flow/operator-default.png),
[hood-down/high trainers](runtime-flow/operator-high-down.png) and
[narrow settings layout](runtime-flow/settings-narrow.png).

## Input-driven capture

[Reach combat excerpt](reach/combat-excerpt.webm) is a 25-second stream-copy excerpt
from the final automated keyboard/mouse encounter, starting 145 seconds into the
315.68-second recording. It preserves the recorded pace; the game is running through
SwiftShader at roughly 1–2 rendered frames per second, not smoothly on a real GPU.
Full videos remain under `test-results/whole-game-*-verified/` locally. The final
[Court report](court/report.json) and [Reach report](reach/report.json) retain complete
combat/reset snapshots and frame-time samples; [Reach victory](reach/victory.png)
shows the completed result.
