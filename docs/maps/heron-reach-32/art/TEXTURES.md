# Heron Reach texture and material kit

The shared PBR kit for the Heron Reach art build. It follows [the art conventions](CONVENTIONS.md):
material names, coverage, WebP files in `public/materials/heron/`, OpenGL normals and glTF ORM
packing (R occlusion, G roughness, B metalness).

## What is in the kit

- **22 tiling sets** (`hr_brick_stock` to `hr_plaster`): `<name>-color.webp`, `-normal.webp` and
  `-orm.webp`, 1024 px, covering 2 m (1 m for the three steels and rubber). Every map wraps
  seamlessly. Brick is re-laid at 26 courses by 9 bricks per 2 m (about 77 mm courses and 222 mm
  brick pitch), paving slabs at 4 by 4 (500 mm), red pavers as a 45-degree herringbone of
  202 by 101 mm pavers, board-marked concrete at 10 boards (200 mm), the roller shutter at 24 laths
  (83 mm) and bench timber at 8 planks (250 mm). Joints, courses and laths run straight and
  continuously across the tile edges.
- **Decals** in `decals/`: rain streaks below sills, blotchy grime, moss and algae edge, puddle
  mask, normal and wet tint, worn double yellow line, worn white court line, a cast-iron gully
  grate (colour, normal, ORM), a 2 by 2 atlas of abstract graffiti tags and tileable leaf stains.
- **Lit windows** in `windows/`: an 8 by 4 atlas of dusk room views (`interiors-color.webp` and
  `interiors-emit.webp`, 2048 by 1024). Each 256 px cell is one 1.2 by 1.5 m pane: drawn curtains,
  net curtains, venetian blinds, lamp glow, dark rooms, TV glow and kitchen strip lights. Warm
  2700 K dominates; kitchens are 4000 K and TVs are blue.
- **Distant tower facade** in `backdrop/`: a 12 by 12 m tileable patch of a 1960s precast
  concrete tower (4 storeys by 4 bays) with colour and emission maps for low-poly background towers.
- **Generated images**, processed by `scripts/maps/art/make_heron_generated.py`:
  - `backdrop/tower-elevation-{a,b}-{color,emit}.webp`: two full tower fronts (a concrete and brick
    point block, a deck-access slab) used as `hr_tower_elev` and `hr_tower_elev_b` on the skyline
    towers, tiled across in 17 m bays. The emission maps keep only the warm lit windows.
  - `backdrop/skyline-panorama.webp`: the far city on a 470 m ring behind the towers, three repeats
    round, its top quarter faded so the sky dome shows above it.
  - `windows/interiors-photo-{color,emit}.webp`: the window atlas used at runtime, with twelve
    interiors (living rooms, kitchens, net curtains, blinds, a TV-lit bedroom, a hallway, a
    bathroom and more), their mirror images and four close-ups. Cells 4, 12, 20 and 28 keep the
    procedural dark curtains, which the Blender build uses for unlit windows.
  - `decals/graffiti-photo-atlas.webp`: six graffiti pieces (2 by 3) for the undercroft and core
    flanks.
- **Blender library** `assets/blender/heron-reach/materials.blend`: one Principled BSDF material
  per conventions name, the 9 plain shared materials, `hr_decal_<kind>` materials, plus
  `hr_window_interior` and `hr_backdrop_tower`. Images are packed. Tiling materials use
  UV Map, then Mapping (scale 1 / coverage, so 1 UV unit = 1 m), a Normal Map node and a
  Separate Color split of the ORM map, with occlusion wired to a `glTF Material Output` group.

## glTF export

`bpy.ops.export_scene.gltf` (GLB, image format WEBP or AUTO) writes the Mapping scale as
`KHR_texture_transform` on every texture of the material (scale 0.5 with offset 0, 0.5 for a
2 m set; the offset is the exporter's flip from Blender's bottom-left UV origin). A scale of 1
writes no transform. The ORM image is reused for both `metallicRoughnessTexture` and
`occlusionTexture`. Images stay WebP, so the GLB lists `EXT_texture_webp` and
`KHR_texture_transform` as required extensions. Emission above 1 writes
`KHR_materials_emissive_strength`. The drain decal (Round on alpha) exports as `MASK`; the soft decals export as `BLEND`.
Full results are in the manifest under `gltfExportTest`.

