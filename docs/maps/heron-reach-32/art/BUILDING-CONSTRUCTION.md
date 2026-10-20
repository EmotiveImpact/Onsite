# Building construction and private stairs

This additive Blender pass makes existing building joints and eight private H2 staircases read
as assembled construction. The public stair kit, original Blender 5.2 files, Rapier solids,
navigation, opening dimensions and existing gameplay systems remain unchanged.

## Files and reproduction

- `scripts/maps/art/build_heron_building_detail.py` is the complete original generator. The private
  stair and narrow-door assembly functions are included directly; no temporary helper is required.
- `assets/blender/heron-reach/building-detail.blend` is the editable Blender 4.3.2 source.
- `assets/blender/heron-reach/building-detail-manifest.json` records placements, exact source/asset
  hashes, retirement masks, material interfaces and measured export costs.
- `public/models/heron-reach/building-detail.glb` is the sole shipped model for this pass.

```sh
blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_building_detail.py
```

The script opens an empty new Blender scene, never an original estate source. It uses
`heron_art_mesh.Builder` in map metres: x east, y up, z south. The GLB is already in world
coordinates `(mapX - 72, mapY, mapZ - 60)` and needs no offset. Four spatial groups,
`building/NW`, `building/NE`, `building/SW`, `building/SE`, each hold thirteen material batches.

The saved Blend packs all its file images, with an assertion that each packed reference exists.
Its textured editing materials remain intact on disk. The export session then replaces their
graphs with named placeholders, leaving zero embedded images/textures in the GLB. Runtime reuses
the existing Heron material library, including vertex-colour contact shading. gltfpack uses the
locked npm version with `-cc -kn -km -kv -vpf -vtf`; float positions preserve small construction
details. Raw GLB output is temporary and does not ship. The exporter may print the unavailable
Draco-library diagnostic; compression here uses the working meshopt path and checked output.

All geometry is original ONSITE procedural work. No model, image, font or new dependency was
downloaded. Existing PBR texture provenance remains with the project's material manifests.
The assembly adds no light objects or new runtime texture allocations.

## Private H2 stair correction

The old private stairs had individually boxed treads, a missing rendered divider despite its
solid collider, and full-home finish sheets crossing the actual stair void. Those sheets made
the half landing appear to have approximately 1.29 m headroom and visually blocked the ascent.

All eight H2-L homes now have two coherent flights: **16 flights and 144 exact treads**. The
profile uses the existing 1.20 m width, 0.15 m rise, 0.28 m going and 2.52 m flight run. Continuous
concrete waists and soffits lie within the original tread-box union; no bearing extension lowers
the existing landing headroom. A 6 mm bevel cuts into each nosing without raising the walking
surface. Existing anti-slip tread material uses one 0–1 UV rectangle per step.

The existing private divider occupies local x=1.38–1.53, z=1.40–3.92, y=3.00–7.20. Its new opaque
painted backing communicates the existing solid collision. Supported rails with sealed ends fit
its recessed side channels and the outer wall gaps. First flights rise towards decreasing local z, return flights
towards increasing z; the complete assembly reflects for southern homes. Rail pitch follows
`0.15 / 0.28`, with the centreline 0.95 m above the nosing pitch. The upper guard is opaque within
its existing volume; its rail connects into the divider and the return flight.

The local stair frame is x=`home.x + 6`. For north homes, map z=`home.z + 2 + localZ`; for south
homes, map z=`home.z + 6 - localZ`. The latter is intentionally distinct from mirroring an entire
8 m home around the wrong origin. All private stairs rise from y=3 to y=6.

Only the H2-L ceiling at y=5.795 and H2-U laminate floor at y=6.004 are replaced. The original
sheet rectangle is x=`home.x + 0.2` to `home.x + 8.8`, z=`home.z + 0.2` to `home.z + 7.8`.
New rectangles surround the authoritative, correctly mirrored ST-H void. The lower laminate
floor, upper ceiling, physical slabs, half landing and all other room finishes remain.

Retirement is separate from the public stair filter:

