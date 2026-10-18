# Build ONSITE / Heron Reach from the B01 blueprints

Use this brief with `ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf`, `build-spec.json`,
`../map.json` and `assets/blender/maps/heron-reach-32-B01-guides.blend`.
The complete transfer archive preserves those repository-relative paths.

## The assignment

Build **Heron Reach as an additional ONSITE level** in Blender, then integrate it
with the existing WWB / Three.js / Rapier foundation. Keep the small Heron Court
playable as the regression baseline. Inspect current branches and working changes
first; another visual pass may have advanced since this package was produced.
Preserve all useful art, source files, donor notices and original concept references.

The target is a convincing fictional South London estate with layered routes for
a future 32-player / 16v16 mode. Prove the physical layout against bots first. Do
not implement networking as part of the level build. No new controller, second
physics world or second navigation owner should move the same actors.

The visual target remains the original ONSITE London art: stock brick, deep
recessed windows, concrete access galleries, service rooms, court fencing, blue-hour
air, warm door/shop light, damp paving, dirt where water collects, grass seams,
trees, leaves and rubbish. Preserve readability of Black British characters in
black kit. Study `docs/concepts/onsite-london-fps.png`, walkway/corner-shop references,
`MODELLING-NOTES.md` and `TEXTURE-PACK-30.md`; the blueprints are geometry, not a new
art direction.

## Source hierarchy

1. **`../map.json`** sets the 144 × 120 m site, blocks, home and core origins,
   level datums, broad floors, route intent, cover and landscape positions. SHA-256:
   `2f6e2c8f4223435827f5342066e4d4bcb2efb43f198a992639bda9c44b106aaa`.
2. **B01 `build-spec.json`** sets exact wall faces, openings, clear rooms, stairs,
   floor voids and coordinate transforms. Read its `changes` and `surfaceRules`.
3. **B01 drawings** show that contract with dimensions and scales. Use the CSV
   schedules for placements. SVG is editable; PDF prints at 100% on A1.
4. The **B01 guide `.blend`** is generated from the contract and includes real home
   apertures and stair geometry. The older Rev 01 massing is retained as context;
   do not infer final stairs, openings or collision from its proxy boxes.

Resolve any contradiction in the source JSON and regenerate the affected drawings
and guides. Record placement changes explicitly. Never silently shift a doorway
in Blender and leave collision/navigation at its old location.

## Build dimensions and coordinates

- Map `(x, y, z)`: east, up, south; north-west site corner at zero.
- Blender `(X,Y,Z) = (x−72, 60−z, y)`. One unit = one metre.
- Exported GLB / Three.js `(X,Y,Z) = (x−72, y, z−60)`.
- Levels: B1 −3, G 0, L1 +3, L2 +6, R +9 metres. FFL means finished floor top.
- Outer walls 0.20 m, partitions 0.12 m, slabs 0.20 m **below** FFL. Clear room
  ceiling 2.80 m. Door heights 2.20 home / 2.40 public; thresholds ≤0.02 m.
- Home halls 1.50 clear; galleries 3.00 clear; public flights 1.50 clear and
  private flights 1.20 clear. Rail faces and posts must not narrow those widths.
- Both stair types: 20 risers ×0.15 per storey, in two half-flights of **10 risers /
  9 treads**. Going 0.28, run 2.52. The landing takes the tenth rise. Minimum design
  headroom 2.40; perform a real sweep before accepting the geometry.
- Southern modules mirror **every** local z coordinate, including holes and doors.
  H2 stair-local origin is `(6,2)` inside its home. Recalculate normals after
  baking mirrored coordinates; no negative object scales in exports.

## Use the guide model correctly

Open `assets/blender/maps/heron-reach-32-B01-guides.blend` and save an authored copy
before editing. The generator replaces that guide file on rebuild. Ground is visible
by default; toggle `B1_UNDERCROFT`, `L1_GALLERIES`, `L2_UPPER` and `R_ROOFS`. Enable
`90_OPENING_LABELS` to see the 250 portal/window empties and their width/height data.
Stair flight meshes live on their lower level's collection; show both adjacent
levels when inspecting a stair section or looking down through an upper void.

