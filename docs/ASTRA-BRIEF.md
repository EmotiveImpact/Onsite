# Brief for Astra: push Heron Reach towards the concept art

## Current owner instruction and continuation

The owner subsequently **deferred real-GPU benchmarking** and authorised visual implementation.
Do not reinstate it as a blocker. The seven-item art pass is on
`codex/heron-reach-textures-dressing`, stacked above six focused branches; it has not been merged
by this session. Read the [current work log](maps/heron-reach-32/art/ART-PUSH-2026-10-19.md) before
repeating this original queue. That log records actual code, assets, validation and limitations.
The original brief below remains the visual direction. Networking stays deferred.

The next quality item is now on `codex/heron-reach-scene-depth`, stacked on that
complete pass. Read the [current goal](development/NEXT-QUALITY-GOAL.md) and
[scene-depth work log](maps/heron-reach-32/art/SCENE-DEPTH-2026-10-19.md) before
repeating the earlier queue. It adds actual scanned fittings/covers, original
Blender shop detail, floor/visibility-aware lighting and scoped height haze.
Collision, navigation and gameplay remain unchanged.

Written 19 October 2026 for whoever picks this repository up next under the name Astra. It assumes
you are starting cold. Read it top to bottom once, then use the priority list as your work queue.

## What ONSITE is

A bots-first browser FPS set on a fictional South London council estate. It runs on Three.js
0.186 and Rapier 0.21 with the MIT-licensed WWB gameplay modules (player, Arsenal, bots, round
rules). Networking is deliberately deferred. There are two maps:

- **Heron Court** (`/`): the small 36 × 30 m courtyard. It is the default map and the regression
  baseline. It must keep working after every change.
- **Heron Reach** (`/?map=heron-reach`): the 144 × 120 m, four-block, five-level estate. This is
  the map to improve. It is live at <https://onsite-azure.vercel.app/?map=heron-reach>.

`main` deploys to Vercel automatically on every merge, so anything you merge is public within
minutes. Work on a branch and open a pull request.

## Rules that are not negotiable

These come from [CLAUDE.md](../CLAUDE.md) and the owner's decisions. Read CLAUDE.md in full.

- Build on the existing runtime (`index.html` → `src/onsite/main.ts`). Do not start a new
  prototype, swap engines or replace the WWB movement, Arsenal, bots or round systems. The old
  standalone prototype in `game/` is parked; its mood is a reference, its code is not a base.
- Collision and navigation belong to code (`src/onsite/heronReach.ts` for Heron Reach,
  `src/onsite/level.ts` for Heron Court). Art is built around those boxes and never moves them.
  One Rapier world owns movement.
- Every texture and mesh needs provenance. Nothing gets downloaded and dropped in without a
  licence note. Keep `research/reference-clones/` out of the build.
- Keep the Black British character direction, the original concept art and the ONSITE HUD style.
- The look is **blue hour** (dusk with a little light left in the sky), not full night.
- Be honest about evidence. Screenshots from `?inspect` are inspection fixtures, not gameplay.
  Numbers from SwiftShader (the software renderer used in cloud machines) are not real-GPU
  performance and say nothing about smoothness.
- Write in British English.

## Run and test

Node 24 is expected (`npm test` uses a Node 24 flag). On Node 22, run the pieces directly as
shown below.

```sh
npm ci
npm run dev                 # then open /?map=heron-reach  (the plain URL is Heron Court)

npm test                    # all unit and navigation tests (Node 24)
# On Node 22:
node --test tests/simulation.test.js
npx tsx --test tests/wwb-navigation.test.ts tests/estate-assets.test.ts tests/heron-reach.test.ts

npm run typecheck
npm run build
```

Useful URL switches on Heron Reach: `&art=0` shows the collision blockout, `&rain=0` turns rain
off, `&inspect` freezes bots for camera placement.

Browser checks run against a frozen build, because the dev server reloads mid-run when `src/` or
`props-manifest.json` changes:

```sh
npm run build && npm run preview -- --port 4173 &
ONSITE_URL=http://127.0.0.1:4173 CHROMIUM=/path/to/chromium node scripts/maps/verify-heron-reach.mjs
ONSITE_URL=http://127.0.0.1:4173 CHROMIUM=/path/to/chromium node scripts/maps/heron-reach-stills.mjs
ONSITE_URL=http://127.0.0.1:4173 npm run test:browser      # Heron Court regression
```