| Old private geometry | Triangles per home | Eight-home total |
| --- | ---: | ---: |
| Cast tread faces | 180 | 1,440 |
| Board-marked tread undersides | 36 | 288 |
| Rubber nosings | 96 | 768 |
| Old open upper guard | 136 | 1,088 |
| Two spanning finish sheets | 4 | 32 |
| **Total** | **452** | **3,616** |

Private tread masks are local x 0.18–1.38 or 1.53–2.73, z 1.40–3.92,
y base−0.151 through top+0.006, with the cast/board/rubber material whitelist. The old guard
mask is local x 0.11–1.39, z 3.86–3.92, y 6.00–7.20, material `hr_steel_black`.
All vertices must satisfy a mask; the existing compressed architecture needs 8 mm tolerance.
Sheet retirement additionally requires exact owning rectangle, material and plane height.
The manifest records these masks and original counts independently of the public kit.

## Sixteen narrow inner doors

The affected inner openings are physically 0.80 m wide, while the old 60 mm jambs on both sides
left only 0.68 m visible clearance. The player's capsule diameter is 0.76 m. The old held-open
leaf also protruded into the approach beside the opening.

New timber casings sit over the existing wall, outside both opening edges, projecting 12 mm
from each wall face. The plaster leaf keeps its original 0.68 m width, 45 mm thickness and
height, and folds fully open against the longer P2 wall on the opposite jamb. This clears both
its own opening and the adjacent external entrance approach. Two small supported hinge
assemblies connect it to the casing; the whole leaf has existing solid wall behind it. The
opening and fully open door state stay intact, with no new geometry in the 0.80 m corridor.

The separate narrow-joinery retirement removes exactly **384 jamb + 192 leaf = 576 triangles**.
It preserves the original heads, thresholds and all 128 coincident head/threshold end-cap
triangles. Jamb selection uses both exact local volumes and face dimensions; a simple loose
box mask would incorrectly delete those caps. Leaf selection uses its exact old box and
`hr_plaster` material. Every predicate, old/new bound, original/replacement hinge side and
supporting wall is recorded per doorway in `narrowDoorJoinery`.

The combined geometry check also identified sixteen adjacent P1 D02 hallway leaves, each in a
0.90 m opening. Their original perpendicular pose crossed the bathroom approach even though
the standing capsule was physically clear at all five tested approach depths. These precise
leaves now sit fully open, parallel to their existing P1 wall. They retain the original 0.78 m
leaf width, 45 mm thickness and height. Two modelled hinge bridges support each leaf; 720 mm
of its width has existing wall behind it, and the remaining 60 mm meets the existing jamb.
The P1 opening, frame, threshold and collision stay intact.

This second correction has its own `adjacentHallwayLeaves` records and
`adjacentHallwayLeafTotals`: **192 old plaster triangles**, separate from the unchanged
576-triangle narrow-joinery retirement. Each selector requires the exact H2 owner, P1 D02
position, 0.90 m width, axis, normal, floor and old leaf bounds. It does not retire other
0.90 m doors.

Eight upper H2 D01 exterior leaves also crossed a physically clear bathroom approach in their
old inward pose. These precise upper leaves now fold fully open against the exterior wall,
retaining their original hinge side, 0.98 m width, 45 mm thickness and height. Four painted
pieces frame each glass insert, and two attached hinges connect the leaf to the retained jamb.
The unchanged wall backs 920 mm of each leaf; the jamb backs the remaining 60 mm. Their glass
projects at most 67 mm past the home's outer wall face, clear of every tested standing approach.
The lower exterior entries, all frames and thresholds remain intact.

Their separate `upperEntryLeaves` retirement removes **96 painted + 96 glass = 192 triangles**.
It requires the exact H2 owner, upper D01 position, level, material and old leaf/glass bounds.
Retiring both old components avoids a glass insert remaining in the former pose. This adds
one existing shared glass material per quadrant, bringing the asset to 52 spatial/material batches.

## Attached building construction

The existing facade builder already supplies window openings, frames, flat sills/lintels,
home downpipes and column bodies. This pass keeps them and adds the missing joints and supports.
It does not imply new rooms, routes or shoot-through glazing.

