# Heron Reach world asset audit — 20 October 2026

The largest immediate opportunity is to use the detailed assets we already have
in **Heron Reach**. At release `c583afeb`, twelve individually licensed IRONLINE /
Poly Haven prop models are shipped in `public/models/donors/`, but `View.ts`
calls its `props()` loader only for **Heron Court**. Reach uses the separate
original Blender kits. Its later scanned-detail pass imports manholes and
fluorescent fittings, but not the twelve street/service props.

This audit separates existing runtime use from candidate imports. Source
acquisition below is complete; Blender output and placement are recorded by the
implementation pass, not implied by a downloaded model.

## What to take from the existing references

All five local clones are clean at their recorded revisions in
[the source manifest](../../research/SOURCES.json).

| Source | Actual use before this pass | Best next use |
| --- | --- | --- |
| WWB `4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1` | MIT player, physics, input, scheduling, Arsenal, bots and rules; separately traced utility box and security light in Court | Keep the coherent gameplay foundation. Its traced Poly Haven fittings are useful; its cranes, technology suits and military crates do not fill the residential art gap. |
| IRONLINE `130ac2a5c856401ec36e7d35afcfefe40c5801f4` | Individually credited rifle/arm derivatives, twelve CC0 props in Court, HDRI, two surface sets; later CC0 scanned manholes/strips in Reach | Reuse selected scanned rubbish, delivery and maintenance props in Reach. Extract individual variants and optimise textures before repeated placement. |
| Operation Blackout `51816a061cac321e9fdd3e85f34db1969985dd77` | Scoped MIT atmosphere adaptation | Continue to study presentation, not another player/map architecture. No donor models are needed for this dressing pass. |
| Claude of Duty `d9b237b75c9304ab8d9ef4cfa0c3568c7c11a853` | MIT renderer techniques studied; no copied runtime assets | Contact shadows, visibility and reflection ideas remain useful separate rendering work. It does not provide a ready-made realistic London prop library. |
| Modern Claudefare mirror `51bdc6e94e60c60abfae9c23f39851bb01e088fd` | Read-only architecture/design study | Keep reference-only: no project reuse grant established. |

The existing [donor map](../development/DONOR-MAP.md), [individual model
provenance](../../public/models/donors/provenance.json) and [shipped
notices](../../public/licenses/DONOR-ASSETS.md) remain authoritative. IRONLINE's
package ISC declaration does not clear every bundled asset. Its Fab-derived
animation clips and mixed decal atlas are outside this import.

## Existing scanned props with immediate placement value

These are actual decoded triangle counts and embedded image sizes of the shipped
GLBs, not the much larger original source counts reported by Poly Haven.

| Model | GLB bytes | Triangles | Embedded maps | Best role |
| --- | ---: | ---: | ---: | --- |
| `trashbag` | 259,532 | 1,200 | 3 × 1024² | Varied refuse inside existing bin-store bodies |
| `cardboard_box_01` | 247,864 | 900 | 3 × 1024² | Delivery boxes on existing shelves or within service footprints |
| `old_tyre` | 371,892 | 1,000 | 3 × 1024² | Workshop clutter or a supported flat stack |
| `rusted_wheel_rim_01` | 305,400 | 1,200 | 3 × 1024² | Small workshop detail, not a new obstacle |
| `wooden_crate_02` | 331,724 | 1,500 | 3 × 1024² | Existing storage/workbench footprint |
| `cement_bag` | 134,772 | 844 | 3 × 1024² | Small maintenance grouping |
| `metal_trash_can` | 839,444 | 2,396, two variants | 6 × 1024² | Extract one complete clean or rusty bin, including its leaned lid |
| `exterior_aircon_unit` | 1,330,484 | 2,966, two variants | 12 × 1024² | Extract a single clean/rusty assembly for an existing sealed service surface |

The metal-bin and aircon sources are **variant layouts**, not single wide objects.
The bin's full source bounds are 1.777 × 0.906 × 0.548 m; the AC layout is
1.784 × 0.928 × 0.374 m. Normalising the whole scene by height places both
variants together. Select a complete variant first, then measure its actual
transformed vertices. The tyre and rim are upright in the XY plane, with axle
along Z; laying them flat changes their required support offset.

All eight unchanged source files above would imply roughly **192 MiB** of
RGBA image storage including mipmaps, despite their modest download size.
This is an estimate, not measured GPU allocation. Three 1024² maps imply
approximately 16 MiB; three 512² maps imply 4 MiB. Derive 512 px maps for small
background props, retain sharp silhouettes, share each material/image between
instances, and do not load unused variants. Compare actual draw calls and frame
time after placement. Avoid treating image compression as equivalent to GPU
texture compression.

## Further licensed local candidates

IRONLINE's README records these as simplified/WebP derivatives of Poly Haven
CC0 models. Original author metadata was rechecked through
`https://api.polyhaven.com/info/<id>` for this audit.

| Candidate | Author | Local bytes / triangles | SHA256 |
| --- | --- | --- | --- |
| `utility_box_01` | James Ray Cock | 244,540 / 1,500 | `b61859ebc3b70219217be5d7930642d81e4463e56fe06f1869905aede9907943` |
| `utility_box_02` | James Ray Cock | 266,844 / 1,799 | `74cb0d63c218982286048e31d8fa9011eb965d84e3a6e31e1dc854e97680139a` |
| `modular_industrial_pipes_01` | Jorge Camacho | 834,920 / 4,650 | `1a3afb1fac9b957ae42b4f8da03a5c85002a6b393c1e11b6caac95c6b224b564` |
| `WetFloorSign_01` | Fran Calvente | 111,280 / 228 | `77d9d43f71b8f8285dc91a9474b4dc8ccc2119fdbce49d02d64ea90854943662` |
| `portable_generator` | James Ray Cock | 654,252 / 4,571 | `c6f6cad2bbf885e6fa60146fc6671d37294506853f14b4ae7631faa1ca5a5c92` |