The file has unioned floor guides, home walls, holes, corrected stairs and core
enclosures, simple shop shells, reserved solids and cover proxies. It does **not**
contain final guards, common-concourse exterior facades, undercroft perimeter walls,
finished foliage or lighting. Build those from B200–B700. Glass apertures are empty
in the guide; add closed glass and corresponding non-traversable collision.
Do not mistake an omitted guide wall or rail for permission to create a gameplay route.

Create authored collections following B700. Keep render meshes, simple collision
solids, floor-aware navigation guides and light-intent data separate. Avoid coincident
slabs: union the shared floor surfaces, remove the core footprints, add explicit
landings, and remove the H2 upper openings once. Public core caps are non-playable.

## Implementation sequence

1. **One complete block and both stair types.** Use Rowan, S1/S2 and its H1/H2 units
   as the first repeatable kit. Build real holes, jambs, headroom and all exits.
   Ground, lower gallery and upper rear landing must connect without jumps.
2. **Physical verification before repeated detail.** Integrate simple solids with
   the existing `src/onsite/level.ts` / `navigation.ts` ownership. A home doorway is
   a portal, not another movement system. Test both stair directions and the H2
   private route with the real player and bot capsules. Include the mirrored south
   version in the same verification; a passing north core does not prove the mirror.
3. **Complete the level shell.** Place four blocks and all eight public cores, then
   the continuous +3 gallery, four distinct +6 islands, four undercroft exits and
   two roof terraces. Only Rowan/Cedar roofs are playable. Use B101–B105 for floor
   membership; navigation must retain stacked surfaces at the same x/z.
4. **Landscape and architecture.** Add London facade bays, real window reveals,
   soffits, guard openings, drainage, shop displays and home furnishings without
   obstructing circulation. B600 fixes tree, wetness and fixture positions. Low
   planting and small rubbish are visual; hard cover/trunks use explicit collision.
5. **Materials and lighting.** Start with six shared PBR families. Reuse suitable
   existing individually credited assets and notices. Generated colour images are
   candidates, not automatic complete PBR sets. Rebuild the blue-hour/warm-threshold
   lighting in Three.js; do not rely on Blender lights surviving GLB export.
6. **Profile and refine.** Chunk by block/floor, instance repeated assets, test LODs
   and foliage overdraw. Measure real frame time, load, GPU memory and simulation
   cost with populated actors. Add decoration from those measurements.

## Acceptance evidence to return

- An as-built floor plan derived from actual collision/nav geometry, with every
  deviation from B01 recorded. Include all served levels and mirror transforms.
- Input-driven ascent/descent through every public core and at least one H2 route
  in each orientation; doorway, headroom, railing and collision results.
- Bots that choose and physically traverse the correct stacked floor, plus a
  complete combat/round-reset check on the preserved WWB runtime.
- Spawn/exit sightline checks from galleries and roofs. Test capture height bounds:
  an actor above a ground objective must not count as standing inside it.
- Actual browser stills from a courtyard, gallery, home, public stair and undercroft;
  a short gameplay capture if supported. Distinguish them from concept artwork.
- Rendering hardware, frame-time measurements, draw calls, triangles, texture memory
  and download size. The older cloud SwiftShader result was slow; do not claim
  smooth gameplay or verified 32-player capacity from these plans.

No source in this handoff authorizes wholesale copying of unreviewed donor assets.
WWB remains the runtime foundation; suitable licensed IRONLINE assets can support
the presentation. Modern Claudefare stays unlicensed reference-only. Keep research
clones ignored. Publishing/merging/deploying follows the user's explicit scope.

## Checks already performed on this package

169 offline coordination checks passed, including 0.70 m diameter 2D clearance
through all three home module plans with planned furniture. The generated Blender
guide has 144 checked home doorway/arch centres free of wall solids. All 17 drawing
pages exported and passed viewer/edge checks. Those results cover the design and
guide; full runtime traversal, headroom, bot behaviour and performance remain to prove.
