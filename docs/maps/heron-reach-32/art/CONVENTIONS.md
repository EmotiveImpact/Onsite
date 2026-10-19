# Heron Reach art kit conventions

Shared rules for the Heron Reach Blender art build: materials, foliage, props and the
architecture assembly. The level's physical layout is owned by `src/onsite/heronReach.ts`.
Art never changes collision or navigation. Anything big enough to block a player is
reported with its footprint so the generator can give it an explicit box collider.

## Tools

- Blender 5.2.2 runs as a Python module: `python3 script.py` with `import bpy`.
  There is no GUI. Cycles on the CPU works for preview renders. Do not rely on EEVEE.
- Python has numpy and Pillow. Do not install packages or download assets. Poly Haven,
  ambientCG and similar hosts are blocked here. Every new texture and mesh is
  original work, made procedurally or by hand-written code. Record how it was made.
- The machine has 4 CPU cores. Keep preview renders small (for example 960 × 640,
  64 to 128 samples, with denoising).

## Scale, axes and transforms

- One Blender unit is one metre. Blender is Z-up. glTF export converts to Y-up.
- Each asset's object origin sits at the centre of its footprint, on the ground (Z = 0),
  and faces −Y (Blender front) unless stated otherwise.
- Apply all transforms before saving. No negative scales. Recalculate normals outward.

## UVs and texel density

- Tiling surfaces use real-world UVs: **1 UV unit = 1 metre**. Materials scale texture
  lookups by `1 / coverage` with a Mapping node, so a 2 m brick texture uses scale 0.5.
- Unique props may use their own 0–1 UV layout and a dedicated texture.

## Materials

Principled BSDF only. Image textures: colour in sRGB, normal and data maps in Non-Color.
Normal maps use the OpenGL convention (+Y). Packed data maps follow glTF ORM:
R ambient occlusion, G roughness, B metalness. Alpha-cut materials use Alpha Clip
semantics (alpha threshold 0.5) so they export as glTF `MASK`.

Shared tiling materials, built by the texture kit (names are exact):

| name | surface | coverage |
| --- | --- | --- |
| `hr_brick_stock` | London stock brick | 2 m |
| `hr_brick_red` | red estate brick | 2 m |
| `hr_brick_painted` | painted brick | 2 m |
| `hr_concrete_cast` | smooth cast concrete | 2 m |
| `hr_concrete_board` | board-marked concrete | 2 m |
| `hr_concrete_rough` | rough, stained concrete | 2 m |
| `hr_render` | painted render | 2 m |
| `hr_asphalt` | asphalt road and lanes | 2 m |
| `hr_court` | painted court asphalt | 2 m |
| `hr_paving` | concrete paving slabs | 2 m |
| `hr_pavers_red` | red block pavers | 2 m |
| `hr_roof_felt` | roof felt | 2 m |
| `hr_steel_black` | black painted steel | 1 m |
| `hr_steel_galv` | galvanised steel | 1 m |
| `hr_steel_aged` | aged and rusted steel | 1 m |
| `hr_shutter` | roller shutter | 2 m |
| `hr_rubber` | rubber floor | 1 m |
| `hr_timber` | bench timber | 2 m |
| `hr_soil` | dark soil | 2 m |
| `hr_grass_ground` | short grass ground | 2 m |
| `hr_gravel` | gravel | 2 m |
| `hr_plaster` | interior plaster | 2 m |

Plain shared materials (no image unless stated): `hr_glass` (dark reflective glazing),
`hr_glass_lit` (warm emissive, 2700 K), `hr_lamp_emit` (lamp lenses, strong warm emissive),
`hr_upvc_white` (window frames), `hr_paint_yellow` (bollard bands and line paint),
`hr_plastic_black`, `hr_plastic_green`, `hr_door_paint` (front-door paint, colour varies
by vertex colour), `hr_signage` (sign faces).

Foliage materials are owned by the foliage kit: `hr_bark_plane`, `hr_bark_birch`,
`hr_leaf_plane`, `hr_leaf_birch`, `hr_grass_blade`, `hr_shrub_leaf`, `hr_hedge_leaf`,
`hr_leaf_litter`, `hr_weed`.

A prop may use the shared materials plus its own `hr_prop_<asset>` materials for unique detail.

## Files

- Textures ship in `public/materials/heron/` as WebP: `<name>-color.webp`, `<name>-normal.webp`,
  `<name>-orm.webp` (1024² unless noted). Foliage textures go in `public/materials/heron/foliage/`,
  prop textures in `public/materials/heron/props/`.
- Blender sources live in `assets/blender/heron-reach/`. Pack images into each `.blend`.
- Every kit writes a `manifest.json` beside its `.blend`, listing each asset, its collection,
  its triangle count, its footprint in metres and whether it needs collision.
- Preview renders go to `/mnt/project-files/heron-reach/progress/kit/`. This is a shared,
  network-mounted folder: write new files only, with the kit's prefix (`tex-`, `foliage-`,
  `props-`), and never delete or overwrite another kit's files.

## Look

Study `docs/concepts/onsite-london-fps.png`, `docs/concepts/screens/*.png` and
`docs/concepts/asset-pack-50/*.png`. The target is a weathered South London council estate at
blue hour: London stock brick, board-marked concrete, black steel railings, damp paving,
moss and grime where water collects, warm 2700 K door and shop light against cool blue air.
Everything is worn, not new. Avoid saturated colours.
