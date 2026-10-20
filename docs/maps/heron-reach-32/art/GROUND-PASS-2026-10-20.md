# Heron Reach ground and growth pass

20 October 2026. Final implementation/source checkpoint:
`623bc24ad98aa60db86f41b50da6e9dae12daeb4` on `codex/heron-reach-ground-growth`,
above completed building evidence `ca97cd49e96ffff97d0259e48e9308f794202c72`.
Initial ground source is retained at `71501c1`; the plane-only correction is
`16ef2cd`. Its original pre-rebase artifact source was `0afdea5`, with identical
runtime content. The planter revision is `c912eab`; the final grass/weed winding correction is `623bc24`.

All implementation checks pass. Review prompted fuller boundary trees, six varied low
clumps per raised bed and a scoped correction of inverted weed leaves. Final seven-view
review is accepted. Both serial normal-input encounters pass, with no errors or
failed requests. No merge or production deployment; the existing
PR integration may build a preview.

## What changed

Original additive Blender geometry breaks up uniform ground with 131 irregular
soil pockets, 89 low moss/edge deposits, 45 small loose-leaf drifts and soil rings
around the existing 20 trunks. It adds 53 low ground weed clumps and six varied clumps in each of
the eight existing raised planters: ten leafy shrubs, 22 broad low rosettes and
16 upright weeds. Planter roots meet the existing 0.85 m soil
surface; transformed plants fit inside the 120 mm rims and stay below 1.25 m.
Sixteen existing London-plane LOD1 trees occupy unreachable north/south pavement,
with trunk and canopy clearances; no new trunk is placed on a playable route.

The deterministic planner uses actual ground slabs, grass finish heights, existing
dressing and protected route/objective/doorway areas. An offline exporter writes a
minified public plan; the browser imports only the small validator/density helper,
not the planner or its foliage manifest. Existing dressing creates physics before
the additive render-only placements are merged. Physical geometry, collision,
layered navigation, movement, bot and combat systems are unchanged.

| Addition | Measured source/export cost |
| --- | --- |
| Ground detail | 5,240 triangles; 57 spatial/material batches on 24 m tiles; 158,884-byte GLB |
| Instanced weeds/shrubs | 22,256 triangles; ground plus plants totals 27,496 triangles |
| Sixteen perimeter trees | 23,408 instanced triangles; two-asset kit has 2,926 triangles and four material primitives; 36,640-byte GLB |
| Runtime placement plan | 221,414 bytes; three new runtime files total 416,938 bytes before HTTP compression |

Both GLBs contain no embedded images/textures. Trees share the already-loaded
`hr_bark_plane` and `hr_leaf_plane` materials.
Ground reuses existing soil/grass PBR maps and the existing leaf-litter atlas.
These are asset/geometry costs, not observed frame time or net frame submissions;
grass masking removes some original instances and visibility varies by camera.

## Grass and weed orientation correction; fallback

Decoded `GRASS_CLUMP_A–D` meshes contain 588 geometrically downward-wound faces,
despite authored normal Y values of +0.874 to +0.923. Double-sided shading reverses
those normals when viewed from above, explaining the dark appearance. Only 427
faces have a negative dot against their tilted authored normals; asset-root face
Y is the tested correction criterion. The scoped helper clones geometry and flips
downward triangle indices, preserving normals, UVs, colours and source geometry.
It is idempotent for corrected exports. The foliage builder also fixes future
blade winding; the shipped original foliage kit is retained. No material tint,
unlit shader or blanket foliage-normal change substitutes for the correction.
Initial broad views show lit olive blades replacing the earlier black outlines.
Thin blades may still alias at DPR 1. The enlarged planter close-up then exposed
black rosette leaves from the same source error: 66 inverted strip triangles in
WEED_TUFT_A, 30 in WEED_TUFT_C and 30 blade triangles in WEED_TUFT_B. The correction
reverses exactly these 126 faces. A/C strip selection requires every transformed
corner normal Y > 0.98 and a downward geometric face; B is scoped to its separate
hr_grass_blade primitive. All twelve upright card triangles keep exact indices,
including four with downward geometric Y. Attributes/materials and placements
stay unchanged. Future strip_leaf source winding is corrected without rebuilding
the original foliage kit; its SHA256 remains
`2dcd63bcdd13cf3d8f57ff51f0c2b95373b85cd6adc3897ab5a5469ca2b4ba8a`.
The failed [close-up](evidence/ground-growth/initial-weed-shading/garden-ground-close.png)
and [seven-view report](evidence/ground-growth/initial-weed-shading/report.json)
are retained as a superseded shading iteration. The final close-up shows lit green
leaves in place of the black silhouettes, and all seven final views are accepted.

