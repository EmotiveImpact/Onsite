# Public-core stair construction

This original Blender pass replaces the rendered treads and mistaken repeated rails in all eight
public ST-P cores. The 24 storey connections contain 48 flights and 432 treads, including the
mirrored southern cores and every existing B1 connection. Rapier solids, movement, navigation,
doors, route widths and the original Blender 5.2 files remain unchanged.

## Source and export

- Builder: `scripts/maps/art/build_heron_stair_detail.py`.
- Editable textured source: `assets/blender/heron-reach/stair-detail.blend`, Blender 4.3.2.
- Measured placements, source/asset hashes and costs: `assets/blender/heron-reach/stair-detail-manifest.json`.
- Runtime geometry: `public/models/heron-reach/stair-detail.glb`.
- Authoring: map metres, x east / y up / z south, through `heron_art_mesh.Builder`.
  Exported world coordinates are `(mapX - 72, mapY, mapZ - 60)`; apply no loader offset.

Regenerate only this additive file:

```sh
blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_stair_detail.py
```

The builder uses the existing locked npm gltfpack, with `-cc -kn -km -kv -vpf -vtf`.
Float positions retain millimetre construction details. The raw GLB is temporary and removed
after compression. No raw model or source texture PNG is copied into `public/`.
The Blender exporter prints an unavailable Draco-library diagnostic; this export uses the working
meshopt compression path instead. Successful completion requires gltfpack and its output checks.

The geometry is authored specifically for ONSITE. There are no downloaded models or new textures.
The editable Blend packs all 15 of the project's existing material images; reopening the saved
file independently confirmed every file image has a packed reference, so the source travels
without depending on the machine's absolute texture paths. Their provenance remains in the
Heron material manifests and art documentation. Runtime geometry contains no images, textures or
light objects and reuses `HeronReachMaterials`. Original manually authored sources stay closed.

## Construction and physical contract

Each flight is a continuous shaped concrete waist with closed side cheeks, exact risers, sloping
soffit and a short upper bearing under the retained landing slab. Treads are 1.50 m wide, with
0.15 m rises and 0.28 m goings. Nine treads rise to the tenth riser at the landing. A 6 mm nosing
bevel cuts into the physical tread envelope; it never raises the walking surface. Every tread
box is matched against the existing layout before export. The existing anti-slip/yellow-nosing
map uses one 0–1 UV rectangle per tread.

Local first flights rise towards decreasing z; return flights rise towards increasing z. The
whole assembly, including winding, rail pitch, brackets, guards and fittings, reflects across
local z=3 for southern cores. Handrail slopes follow the actual nosing pitch, `0.15 / 0.28`,
with 0.95 m between the nosing pitch and rail centre. Rails return into supported wall or panel
saddles; visible hexagonal fixings and compact brackets explain their attachments.

The existing centre separators are full-height opaque colliders. They now read as opaque painted
steel well/service spines, with folded seams, panel joints and recessed rail channels. This is
deliberate: visually open railings would imply a shot or sightline through solid physics. Their
main sheets are continuous across the complete height and length of the old separators. Landing
guards likewise retain opaque panels, with their handrails on the visible landing face. A more
open glazed stairwell requires a separately designed collision/visibility change.

| Element | Existing local envelope retained | Construction constraint |
| --- | --- | --- |
| First flight | x 0.40–1.90, z 1.70–4.22 | Full 1.50 m walking width retained |
| Return flight | x 4.10–5.60, z 1.70–4.22 | Full 1.50 m walking width retained |
| Left solid spine | x 1.90–1.96, z 1.70–4.22 | Inner rail centre x 1.918, radius 0.018 m |
| Right solid spine | x 4.04–4.10, z 1.70–4.22 | Inner rail centre x 4.082, radius 0.018 m |
| Half landing | x 0.40–5.60, z 0.20–1.70 | Existing 1.50 m depth; no new cross-well barrier |
| Full landing | x 0.20–5.80, z 4.22–5.80 | Existing 1.58 m depth and door threshold retained |
| Outer handrails | x centres 0.34 / 5.66, radius 0.022 m | Entirely in the existing wall/flight gaps |
| Side-wall dado/skirting | At x 0.20 / 5.80 walls | Paint projects ≤7 mm; skirting ≤22 mm |

Side-wall paint bands and skirting follow the flight/landing heights. They stop before the front
door and do not cover the back-wall level numerals. Contact darkening at riser feet, cheeks,
undersides, seams and mounts uses vertex colour; it adds no per-frame effect or texture.