## Provenance

- The colour basis of each tiling set is the matching generated image from the repo's own
  texture pack, `assets/textures/source-30/` (see [the pack notes](../../../concepts/TEXTURE-PACK-30.md)).
  Those images were delit, re-laid or quilted, resampled and graded here. Source paths and
  SHA-256 hashes are recorded per texture.
- All normal, ORM, decal, window and facade maps are original, derived or drawn procedurally by
  the kit scripts with numpy and Pillow. Nothing was downloaded. No Poly Haven map is reused: the
  existing CC0 sets in `public/materials/pbr/` were not needed, so the manifest's
  `reusedPolyHaven` field is empty for every set.
- The graffiti is abstract marker strokes only: no letters, words, crew names or brands.
- The generated images above started as ChatGPT images made on the project's own account for
  this map (`docs/maps/heron-reach-32/art/generated/`, merged to main from the `claude/chatgpt-images` branch,
  commit dd803c9). The script only crops, resizes, packs and keys them. They depict no real
  building, home or person. The graffiti pieces are illegible wildstyle and bubble letters with no
  readable words, crew names or brands.
- Underpass tiles (`hr_tile_underpass`, undercroft walls to 2.4 m), exposed aggregate concrete
  (`hr_concrete_aggregate`, gallery upstands), glass blocks (`hr_glass_blocks`, stair core strips),
  wired glass (`hr_wired_glass`, core door vision panels), painted stair treads (`hr_stair_tread`,
  one map per core step), the void sheet, and the tag, buffed-patch and gum decals come from the
  same ChatGPT commit, seam-healed and cropped by the South London research thread
  (`/mnt/project-files/south-london/assets/textures-generated/`).
  `scripts/maps/art/make_heron_sl_textures.py` resizes them and derives normal and ORM maps from
  their luminance. The tags are illegible marker tags and throw-ups.

## Rebuilding

```sh
python3 scripts/maps/art/make_heron_textures.py      # 22 tiling sets (about 3 minutes)
python3 scripts/maps/art/make_heron_decals.py        # decals, windows, facade
python3 scripts/maps/art/make_heron_materials.py     # .blend, glTF test, Cycles previews
```

Pass material names to the first script to rebuild only those sets. The manifest
`assets/blender/heron-reach/materials-manifest.json` records, per texture, the processing
steps, coverage, seam ratios (wrap-edge difference over the typical adjacent-pixel difference;
phase-matched for jointed surfaces), file sizes and hashes.

## Known limits

### Wet-ground addition, 19 October 2026

`make_heron_wetness.py` generates `decals/wetness-mask.webp` and `decals/lamp-streak.webp`
from deterministic periodic noise and a rippled falloff (NumPy/Pillow, seed 741). They are original
ONSITE procedural work; no external pixels or model were used. Both are 512 px. The mask uses
linear data and repeats every 11 world metres; the streak is an sRGB RGBA texture.
`decals/wetness-manifest.json` records hashes and sizes. The runtime uses the existing PBR ground
maps and dusk environment, with no added render pass or changes to collision.

### Shop backdrop addition, 19 October 2026

`make_heron_shop_textures.py` prepares the existing project ChatGPT images
`generated/shops/corner-shop-interior.png` and `launderette-interior.png` at 1024 × 512,
WebP quality 88. Sources are preserved; no external pixels were downloaded. The source commit
is `dd803c9`, the same generated-image set already credited above. Source/runtime hashes and
processing notes live in `public/materials/heron/shops/manifest.json`.

The Blender shop-detail kit places single-sided backdrops against existing rear walls, behind the
three-dimensional shelves and washers. Rear doorway gaps stay clear. These are lit image cards,
not fully modelled shelves inside the image; the existing prop geometry supplies foreground depth.

- The source images are generated and not physically measured, so coverage is a modelling
  decision, made to fit real brick, slab and paver sizes.
- Aged steel and render keep some mid-scale blotches, so repeats show on very large flat areas.
  Break them up with decals or vertex-colour variation.
- The window interiors are flat-shaded painted views meant for glazing seen from outside. They
  carry no parallax.