The existing grass owner keeps every original random transform draw, then compacts
accepted instances with an independent coordinate hash. Soil density is 0.13 and
tree-ring density 0.04; elsewhere it remains 1. Retained transforms and unaffected
later tiles match the baseline. Masking activates only after explicit successful
ground loading. Failed ground loading preserves baseline grass; failed plan HTTP,
JSON or validation preserves original kit placements and grass and skips the tree
kit request. Missing winter materials skip the affected additive LOD asset; missing
leaf material hides only the extra loose leaves. Normal browser checks reject
ground fallback warnings, so graceful fallback cannot count as a successful art pass.

## Provenance and exact artifacts

All new planning, mesh generation and correction code is original ONSITE work.
No external model, donor code or new texture pixels were imported. Editable sources:
[ground-detail.blend](../../../../assets/blender/heron-reach/ground-detail.blend) and
[ground-trees.blend](../../../../assets/blender/heron-reach/ground-trees.blend).
The latter appends the two existing London-plane LOD1 collections from
[winter-trees.blend](../../../../assets/blender/heron-reach/winter-trees.blend), SHA256
`cef4a4bb25c814a23e8b3264043d89757e7871b2d2e67acf16fdd3fa62eb35ad`.

The [ground manifest](../../../../assets/blender/heron-reach/ground-detail-manifest.json),
[tree manifest](../../../../assets/blender/heron-reach/ground-trees-manifest.json) and
[construction/regeneration record](GROUND-GROWTH.md) record mesh/material ownership,
Blender 4.3.2, existing source textures and tool hashes. Compression uses the locked
gltfpack 0.22.0 with `-cc -kn -km -kv -vpf -vtf`; float positions retain fine surface offsets.

All hashes below are SHA256 at the final implementation checkpoint. The
[source/test manifest](evidence/ground-growth/after/source-manifest.json) records
every changed implementation file. The ground manifest keeps its exact original
geometry-generation plan hash (`507d2f9dbd182cddb3c96767420476ee4ec9fe5a7ecf2f3e4f9503e6f4bc80b3`)
separate from the final placement hashes; the ground patch array and GLB/Blend
remain identical to that original generation.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| [Ground GLB](../../../../public/models/heron-reach/heron-reach-ground-detail.glb) | 158,884 | `fb17be2f07d66c4d70074bf3d3e62bda559226bf71642578d5799e908b9e6a5a` |
| [Tree GLB](../../../../public/models/heron-reach/heron-reach-ground-trees.glb) | 36,640 | `4189cc10ca98b9d9f95a1a12f8b0b1941d1e12b5a1d5d23fcc0c980bf3df8a87` |
| [Public plan](../../../../public/models/heron-reach/ground-plan.json) | 221,414 | `f3d512ad368107769fbb0a6bea78660a5b0fa0abad0092f31194e728b1a4124b` |
| [Authoring plan](../../../../assets/blender/heron-reach/ground-plan.json) | 434,585 | `8ce58577bf3a746a1530be8219683b629947662cf3538d6eaf86b1d762129520` |
| Ground Blend | 3,894,770 | `87e943a3e460c5afa23a6d80c3e4cc6c99c2fe9e46f70bd6e9c34b3691fa1a11` |
| Tree Blend | 1,901,368 | `452ba251d0c1f9affca22310f277b2909783342d1a0dbce9628a5a0d85cb0b4a` |
| [Plan exporter](../../../../scripts/maps/export-heron-ground-plan.ts) | 861 | `ce46cf45f5609c0f0747f9d2a2b58a9156c146abb14b36893dd440eb85300fe8` |
| [Ground builder](../../../../scripts/maps/art/build_heron_ground_detail.py) | 11,227 | `e146d3069a280d043aef59d1c616402c573f032dbdcc035f87cad5e48fb8e791` |
| [Tree exporter](../../../../scripts/maps/art/export_heron_ground_trees.py) | 14,276 | `bb76009861cf52d2e2a32359795376499ac06bee881fce764cadd2c12598225d` |
| [Foliage builder](../../../../scripts/maps/art/make_heron_foliage.py) | 61,763 | `8d51e6b97b2d16663b916da4792a1b8fdd05b93ab92b0413727a8ae287012642` |