The waist underside at each tread front is `treadTop - 0.30 m`, and at each tread back it is
`treadTop - 0.15 m`. It never drops below the existing stepped collision undersides on the
walking flight. Upper bearing wedges retain at least 2.70 m over the corresponding landing
below. Independent tests ray-check the compressed geometry itself, rather than trusting these
reported dimensions.

Twenty-four new half-landing strip housings sit at local x=4.85, z=0.95 (mirrored with the core),
y=`lowerFloor + 4.15`. Their lens undersides have 2.645 m clearance above the half landing;
two brackets attach each housing to the back wall. They match `heronStairLighting.ts` anchors.
The runtime point source sits 0.35 m below the anchor, clear of the physical lens. The original
32 full-landing fixtures remain in the old architecture. This GLB contains no additional lights.

## Runtime integration

`src/onsite/heronStairArt.ts` loads the additive GLB and removes only the old public-core tread
and rail triangles from the existing compressed architecture. It must run retirement only after
the replacement loads successfully. The original architecture merges core walls, stairs and
other features by material/chunk; hiding complete old objects would delete unrelated geometry.

The old asset's global quantisation needs an 8 mm selection tolerance. Exact material/volume
selection retires **35,072 triangles: 5,184 tread triangles and 29,888 mistaken rail triangles**.
All landing slabs, walls, glazing, painted numbers, service pipes, private ST-H stairs and other
estate geometry remain. In local core coordinates, the retirement masks are:

- Treads: materials `hr_concrete_cast`, `hr_concrete_board`, `hr_stair_tread`; x 0.40–1.90 or
  4.10–5.60; z 1.70–4.22; y base−0.151 through top.
- Old rails: `hr_steel_black`; y base−0.03 through top+2.53; either spine x 1.902–1.958 or
  4.042–4.098 with z 1.68–4.24, or landing-guard x 0.19–4.11 with z 4.162–4.218.
- All triangle vertices must satisfy the relevant volume. South-core z is unmirrored for testing.

Do not retire concrete with a loose landing mask: some original wall/lintel surfaces share
landing planes. The independent tests fingerprint retained landing tops, edges and soffits.

The new model has four culled quadrant groups, `stair/NW`, `stair/NE`, `stair/SW`, `stair/SE`.
Each holds two cores and one mesh for each of seven shared materials, for 28 material batches:

| Material | Runtime treatment |
| --- | --- |
| `hr_stair_concrete` | Clone existing cast-concrete textures, roughness 0.88, metalness 0; sheltered and dry |
| `hr_concrete_board` | Existing board-marked concrete, primarily soffits |
| `hr_stair_tread` | Existing unique anti-slip tread map; dry |
| `hr_door_paint` | Existing paint with muted green/grey vertex tints |
| `hr_steel_black` | Existing dark steel handrails |
| `hr_steel_galv` | Existing galvanised fixtures, brackets and fixings |
| `hr_core_strip` | Existing strip-lens emission |

Preserve `COLOR_0` multiplication when replacing placeholder materials. Do not apply the outdoor
wet-ground shader to `hr_stair_concrete`. The full material and source hashes live in the manifest.

## Validation and costs

The builder asserts all 432 source-box matches, all eight core bounds, inner/outer rail envelopes,
the 1.50 m clear flight widths and minimum fixture/bearing headroom. The shipped asset is decoded
by `tests/heron-stair-construction.test.ts`, which checks actual surfaces near tread centres/edges,
mirror/B1 coverage, standing-body routes, upward headroom, real rail positions/slopes, opaque-spine
coverage, untouched architecture and asset/source hashes. Root owns browser captures and runtime
integration; Blender preview renders are not substituted for runtime evidence.

All six strengthened construction test groups passed against the final compressed asset,
including tread samples 20 mm from either edge and intermediate surface samples on both inner
and outer rails. The reopened Blend passed the packed-image check independently of the export.

The final export contains **29,136 triangles, 28 batches and 395,084 compressed bytes**.
Its SHA256 is `02e9d9af147abaaebd9fdf2e43c15fb2bbe5232d54c60a83a34db76123c98d26`;
the generator and packed Blend hashes are in `stair-detail-manifest.json`. The builder enforces
fewer than 30,000 new triangles and at most 28 batches. Retiring 35,072 old triangles reduces the
rendered triangle total by **5,936**. The additive GLB adds roughly 0.4 MB to download; no new
decoded texture allocations are required. The old download still contains the retired geometry
because the existing architecture source is preserved. The packed editable Blend is 3,573,995 bytes.