| New assembly | Count | Placement and clearance |
| --- | ---: | --- |
| Public entrance surrounds | 32 | Collars lie outside the full 1.50 m openings; chamfered head begins 5 mm above the existing 2.40 m opening and stops below the block-name sign |
| Core drainage assemblies | 8 | On the left 160 mm corner pier, away from the centred door, right-side CCTV and existing sill ends; brackets, coupling collars and shallow scupper hopper |
| Core sill drip profiles | 64 | Attached to the retained sill lower edge; total projection increases from 60 to 76 mm |
| Gallery fascia/coping joints | 160 edges | Formed drip lip and six-metre panel joints on existing fascia/parapets; lowest new edge is 2.446 m above ground at L1 |
| Column head bearings | 88 | Above 2.745 m; 12 mm maximum enlargement around the existing column body |
| Pendant cords and ceiling roses | 24 | Attach existing shades at their original absolute coordinates; no shade, emission or light-anchor movement |

The core pipes are at local x=0.16, 2.84 m from the door centre. Pipe/collar projection is at most
83 mm, while the roof-height hopper projects 120 mm. They remain small attached fittings rather
than new ground furniture. No pipe is added to a home facade that already received downpipes.

Gallery seams have a 9 mm stand-off to clear the retained architecture's older 8 mm position
error. They stay on the outer faces, away from the walking side; coping joints remain within
the existing coping width. The shaped lower lip projects at most 26 mm beyond the existing
fascia. Column bearings and pendant attachments exceed the 2.40 m standing-clearance envelope.

The old pendant placements were not mirrored by the original generator. New cords therefore
use exactly `(home.x + 6.5, home.y + 2.60..2.789, home.z + 6)` for both north and south homes.
This attaches the actual existing shade rather than placing a correctly mirrored cord elsewhere.

## Material and loading contract

`src/onsite/heronBuildingArt.ts` owns runtime loading and retirement. Retire legacy triangles
only after the replacement model loads successfully. Keep its private-stair and narrow-joinery
filters independent so their exact counts remain reviewable. Do not hide complete old chunk
objects, which contain unrelated walls, landings and furniture.

Shared material names are `hr_stair_concrete`, `hr_concrete_board`, `hr_stair_tread`,
`hr_steel_black`, `hr_steel_galv`, `hr_door_paint`, `hr_ceiling`, `hr_floor_laminate`, `hr_timber`,
`hr_plaster`, `hr_concrete_cast`, `hr_rubber` and `hr_glass`. Only `hr_stair_concrete` is an alias: use the
same dry cast-concrete clone as public stairs, roughness 0.88, metalness zero and no exterior
wet-ground shader. Other names reuse the existing instances. Preserve `COLOR_0` multiplication.

The manifest contains `privateStairs`, `privateSheetRetirement`, `narrowDoorJoinery`,
`adjacentHallwayLeaves`, `upperEntryLeaves`, public `protectedOpenings` and measured `features` with existing
supports and allowed projections.
The builder asserts every private tread's exact collision-box match, private stair envelope,
authoritative void match, casing wall support and packed image reference. Independent tests
decode the shipped compressed geometry and the retained architecture for clearance and
retirement checks. Root owns runtime captures and physical traversal evidence.

The completed export is **35,344 triangles, 52 batches, 484,816 bytes**, with no new
textures/lights. Its SHA256 is `437d8c49fc2cb5cd00232d655d663f42718920181338b8e925b9d68dc829f8fa`.
The packed editable Blend is 5,747,705 bytes. Total retired geometry is **4,576 triangles**,
giving **30,768 net additional rendered triangles**. The original architecture download stays
intact for recovery. Exact current source and asset hashes are authoritative in the manifest.

The final GLB passed all seven groups in `tests/heron-building-construction.test.ts`: decoded
budgets/provenance, all 144 physical tread heights and near-edge widths, combined private
stair headroom and void cuts, opaque dividers and directed rails, every physically clear
standing doorway approach, exact scoped legacy retirement/preservation, and loader failure
safety. The doorway checks use the actual 0.76 m standing capsule against unchanged Rapier
solids before testing combined render geometry; all 80 narrow-door samples are physically
clear. Original public stair retirement, partitions, windows, landings, frames and retained
head/threshold caps remain separately verified. Root owns the final browser captures and
continuous physical traversal checks.