## Completed implementation validation

These commands ran successfully in the isolated `/workspace/Onsite-ground` worktree:

```sh
npm test
npm run typecheck
npm run build
```

All **127 tests passed**: ten legacy plus 117 TypeScript tests, with no failures or
skips. The twenty-seven new tests cover actual decoded support/route geometry, planter
bounds, perimeter trees, budgets, attribute-preserving grass winding, deterministic
baseline matrices and compaction, material sharing and independent load failures.
Typecheck passed. Production build passed with its existing large-chunk warning.
The added plane checks use decoded source bounds and per-mesh hashes: positions,
indices, normals, UVs and bark colours are byte-identical to the initial plane
geometry. The [identity report](evidence/ground-growth/after/plane-identity.json)
records existing gltfpack rounding, including 0.170 mm at one crown extremity.
Rotated actual geometry clears full lamp envelopes, street props, context facades
and neighbouring new crowns. All sixteen centres/yaws and original plane choices
are preserved. Ground patches, outside-planter weeds and original ground/winter
geometry are unchanged. Decoded final planter foliage fits every rim, meets soil
within 1 mm, reaches at least 0.34 m shrub height and stays below 1.25 m overall.
Raw [test](evidence/ground-growth/after/tests.log),
[typecheck](evidence/ground-growth/after/typecheck.log),
[build](evidence/ground-growth/after/build.log) and
[tree export](evidence/ground-growth/after/tree-export.log) logs are archived.
The initial implementation passed 120 tests; the tree and planter corrections add
three test groups; the weed correction adds four actual-asset, scope and kit-loader groups.

The final frozen build is `/tmp/onsite-ground-winding-dist`, served on port 4194.
The superseded planting/shading build remains in `/tmp/onsite-ground-planters-dist` (4193).
The earlier tree-corrected `/tmp/onsite-ground-corrected-dist` is retained from 4192 and
initial `/tmp/onsite-ground-final-dist` remains recoverable from 4191;
4190 was avoided because it is browser-restricted. HTTP smoke checks returned 200
and matching served/frozen hashes for HTML, JS, CSS, public plan and both GLBs.
The main script `index-UnAVxv0V.js` is 5,391,562 bytes, SHA256
`47f60eae723149b82c78933b0071e23f829bf83c9e1234b7236709395e2d8a54`.
HTML SHA256 is `e90d780a0e762de6a3ce01ffe306c9b46d9f8510f719e56033b14fbe33967083`.
The [frozen preview manifest](evidence/ground-growth/after/preview-manifest.json)
records those smoke checks before browser validation.
These checks establish build/asset delivery, not browser appearance or gameplay.

## Final matched runtime views

Seven corrected captures from frozen port 4194 pass delivery and matching checks;
the final visual set is accepted after root inspection of all seven views. Ground,
planting and detail stay attached to their support and broad route readability is
unchanged. Both serial normal-input encounters also pass; their separate evidence follows below.
The six broad baseline images are inherited from `../building-construction/after/`.
The separate close-up baseline in `ground-growth/before/` uses the same frozen
building runtime. The final [report](evidence/ground-growth/after/report.json) and independent
[comparison](evidence/ground-growth/after/comparison.json) verify all seven requested
poses exactly, 1280 × 720 and DPR 1 on Chromium/ANGLE SwiftShader. Settled actual
positions differ by at most 0.509 mm; yaw/pitch match. Errors and failed requests
are empty, and the harness rejects ground fallback warnings. All served JS, GLB,
material-manifest and plan bytes/hashes match the frozen artifacts. The inherited
architecture, runtime material manifest and building-detail GLB remain unchanged.
These are inspection fixtures with active actors, not normal-input gameplay or
frame-time benchmarks.