The scripts default to `/usr/bin/chromium`; set `CHROMIUM` if yours lives elsewhere. They force
SwiftShader, so lighting in their stills is a reduced version of what a real GPU shows (no bloom,
thinner grass, fewer point lights).

## How Heron Reach is built

Start with these, in order:

1. [as-built/README.md](maps/heron-reach-32/as-built/README.md): what exists, deviations from the
   blueprints, evidence and performance numbers.
2. [art/README.md](maps/heron-reach-32/art/README.md): the art pipeline end to end.
3. [art/CONVENTIONS.md](maps/heron-reach-32/art/CONVENTIONS.md): scale, UVs, material names, file
   layout and the look target. Follow it for every new asset.
4. [art/TEXTURES.md](maps/heron-reach-32/art/TEXTURES.md), [FOLIAGE.md](maps/heron-reach-32/art/FOLIAGE.md),
   [PROPS.md](maps/heron-reach-32/art/PROPS.md): the kits and how each one was made.
5. [blueprints/CLAUDE-BUILD-BRIEF.md](maps/heron-reach-32/blueprints/CLAUDE-BUILD-BRIEF.md): the
   original design brief and its dimensioned drawings.

In short:

| Layer | Where | Notes |
| --- | --- | --- |
| Playable shell, collision | `src/onsite/heronReach.ts` | Generated from `build-spec.json` and `map.json`. |
| Dressing plan | `src/onsite/heronReachDressing.ts` | Deterministic placement; big props get box colliders. |
| Runtime art | `src/onsite/heronReachArt.ts` | Loads GLBs, assigns materials, sky, lamps, glow, puddles, decals, rain, bloom. |
| Blender build | `scripts/maps/art/build_heron_reach_art.py` and `heron_art_*.py` | Headless Blender 5.2 as a Python module. |
| Rebuild everything | `npm run assets:heron-reach` | Layout export, Blender build, GLB export, gltfpack. |
| Textures | `scripts/maps/art/make_heron_*.py` | numpy and Pillow, written as WebP to `public/materials/heron/`. |
| ChatGPT source images | `docs/maps/heron-reach-32/art/generated/` | 33 images; `make_heron_generated.py` crops and packs them. |
| South London kits | `assets/blender/heron-reach/south-london/` | Signs, services, car park, structures; `mat_*` names map to `hr_*`. |

Blender has no GUI here. Cycles CPU renders work for previews; do not rely on EEVEE. Preview
renders are for judging geometry and materials, not the in-game lighting.

## Where the look stands

The target is the concept art in [docs/concepts/onsite-london-fps.png](concepts/onsite-london-fps.png)
and the ten scenes in [docs/concepts/screens/](concepts/screens/). The latest in-game stills
(19 October, SwiftShader, inspection fixtures) are in
[maps/heron-reach-32/art/stills-2026-10-19/](maps/heron-reach-32/art/stills-2026-10-19/).

Side by side, the layout, materials and HUD are in the right family. The biggest differences are in
light, wetness, atmosphere and the density of detail near the eye. Compare these pairs:

| Concept | Current still | What is missing |
| --- | --- | --- |
| `screens/10-football-court.png`, top panel of `onsite-london-fps.png` | `03-the-cage.png` | Mirror-wet court with long warm streaks; tall floodlight columns throwing real pools; painted court lines; fence reads as fine chain link, ours as a coarse dark grid that aliases badly; goals with nets. |
| `screens/05-corner-shop.png`, bottom right of `onsite-london-fps.png` | `06-corner-shop.png` | The shop interior is bright, stocked and visible through the glass, spilling warm light onto wet paving. Ours has dark glass, a sign light that blows out, and no spill. The shop interior images exist but are unused. |
| `screens/02-stairwell.png` | `08-core-entrance.png` | Concept cores are tall glazed stairwells: fluorescent strips, painted level numbers, pipes, wet concrete. Ours read as a small brick box with one hot light and white, flat window panes. |
| `screens/01-estate-entrance.png`, top panel of `onsite-london-fps.png` | `02-garden-court.png`, `01-overview.png` | Concept towers are close, tall and detailed (balconies, frames, varied lit windows) and sit in haze. Ours are plain boxes with dot windows at a constant brightness, with no aerial perspective. Trees in the concept are bare winter trees with fine branches; ours are chunky. |
| All scenes | All stills | Haze and depth layering; strong warm/cool contrast between 2700 K lamps and blue air; rain reading as streaks catching light rather than white lines; wet reflections everywhere at ground level. |

