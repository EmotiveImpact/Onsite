# Heron Reach ground and planting

Original, deterministic ONSITE presentation geometry around the existing map. No collision,
navigation, gameplay cover dimensions, physical shadows or water rendering are changed.

The current map already has 20 winter trees, 80 large leaf-litter patches, 672 grass cells,
shrubs/weeds in ten planting rectangles, kerbs, puddles, three Corner drains and two manholes.
This pass adds small irregular soil/moss deposits and sparse loose leaves at those features;
it does not introduce another lawn, puddle layer or trunk on a playable route.

## Content and measured cost

- 20 ragged soil rings at the exact existing trunk centres.
- 131 irregular bare-soil pockets and 89 short moss/grass-edge deposits.
- 45 small loose-leaf drifts, avoiding existing leaf-litter patch centres.
- 53 low ground weed clumps, plus six varied clumps in each of the eight existing raised
  concrete planters: 10 leafy shrubs, 22 broad low rosettes and 16 upright weeds.
  All planter roots meet the existing soil top at 0.85m; transformed foliage remains inside
  the 120mm rim and below 1.25m total height. Existing planter collision remains authoritative.
- 16 extra winter London-plane LOD1 trees on the unreachable north/south pavement at map z=-1.9/121.9,
  between street lamps. Trunks clear existing dressing, canopies clear context facades.

Ground geometry: **5,240 triangles, 57 spatial/material batches on 24m tiles, 158,884-byte GLB**.
Extra instanced plants: **22,256 triangles**. Combined ground/plants: **27,496 triangles**.
The final planter revision adds 38 low clumps and varies/enlarges its ten shrub roles within
the same rim/height limits: +2,988 triangles. The original ground patches and 53 ground weeds
remain fixed; the additive ground/tree GLBs and Blends are unchanged from the plane correction.
Trees: **23,408 instanced triangles**, from a 2,926-triangle, **36,640-byte** two-asset LOD kit.
The initial eight perimeter birches were replaced at the same centres/yaw after their pale,
sparse spokes failed runtime review. Existing plane choices and the original winter kit stay fixed.
The correction adds 5,956 placed tree triangles but removes 21,100 download bytes and
reduces the extra tree kit from eight to four material primitives. The ground GLB/Blend,
patches, original winter source and original winter runtime GLB remain byte-identical
to the first pass. Source hashes are recorded in the manifest and work log.
No GLB embeds images or textures. These are geometric budgets, not measured GPU timing.

## Source and regeneration

All new mesh/placement code is original ONSITE work. Textures and plant meshes reuse the
existing project material/foliage kit. No donor code, external asset or new texture pixels.
`ground-detail.blend` retains editable original low-relief meshes and existing packed PBR maps;
`ground-trees.blend` appends the existing two London-plane LOD1 collections from `winter-trees.blend`.
Manifests record source hashes, Blender version, named roots, materials, geometry and costs.
The ground manifest retains the original exact geometry-generation plan hash separately
from current placement-plan hashes; its patch array and GLB/Blend are unchanged by the
later tree selection and planter-density revisions.
Exports use the existing locked gltfpack 0.22.0 with `-cc -kn -km -kv -vpf -vtf`;
float positions preserve millimetre surface offsets. Tool package/script/WASM hashes are recorded.

Run with Blender 4.3.2 and one thread:

```sh
npx tsx scripts/maps/export-heron-ground-plan.ts
blender -b -t 1 --python-exit-code 1 --python scripts/maps/art/build_heron_ground_detail.py
blender -b -t 1 --python-exit-code 1 --python scripts/maps/art/export_heron_ground_trees.py
```

Both Blender scripts support isolated output roots; see their module documentation. Exported
GLBs contain geometry and named material placeholders only. Existing files are never replaced.

## Runtime integration

The TS exporter calls `buildHeronGroundPlan({solids,surfaceIds,layout,grassCells,existingPlacements:dressing.items})`
against the actual map and writes both an authoring copy and the exact minified public plan.
At runtime `loadHeronGroundPlan()` fetches `/models/heron-reach/ground-plan.json` (221,414 bytes)
alongside art. This avoids repeating roughly 0.1–0.25 seconds of placement/support work at
startup. `heronGroundRuntime.ts` imports only planner types, so the planner/foliage manifest
never enter the browser bundle. Failed HTTP, JSON or schema validation warns and returns null.

`View` merges `plan.plants` and `plan.perimeterTrees` into render-only kit placements after
the original dressing plan has already created physics. `KitPlacement.scale` composes as
`(scale*(sx??1), scale, scale)` so existing mirrored signs still work.

Add optional `ground-trees` to the kit loader. Its roots are `TREE_PLANE_A_LOD1`,
`TREE_PLANE_B_LOD1`. Resolve the exact materials
`hr_bark_plane`, `hr_leaf_plane` from the already-loaded winter
kit before creating instances. There are no suffixes or new foliage textures.

After kits load, `loadHeronGroundArt(gltf,materials,kits)` returns explicit `{group,loaded}`.
It reuses `hr_soil` and
`hr_grass_ground`; moss tint is vertex colour, and loose leaves reuse the existing kit's
`hr_leaf_litter` material. Missing optional geometry retains the original scene. Missing leaf
material hides only the additive loose leaves. Failed or empty/malformed ground art returns
`loaded:false`, so `View` keeps the original unmasked grass. Public plan failure also keeps
the original kit placement list and avoids requesting the optional tree kit.