| View | Building baseline | Corrected ground | Visual review |
| --- | --- | --- | --- |
| Garden Court | [Before](evidence/building-construction/after/garden-court.png) | [After](evidence/ground-growth/after/garden-court.png) | Accepted |
| Washhouse Square | [Before](evidence/building-construction/after/washhouse-square.png) | [After](evidence/ground-growth/after/washhouse-square.png) | Accepted |
| The Corner | [Before](evidence/building-construction/after/the-corner.png) | [After](evidence/ground-growth/after/the-corner.png) | Accepted |
| Gallery edge | [Before](evidence/building-construction/after/gallery-edge.png) | [After](evidence/ground-growth/after/gallery-edge.png) | Accepted |
| Roof skyline | [Before](evidence/building-construction/after/roof-skyline.png) | [After](evidence/ground-growth/after/roof-skyline.png) | Accepted |
| North boundary trees | [Before](evidence/building-construction/after/north-boundary-trees.png) | [After](evidence/ground-growth/after/north-boundary-trees.png) | Accepted |
| Garden ground close-up | [Before](evidence/ground-growth/before/garden-ground-close.png) | [After](evidence/ground-growth/after/garden-ground-close.png) | Accepted |

| Final viewpoint | Calls: baseline → ground | Triangles: baseline → ground |
| --- | --- | --- |
| Garden Court | 374 → 386 | 1,240,953 → 1,279,483 |
| Washhouse Square | 423 → 439 | 1,272,711 → 1,312,873 |
| The Corner | 592 → 625 | 1,359,960 → 1,408,096 |
| Gallery edge | 624 → 660 | 1,346,870 → 1,395,454 |
| Roof skyline | 526 → 550 | 1,328,984 → 1,369,564 |
| North boundary trees | 192 → 201 | 993,476 → 1,039,228 |
| Garden ground close-up | 325 → 341 | 1,146,448 → 1,191,144 |

Frame submissions increase by 9–36 calls and 38,530–48,584 triangles. Active actors
and visibility mean these are not static asset subtotals or evidence of faster frame time.

The north camera tuple is
`[72,0,4,-0.25,-1,0.35]`; the close-up tuple is `[67.5,0,22,-3,-4,-0.23]`.
The close-up baseline has its own [report](evidence/ground-growth/before/report.json).

Three explicitly **superseded** iterations remain available:

- Initial 4191 [north image](evidence/ground-growth/initial/north-boundary-trees.png)
  and [six-view report](evidence/ground-growth/initial/report.json): the added birch
  was nearly white/yellow through sparse, straight branches. Existing attributes
  survived export; the source LOD lost fine branching. Eight new birches were
  replaced with fuller existing plane variants at unchanged centres/yaw. Existing
  plane choices and shared winter materials remain fixed. The correction adds
  5,956 placed triangles and removes 21,100 GLB bytes.
- Tree-corrected 4192 [close-up](evidence/ground-growth/initial-planters/garden-ground-close.png)
  and [seven-view report](evidence/ground-growth/initial-planters/report.json): tree
  hierarchy/bark improved, but K21’s two tiny central shrubs left the bed underplanted.
  Six varied low clumps per bed add 38 placements/2,988 triangles without changing
  ground/tree GLBs. Its interrupted Court attempt supplies no accepted combat result
  or timing sample.
- Planted 4193 [close-up](evidence/ground-growth/initial-weed-shading/garden-ground-close.png)
  and [seven-view report](evidence/ground-growth/initial-weed-shading/report.json):
  enlarged rosettes appeared almost black while neighbouring plants caught light.
  The final index-only correction fixes the proven weed winding defect described
  above. Geometry, textures, placements and lights stay unchanged.