Each lives at `research/reference-clones/ironline/public/assets/models/props/<id>/<id>.glb`.
They need a separate derivative/provenance record if imported. Utility boxes and
small pipe sections belong against real supporting walls. A free-standing
generator or chair needs an existing blocked footprint or separately designed
collision; it must not become a convincing solid object the player walks through.

## Two new original CC0 sources acquired

The source files are outside `public/` and are not browser downloads. Their exact
original bytes, author metadata, final URLs and hashes are pinned in
[source-manifest.json](../../assets/reference/world-dressing/source-manifest.json).
The [Poly Haven licence snapshot](../../assets/reference/world-dressing/polyhaven-license.html)
contains the explicit statement that its assets are licensed as CC0. Individual
source pages are linked below; CC0 allows commercial adaptation.

| Source | Author | Actual glTF triangles | Downloaded 1k source |
| --- | --- | ---: | ---: |
| [Fern 02](https://polyhaven.com/a/fern_02) | Rob Tuytel: scanning; Rico Cilliers: modelling | 6,232 across four separate variants | 1,260,950 bytes, including separate 114,589-byte opacity mask |
| [Planter Pot Clay](https://polyhaven.com/a/planter_pot_clay) | Amal Kumar | 3,080 | 1,797,158 bytes |

Fern 02 provides recognisable fronds for damp, sheltered planting. The source is
four arranged variants; extract and normalise each root before placing. Its glTF
declares a MASK material but references an **RGB JPEG with no alpha**. The original
separate `Alpha/1k/png` map was therefore acquired too. It is a 16-bit PNG:
explicitly scale 0–65535 to 0–255 when deriving 8-bit alpha, rather than clipping
through a direct Pillow `convert('L')`. Combine it with the original colour into
a separate RGBA derivative; preserve the source files.

The clay pot is approximately 0.266 × 0.263 × 0.222 m in the catalogue's original
Blender coordinate convention. Use actual decoded geometry and transformed metre
bounds during placement. Neither catalogue dimensions nor a source photo prove
ground support or clearance in the level.

Reproduce or verify the pinned source acquisition:

```sh
python3 scripts/import-world-reference.py
```

The [importer](../../scripts/import-world-reference.py) checks HTTPS hosts and final
redirect destinations, declared file sizes, exact glTF buffer/image URI coverage,
relative paths, buffer byte lengths and image validity. It records source SHA256
values and refuses to overwrite changed originals. Repeated execution verifies
the pinned files; it does not silently refresh mutable API metadata. No donor
script or new dependency was executed.

## Strong next downloads, not imported here

- [Plastic Monobloc Chair 01](https://polyhaven.com/a/plastic_monobloc_chair_01),
  Kuutti Siitonen, CC0: 3,356 actual triangles, 1,952,867 bytes for its complete
  1k glTF package; 2k is 6,665,320 bytes. Its weathered white plastic is a useful
  domestic silhouette for supported private balconies or existing furniture
  footprints. It was thumbnail-reviewed but not downloaded as a model.
- [Potted Plant 04](https://polyhaven.com/a/potted_plant_04), James Ray Cock, CC0:
  a small succulent, 8,929 actual exported triangles across its source nodes,
  2,122,625 bytes at 1k. The catalogue's 6,097 polygon count is not the glTF
  triangle count. Suitable for a few close windowsills; not large planted beds.
- [Potted Plant 02](https://polyhaven.com/a/potted_plant_02), Rico Cilliers, CC0:
  69,806 actual triangles and 2,634,698 bytes at 1k. Attractive dense leaves, but
  too costly for mass placement without a deliberately reviewed reduction.
- [Shrub 03](https://polyhaven.com/a/shrub_03), Rico Cilliers, CC0:
  four thin budding-herb variants, 8,287 actual triangles total, 1,628,793 bytes
  at 1k. Visually less useful for filling a bed than the chosen fern.

The current IRONLINE prop inventory has no comparable foliage or domestic-chair
model. Its other props are chiefly barrels, containers, lights and industrial
equipment. More generic military clutter would weaken the residential setting.

## Material and placement priorities

Heron Reach already has a 22-set tiling PBR library plus original decals, window
atlases and ground detail. Its [texture record](../maps/heron-reach-32/art/TEXTURES.md)
states which generated source images were reworked. The ambientCG Ground110 and
Leaking003 sets in `public/materials/detail/` have separate
[CC0 provenance](../../public/materials/detail/provenance.json); they are not a
reason to copy IRONLINE's entire mixed decal atlas.

Place meaningful groups at existing activity areas: refuse inside bin stores,
deliveries on shop/storage shelves, maintenance objects beneath workbenches, plants
inside existing beds, and service equipment on sealed surfaces. Keep doors,
stairs, objectives and sightlines clear. Measure against actual render supports
as well as collider envelopes, avoiding floating props and piles buried inside
opaque furniture. The original physics and navigation remain authoritative.

After those placements, the largest remaining realism gains are balanced local
lighting, believable contact, varied furniture, soil/grass transitions and less
repetitive wear. They need a consistent material/visibility workflow, not another
engine or an unbounded texture download.