Two caveats before you act on that table. The stills were taken on a software renderer, which
switches bloom off and cuts lights, so get one real-GPU capture first. And the concept art is
painted, so treat it as a mood and composition target, not something to match pixel for pixel.

## Priority list

Each item names its likely home in the code. Do them roughly in this order; the first two decide
how much the rest will show.

1. **Measure on a real GPU.** Nobody has. Play the live map on a real machine, record frame time,
   draw calls (`__onsite.metrics()`) and texture memory at The Cage, Washhouse Square and The
   Corner (the heaviest views), and take stills at the same viewpoints as
   `stills-2026-10-19/`. Write the numbers into `as-built/README.md` under a clearly labelled
   real-GPU heading. Everything after this depends on knowing the budget.
2. **Wet ground and reflections** (`heronReachArt.ts`, material setup). The single biggest gap.
   Lower roughness on ground materials with a puddle/wetness mask, stretch the lamp reflection
   streaks, and consider a cheap screen-space or planar reflection for ground only, behind a
   quality switch. Keep the SwiftShader fallback.
3. **Lamp light and atmosphere** (`heronReachArt.ts`). Brighter, larger warm pools under lamps;
   height fog or exponential fog tinted blue; distance haze on the skyline; light catching rain.
   Check bloom thresholds on a real GPU so signs don't blow out (The Corner sign does now).
4. **The Cage** (`scripts/maps/art/heron_props_cage.py`, dressing). Fine chain-link with
   alpha-to-coverage or a proper mipmapped alpha texture and anisotropic filtering, green
   painted posts, tall floodlight columns, painted court lines and goal nets. It is the main
   objective, so it deserves to look like screen 10.
5. **Shop interiors** (`make_heron_generated.py`, `heron_props_shop.py`). Use
   `generated/shops/corner-shop-interior.png` and `launderette-interior.png` as interior cards or
   a simple parallax interior behind the glass; add warm spill light on the pavement.
6. **Stair cores** (`heron_art_arch.py`). Larger glazing, fluorescent strip fittings with an
   emissive and a light, painted level numerals large on the wall (the kit has
   `hr_decal_level_numerals`), exposed pipes, and fix the white window panes.
7. **Skyline and near towers** (`heron_art_context.py`). Add a middle ring of modelled towers at
   60 to 150 m with balconies and frames, vary lit-window brightness and colour, and fade them
   into haze. Reuse the tower elevations in `generated/backdrop/`.
8. **Trees** (`make_heron_foliage.py`). Bare or thinning winter planes with fine branch cards,
   closer to the concept silhouettes.
9. **Texture memory** (about 600 MB worst case with RGBA8 and mipmaps). Move to KTX2/Basis with
   `gltfpack -tc` or `toktx`, keep WebP as the fallback, and measure before and after.
10. **Pigeon netting** is drawn (`generated/decals/hr_decal_pigeon_net.png`) but not placed.
    Put it on gallery openings and balconies in the dressing plan.
11. **HUD parity** (`src/onsite/` HUD code). The concept shows a world-space diamond marker with
    the objective name and distance (for example "HOLD THE COURT 18m"). Ours shows a text
    objective in the corner. Add the marker in the existing ONSITE style.

Out of scope unless the owner asks: networking, a new weapon or character pipeline, DLSS-style
upscaling (an idea was parked: render smaller then sharpen, with automatic resolution drop),
and rebuilding Heron Court.

## How to deliver

- One branch and one pull request per item, with before and after stills from the same
  viewpoints. Say whether each still is SwiftShader or a real GPU.
- Run the unit tests, typecheck, build, `verify-heron-reach.mjs` and the Heron Court browser check
  before asking for review.
- If you rebuild Blender assets, commit the regenerated GLBs, WebPs and manifests together, and
  check the download size in `as-built/README.md` still holds.
- Record new assets' provenance in the kit documents.