Other superseded screenshots remain local in ignored test-results directories.
Previous review found attached tree rings/soil/plant bases with no obvious floating
or static depth-fighting; one soil pocket retains a hard polygon edge as a polish
limitation. Harsh lamp illumination/bright tree bark, stylised and aliasing foliage,
and sparse interiors remain; this is not an AAA-quality claim. The final close-up is accepted: the rosettes catch light and read as green leaves,
with no new placement/style change. The seven-view set is accepted within the
stated inspection limits; both normal gameplay reports remain separate gates.

## Serial combat and measured software performance

Both production encounters ran serially against the final frozen port 4194 build,
with other browsers, exports and heavy checks stopped. These are new ground
verification reports, separate from the earlier building pass.

Actual browser commands, run from `/workspace/Onsite-ground` with the default
`/usr/bin/chromium` and no `CHROMIUM` override:

```sh
ONSITE_URL=http://127.0.0.1:4194 \
  OUT=/workspace/Onsite/test-results/building-ground/ground-after \
  VIEWS=garden-court,washhouse-square,the-corner,gallery-edge,roof-skyline,north-boundary-trees,garden-ground-close \
  QUERY='&dpr=1' \
  EXTRA_ASSETS=/models/heron-reach/building-detail.glb,/models/heron-reach/heron-reach-ground-detail.glb,/models/heron-reach/heron-reach-ground-trees.glb,/models/heron-reach/ground-plan.json \
  node scripts/maps/capture-art-review.mjs
ONSITE_URL=http://127.0.0.1:4194 \
  OUT=/workspace/Onsite/test-results/building-ground/ground-court \
  node scripts/verify-encounter.mjs
ONSITE_URL=http://127.0.0.1:4194 \
  OUT=/workspace/Onsite/test-results/building-ground/ground-reach \
  node scripts/maps/verify-heron-reach.mjs
```

| Production encounter | Report | Gameplay checks | Mean / median / p95; samples | Calls / triangles |
| --- | --- | --- | --- | --- |
| Heron Court | [Report](evidence/ground-growth/court/report.json), [victory](evidence/ground-growth/court/victory.png) | 10 passed; three opponents down, capture/persist/reset | 480.76 / 478.50 / 652.60 ms; 97 | 97 / 284,429 |
| Heron Reach | [Report](evidence/ground-growth/reach/report.json), [victory](evidence/ground-growth/reach/victory.png) | 9 passed; six opponents down, capture/persist/reset | 641.96 / 630.70 / 798.60 ms; 305 | 510 / 1,309,308 |

Court passes all ten checks: real pointer lock/aim, ADS, automatic fire/recoil/reload,
pause/resume, jump/landing, lobby doorway movement, three opponents defeated,
capture/persistence and reset. It records 15 hits from 27 shots, 300 damage and 96
remaining health. Reach passes its nine checks, with six opponents defeated,
38 hits from 81 shots, approximately 600 damage and 96 health; capture persists
and reset restores the active encounter. Both final reports have empty page/console
error and failed-request arrays; the harness rejects ground fallback warnings.

Both use Chromium/ANGLE SwiftShader at 1100 × 700, DPR 0.5 with bloom disabled.
These software frame-time samples include capture/automation overhead and differing
actor/visibility states. They cannot establish real-GPU performance, smooth play
or an attributable speed-up against the building baseline. The Reach material
allocation estimate remains 328,996,233 mipmapped bytes across 82 architecture
WebP maps; this is not measured driver VRAM and excludes unrelated allocations.
Real-GPU verification remains deferred and unverified.

## Short gameplay recording

The [90-second closing Reach clip](evidence/ground-growth/video/reach-closing.webm)
shows the final automated mouse/keyboard encounter and capture victory at original
wall-clock speed. Its [manifest](evidence/ground-growth/video/manifest.json) records
source/output hashes, the exact interval and processing. Chromium used SwiftShader
at 1100 × 700, DPR 0.5; the recording is 960 × 600, sampled at 10 video frames per
second. That encoding rate is not the game's measured frame rate. There is no audio
or retiming. The victory screen is visible; reset is proved by the browser report,
not the closing video frames. The full original recording remains locally in ignored
`test-results/building-ground/ground-reach/`.
