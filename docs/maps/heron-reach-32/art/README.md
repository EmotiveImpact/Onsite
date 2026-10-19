# Heron Reach art pipeline

The playable shell is generated in [`src/onsite/heronReach.ts`](../../../../src/onsite/heronReach.ts).
The art is built around those collision boxes in Blender and never changes them. Big props add
their own box colliders through the dressing plan, so the navigation tests always run against
what the player actually walks into.

## Rebuild

```sh
npm run assets:heron-reach
```

That runs, in order:

1. `scripts/maps/export-heron-layout.ts` writes `assets/blender/heron-reach/layout.json`: every
   collision box plus the semantic layout (openings, homes, cores, guards, columns, dressing,
   light anchors).
2. `scripts/maps/art/build_heron_reach_art.py` builds `assets/blender/heron-reach/heron-reach.blend`:
   - `heron_art_arch.py`: facades with per-side brick and plaster; windows with frames, sills,
     lintels and lit interior cards; render-only windows cut into blank brick runs; doors held
     open; slab edges; gallery upstands with handrails; stair nosings; columns; roofs and parapets;
     ground zoning with kerbs; undercroft services; home interiors; painted core level numbers;
     ceiling strip fittings; and facade fittings (downpipes, dishes, airbricks, vents).
   - `heron_art_context.py`: the render-only world outside the wall, with the street ring,
     terraces across the road and a tower skyline at 150 to 300 m wearing the painted tower
     elevation.
   - `heron_art_materials.py`: materials by name from the texture kit's WebP sets.
   It also writes `public/models/heron-reach/grass-cells.json` and `facade-dressing.json`.
3. `export_heron_reach_glb.py` joins the authored objects per 36 × 30 m chunk and material, then
   exports `heron-reach-arch.glb` without images. `runtime-materials.json` tells the game which
   textures, UV repeat, wetness and emission each material uses.
4. `export_heron_kits_glb.py` exports the props and foliage kits, one root node per asset.
5. `gltfpack` applies meshopt compression to all three GLBs.

Preview stills come from `python3 scripts/maps/art/render_heron_preview.py OUT [view ...]`. These
are Cycles CPU renders for judging geometry and materials, not the game's lighting.

## In the game

[`src/onsite/heronReachArt.ts`](../../../../src/onsite/heronReachArt.ts) loads the GLBs and
assigns the named materials. It instances the kits from the dressing plan, and scatters grass in
8 m tiles that are hidden beyond 40 m. It also sets up the blue-hour atmosphere:

- a graded dusk sky that is also used for reflections;
- a pool of real point lights handed to the nearest lamps;
- glow sprites and wet-ground reflection streaks under every lamp;
- puddles and graffiti decals;
- rain that thins out under cover;
- bloom on real GPUs.

Two URL switches help when checking the art:

- `?map=heron-reach&art=0` shows the collision blockout instead of the Blender build.
- `&rain=0` turns the rain off.

[`src/onsite/heronReachDressing.ts`](../../../../src/onsite/heronReachDressing.ts) is the
deterministic dressing plan. It places:

- lamps (the plan's lights, a perimeter ring and one over every exterior door);
- CCTV, intercoms and notice boards;
- benches and bins around the objectives;
- bollards at the arcade mouths;
- fit-outs for each shop;
- service-lane bins;
- roof plant;
- the Cage panels and goals;
- trees and planting;
- litter and fly-tipping;
- block name, fire, bin and dog signs, dry risers, grit bins, bin stores and a fenced substation;
- caged lamps, cable trays and pipes in the undercroft;
- washing out on a few gallery balconies;
- parked cars, bike hangars and speed cushions beyond the wall.

Colliding props keep door arcs, spawn positions, stair entries and objective rings clear.

## Kits

- [Textures](TEXTURES.md): 22 seamless PBR sets, decals, the window-interior atlas and the
  tower facade.
- [Foliage](FOLIAGE.md): London planes, birches, grass clumps, shrubs, hedges, weeds and leaf
  litter.
- [Props](PROPS.md): street furniture, the Cage, vehicles, shop fit-outs and clutter.
- South London gap-fill kits in
  [`assets/blender/heron-reach/south-london/`](../../../../assets/blender/heron-reach/south-london/README.md):
  estate signs, car park and undercroft services, bin stores, a substation, garages, bike hangars,
  window grilles and fly-tipping. Made in this project by the South London research thread; the
  runtime maps their shared `mat_*` surfaces onto the texture kit's `hr_*` sets.
- [Conventions](CONVENTIONS.md): the shared rules for scale, UVs, material names and files.

Every texture and mesh is original work, made procedurally or by script in this project, apart
from the skyline tower elevation, which started as a ChatGPT image made for this map. No
downloaded assets are used. The kit documents record how each one was made.
