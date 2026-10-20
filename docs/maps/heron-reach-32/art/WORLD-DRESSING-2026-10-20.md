# Heron Reach: scanned objects and living planting

20 October 2026. Branch `codex/heron-reach-world-dressing`, based on released main
`c583afeb32b3d82fe2d069b81076de9e993bf51c`. Recover the unchanged released implementation
from that commit or local checkpoint `checkpoint/onsite-before-world-dressing-2026-10-20`.
Review: [PR #21](https://github.com/EmotiveImpact/Onsite/pull/21), pushed and unmerged.
Production remains on released main. Branch publication triggers the existing
automatic Vercel preview; no manual deployment or merge was invoked.

## What changed

The [donor audit](../../../research/WORLD-ASSET-AUDIT-2026-10-20.md) found twelve
cleared scanned props already shipped for Heron Court but absent from Heron Reach.
This pass uses six appropriate variants in Reach, and adds newly downloaded
CC0 fern and clay-pot scans. It preserves the current WWB gameplay, physical
layout, layered navigation and original render assets.

| Placement | New instances | How it fits |
| --- | ---: | --- |
| Scanned refuse bags | 14 | Replace ten exact existing bag instances within their old footprints |
| Weathered air-conditioning units | 8 | Replace eight units on sealed roofs, with supported feet |
| Bin-store contents | 16 | Three closed rusty bins and one bag in each of four existing colliding stores |
| Workshop stock | 4 | Crate/box and flat tyre on the two existing lower shelves |
| Raised-bed ferns | 53 | Replace 22 selected weeds and fill spare soil with 31 additional clumps inside existing planter rims |
| Home planting | 8 | Four pots and four ferns on four existing H1 tables |

Total: **103 new instances**, retiring **40 exact original instances** (18 props
and 22 weeds). The original trees, shrubs, most weeds and existing workshop tools
remain. The first 72-instance iteration looked too sparse in runtime review;
31 additional low clumps now fill the seven larger beds. The smallest bed keeps
its existing close spacing. Original root centres retain at least 0.45 m clearance. These are render additions; no new colliders or navigation nodes are added.

The planner checks doors, storey support and actual loaded native bounds before
accepting placements. Missing assets retain the corresponding originals. Batches
share geometry and materials and are split by 24 m spatial tile and floor.
The kit adds no lights.

## Blender and provenance

- [Props builder](../../../../scripts/maps/art/build_heron_world_props.py),
  [packed source](../../../../assets/blender/heron-reach/world-props.blend),
  [manifest](../../../../assets/blender/heron-reach/world-props-manifest.json).
  Six individual metre-scale roots; the selected bin lid is closed, AC feet
  meet its base and the tyre is laid flat. Normal/data textures remain lossless;
  small repeated props use 512/256 px maps. The unused wheel rim was removed
  from the derived runtime kit.
- [Plants builder](../../../../scripts/maps/art/build_heron_world_plants.py),
  [packed source](../../../../assets/blender/heron-reach/world-plants.blend),
  [manifest](../../../../assets/blender/heron-reach/world-plants-manifest.json).
  Four original fern shapes, original leaf opacity and a clay pot with an
  original fitted soil insert. Fern colour/alpha is 1024 px, normal 512 px;
  pot colour/normal is 256 px, data maps 128 px.
- [Original downloads](../../../../assets/reference/world-dressing/source-manifest.json),
  publisher metadata, licence evidence, exact hashes and original glTF dependencies
  are preserved. `scripts/import-world-reference.py` verifies the pinned source files.
  Runtime loads only the derived GLBs.
- [Shipped notice](../../../../public/licenses/world-dressing-cc0.md) and
  [project provenance](../../../development/PROVENANCE.md) record the sources.
  No unlicensed mirror assets, Fab animations or additional donor engine code
  are imported.

These are separate Blender 4.3.2 additive files; the original 5.2 estate sources
are untouched. Render models contain no collision/navigation exports. Existing
Three.js lighting remains responsible for the final appearance.

Actual exported tabletop surfaces are at 0.7489127 m after the existing mesh
quantisation, while their physical/source top is 0.75 m. Pots sit at 0.7489 m to
meet the rendered surface. Fern stem anchors, including their basal heights,
seat into the exported pot soil. Tests inspect real decoded triangles, supports,
gates and stems rather than relying solely on authored bounding boxes.

The real Three.js loader test caught a reserved metadata name during preparation:
`extras.pivot` has loader behaviour and must not contain descriptive text. The
final plant export uses `originContract`; all decoded root transforms are finite.
The downloaded licence HTML retains its exact original bytes, including three
upstream mixed-indentation lines; authored files pass the whitespace check.

## Cost

| Kit | Download bytes | Unique triangles | Estimated decoded RGBA8 textures + full mips |
| --- | ---: | ---: | ---: |
| Six props | 1,924,688 | 7,337 | 14,680,036 bytes |
| Four ferns and pot | 212,300 | 9,376 | 7,864,312 bytes |
| Total | **2,136,988** | **16,713** | **22,544,348 bytes / about 21.5 MiB** |

Texture estimates exclude driver overhead and are not measured VRAM. Across all
103 placements the gross added geometry is 152,900 triangles before culling;
original retired geometry reduces the net addition. A download compressed with
WebP does not imply the same saving in GPU memory.

Final prop GLB SHA-256:
`a3f7ccc7e5b7ff67055811e480c6f24a01275ec774b422305d6f226ceb70bf4e`.
Final plant GLB SHA-256:
`f4b2f6fb690070ff44641e334edb3dada1449d59f94c70e4ca1f1a2e1350ed64`.

## Checks and runtime evidence

`npm test` passes **143 tests** (10 preserved legacy and 133 TypeScript tests),
with no skips. `npm run typecheck` and `npm run build` pass. The existing large
JavaScript chunk warning remains: the main chunk is about 5.40 MB before gzip.
The 16 added tests cover decoded geometry/supports, gates, planting, exact
replacement identity, independent asset failure and spatial instancing.

Frozen review build: `/tmp/onsite-world-dressing-final-dist`, preview port 4196.
Main script `index-D5D8OAM2.js`, SHA-256
`094513e43b3df22ee2dd562eed4233b16c2f3bffd0b901416c6931aaf4d341be`.
Before captures use the unchanged release build on port 4194, main script
`index-UnAVxv0V.js`, SHA-256
`47f60eae723149b82c78933b0071e23f829bf83c9e1234b7236709395e2d8a54`.

Matched fixed-camera evidence uses Chromium/ANGLE SwiftShader, 1280 × 720,
DPR 1. These are actual runtime inspection fixtures with active actors, not
concept art or a human-played performance benchmark.

| View | Before | After |
| --- | --- | --- |
| Raised-bed close-up | [Image](evidence/world-dressing/before/garden-ground-close.png) | [Image](evidence/world-dressing/after/garden-ground-close.png) |
| Larger planted bed | [Image](evidence/world-dressing/before/garden-large-planter.png) | [Image](evidence/world-dressing/after/garden-large-planter.png) |
| Workshop shelves | [Image](evidence/world-dressing/before/cycle-workshop-stock.png) | [Image](evidence/world-dressing/after/cycle-workshop-stock.png) |
| Bin store | [Image](evidence/world-dressing/before/north-bin-store.png) | [Image](evidence/world-dressing/after/north-bin-store.png) |
| Service-lane bags | [Image](evidence/world-dressing/before/corner-service-stock.png) | [Image](evidence/world-dressing/after/corner-service-stock.png) |
| Home tabletop | [Image](evidence/world-dressing/before/northwest-home-table.png) | [Image](evidence/world-dressing/after/northwest-home-table.png) |
| Garden Court | [Image](evidence/world-dressing/before/garden-court.png) | [Image](evidence/world-dressing/after/garden-court.png) |
| The Corner | [Image](evidence/world-dressing/before/the-corner.png) | [Image](evidence/world-dressing/after/the-corner.png) |

Visual review confirms supported objects, readable leaf cut-outs and fuller
large-bed planting. It also exposes unfinished work: the home furniture remains
very simple, broad lamp reflections are too bright, service areas lose detail in
shadow, and surrounding façades/ground still repeat visibly. This is an asset
and placement improvement, not a claim that the concept-art target is finished.

The exact final render placements, supports, bounds and per-root triangle counts
are preserved in [the decoded placement audit](evidence/world-dressing/placement-audit.json).

Run locally with `npm ci`, then `npm run dev`; open `/?map=heron-reach`.
Run `npm test`, `npm run typecheck` and `npm run build`. With the game served
on port 5173, normal encounters are:

```sh
ONSITE_URL=http://127.0.0.1:5173 OUT=test-results/world-dressing/court npm run test:browser
ONSITE_URL=http://127.0.0.1:5173 OUT=test-results/world-dressing/reach EXPECT_WORLD_DRESSING='{"replacements":18,"storeContents":16,"workshopContents":4,"ferns":53,"tableArrangements":4}' node scripts/maps/verify-heron-reach.mjs
```

`scripts/maps/capture-art-review.mjs` accepts `ONSITE_URL`, `OUT`, comma-separated
`VIEWS`, `EXTRA_ASSETS` and the same `EXPECT_WORLD_DRESSING` check. The fixtures
live in `scripts/maps/art-review-views.json`. Exact build/model hashes and
requested/actual camera positions are saved in each capture report.

Both final normal-input browser encounters pass serially on the frozen build:

| Map | Checks / combat | Frames | Mean / median / p95 frame time | Final draws / triangles |
| --- | --- | ---: | --- | --- |
| [Heron Court](evidence/world-dressing/browser/court.json) | 10; three bots, 15 hits / 29 shots | 115 | 497.47 / 501.5 / 633.4 ms | 85 / 269,187 |
| [Heron Reach](evidence/world-dressing/browser/reach.json) | 9; six bots, 30 hits / 75 shots | 360 | 721.57 / 714.9 / 883.7 ms | 479 / 1,301,780 |

Both clear the encounter, capture, persist exactly one completed result and
reset the player/opponents. Pointer lock, look, ADS alignment, automatic fire,
timed reload, pause, jump and movement pass. All final page/console errors and
failed requests are empty. Reach also asserts the exact final dressing counts.
Court does not load the new Reach kits.

These timing samples use SwiftShader, 1100 × 700, DPR 0.5, with no concurrent
browser/build/Blender workload. Automation overhead and differing combat states
are included; draw/triangle numbers are the final view, not averages. Approximate
rates are 2.0 FPS Court and 1.4 FPS Reach. They do not demonstrate a performance
improvement or smooth play. **Real-GPU performance remains deferred and unverified.**
Raw captures/video remain in ignored `test-results/world-dressing/`.

Eight final requested camera poses match exactly, with identical viewport/DPR;
both new GLB hashes match the final manifests. The extra large-bed camera also
passes actual Rapier capsule/support validation:
[camera report](evidence/world-dressing/camera-validation.json).
Initial partial/sparse framing remains only in ignored test results. The final
recorded images and reports are the accepted implementation at `2cef5c8`.

## Continue from here

The immediate gain is variation and credible small objects at playable eye level.
It does not finish the estate. The next valuable work is:

1. Furnish and light representative home interiors with coherent furniture sets,
   appliance/cabinet detail, curtains and varied household objects. Some existing
   authored chair, counter and utility-cabinet roots are unused; plan their
   collision/supports before placing large items.
2. Improve soil/grass/paving transitions, local contact shading and material
   consistency. Full-size scans alone cannot fix flat lighting or repeated walls.
3. Improve visibility/culling and obtain real-GPU frame/VRAM measurements before
   broad density increases. The architecture texture budget remains much larger
   than this kit.
4. Continue character motion, weapon choreography, spatial sound and human
   playtesting. These remain separate from environment dressing.

Open Claudefare stays reference-only. Further imports should answer a particular
scene need and have individual rights records; do not copy whole donor asset trees.