`createGroundGrassDensity(plan)` in `heronGroundRuntime.ts` gives the existing `GrassField` a bounded 8m spatial lookup.
It returns 0.13 inside soil pockets and 0.04 inside tree rings, otherwise 1. Keep the original
candidate random sequence stable: it generates scale/yaw for every original candidate, then
compacts accepted instances using a separate coordinate hash. Retained instance matrices
and unaffected later tiles exactly match the baseline. No second grass placement owner.

## Grass winding diagnosis

The original exported `GRASS_CLUMP_A–D` geometry has 588 geometrically downward-wound faces,
while its authored normal Y is +0.874 to +0.923. All faces are back-facing from above; 532/588
are back-facing from a standing eye one metre away. Standard double-sided shading flips
those upward normals downward, explaining the dark grass. UVs and source colour maps are valid.
Only 427/588 faces have a negative dot against the deliberately tilted authored normals;
the reliable intended blade-facing test is geometric face Y in the asset-root frame.

`correctGrassWinding(source,local)` clones only the clump geometry and reverses downward
faces, retaining authored normals/UVs/colours. GrassField calls this for the four known grass
clumps; kit loading also scopes it to WEED_TUFT_B’s separate `hr_grass_blade` primitive. Corrected exports stay unchanged on later passes. The source-builder patch reverses
the corresponding blade face/UV order without rebuilding or replacing the current kit.
Thin 6–12mm blades may still alias at DPR1: anisotropy and coverage are separate sampling
decisions; no new lights, unlit replacement or blanket leaf normal hack is required.

The enlarged planter rosettes exposed the same source-winding defect in the weed kit.
The shipped compressed GLB has 66 downward rosette triangles in `WEED_TUFT_A`,
30 in `WEED_TUFT_C` and 30 downward blade triangles in `WEED_TUFT_B` (126 total).
A/C strip leaves have transformed authored normal Y 0.9931–0.9947; the twelve B/C
upright cards range from 0.9039 to 0.9299. `correctFoliageWinding` clones only the
known A/C `hr_weed` primitives and flips downward faces only when all three authored
corner normals have up > 0.98. B’s separate `hr_grass_blade` uses the blade correction.
All twelve upright cards retain their indices, including four whose geometric face
Y is negative. Other assets/materials retain their original geometry object. Every
position, authored normal, UV and colour remains byte-identical; no tint or unlit
shader is introduced. The future `strip_leaf` builder reverses corner/UV order;
`cross_cards` and the original foliage GLB/Blend remain unchanged. The runtime
correction also applies to existing instances of these same three weed assets.

## Acceptance and review

The pure planner uses current G slabs, exact grass finish heights, full sampled patch outlines,
core margins, both doorway sides, objective rings, spawn yards, Garden Court cross paths and
four Cage gate approaches. It rejects upper floors, stairs and unsupported holes. Raised
planters use their explicit Blender soil finish and transformed measured foliage bounds.
Each bed has six staggered, deterministically jittered clumps with asset/scale/yaw variation;
broad rosettes fill low space around the leafy shrubs instead of repeating a row of shrubs.
Placement seeds belong to each feature, so adding another feature does not reshuffle earlier ones.

Tests cover deterministic/non-mutating planning, all 20 tree centres, flat support and holes,
clear routes, all eight planter interiors, perimeter tree separation, exported vertex heights,
face winding, no embedded images and the 30k non-tree geometry budget. Grass/weed tests decode the
actual compressed kit and verify correction, unchanged upright card indices, exact
attribute preservation, asset/material scope and idempotence.
Runtime tests additionally check a recorded baseline matrix hash, selective compaction,
missing/rejected masks, zero-instance fields, exact winter material ownership, uniform scale,
and independent public-plan/ground-asset fallbacks. Normal browser verification treats all
ground fallback warnings as failures; optional fallback is not silently accepted as a full pass.

Corrected implementation checks in the isolated ground worktree on 20 October 2026:
`npm test` passes all 127 tests (10 legacy and 117 TypeScript tests), `npm run typecheck`
and `npm run build` pass. The correction groups validate actual decoded plane attributes, rotated canopy/prop
clearances the final six-clump beds and exact weed-strip/blade correction while preserving upright cards. Actual transformed foliage vertices meet
soil within 1 mm, clear every rim and stay below 1.25 m; the non-planter placements,
patches and trees retain their pre-planter fingerprints. Per-mesh fingerprints prove positions,
indices, normals, UVs and bark colours match the original exported planes exactly.
The source-bound fixture uses the original decoded vertices, including existing gltfpack
floating-point quantization (up to 0.170 mm at the measured crown), not raw Blender bounds. These checks do not establish browser appearance or real-GPU performance.

Visual review is still required after integration; no browser was run during staging. Compare
the same `garden-court`, `the-cage`, `the-corner` and south boundary/gallery views. Useful close
viewpoints in map coordinates: (72,1.65,38) looking toward (72,1.3,20); (48,1.65,44) toward
(55,1,59); (111,1.65,44) toward the existing Corner drain at (119.72,0,47.61). Review natural
olive/brown growth, visible bare pockets, low planter tops, clear gates and no floating edges.
