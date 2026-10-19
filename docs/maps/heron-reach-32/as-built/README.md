# Heron Reach as-built

This records the B01 [build brief](../blueprints/CLAUDE-BUILD-BRIEF.md) as built: the whole
144 × 120 m map with all four blocks, five levels, the art pass and blue-hour lighting. Heron Court
is still the default level and the regression baseline. Networking is not part of this build, and
nothing here claims 32-player readiness.

## Play it

Run `npm run dev` and open `/?map=heron-reach`. The plain URL is Heron Court.

- `&art=0` shows the collision blockout instead of the Blender art.
- `&rain=0` turns the rain off.

## What is built

[`src/onsite/heronReach.ts`](../../../../src/onsite/heronReach.ts) generates the playable shell
from `build-spec.json` and `map.json`. There is no hand placement. The Blender art is built around
the same boxes and never changes them (see the [art pipeline](../art/README.md)).

- **Blocks:** Rowan House (NW), Ash House (NE), Birch House (SW) and Cedar House (SE), each with G,
  L1 and L2 floors. Rowan and Cedar have playable roofs at +9 m; Ash and Birch roofs are closed.
- **Homes:** H1 flats at ground level and H2 maisonettes across +3 and +6 with private stairs.
- **Cores:** eight public stair cores, S1 to S8. S2, S3, S6 and S7 go down to B1. The southern
  blocks are the northern ones mirrored, and their cores and homes have their own capsule runs.
- **Galleries and bridges:** the L1 galleries with the two 24 m bridges, the L2 islands, and core
  aprons at every served level. Every exposed edge has a 1.2 m guard.
- **Ground:** the arcades, the shops (Launderette, Cycle Workshop, The Corner, Youth Room,
  Washhouse, Estate Office), Garden Court, The Cage and Washhouse Square, the service lanes and
  the two staging yards behind the boundary wall.
- **Undercroft (B1):** an enclosed 48 × 60 m loop under the courts, reached from four cores.
- **Round:** six bots (EAST YARD, THE CAGE, NORTH BRIDGE, GARDEN COURT, CEDAR ROOF, UNDERCROFT), a
  five-minute timer, and a floor-aware capture at The Cage.
- **Dressing:** lamps, street furniture, shop fit-outs, the Cage, trees and planting, estate signs,
  bin stores, a fenced substation, litter and fly-tipping. Large items have box colliders that keep
  door arcs, spawns, stair entries and objective rings clear.

## Deviations from B01

The generator writes these into the layout, and the as-built plan prints them.

1. Shop and service shells are 2.8 m walls under a 0.2 m roof slab (3.0 m overall, as B500).
   Where the +3 west and east galleries pass over a shop, the gallery slab is the roof.
2. Concrete columns (0.4 m square, 6 m grid) carry the exposed +3 slab edges down to open ground.
   They are not drawn in B01. Each has collision, none sits within 1.8 m of a ground doorway, core
   aprons cantilever, and the two 24 m bridges stay column-free.
3. Two five-a-side goals stand against the Cage end fences, offset 5.5 m from the end gates so the
   B500 gate routes stay open.
4. A 3 m boundary wall with railings encloses the site. The street and skyline beyond it are
   render-only.
5. The Cage fence (2.6 m, four 4 m gates) blocks movement but not bullets or bot sight, matching the
   B500 note that the mesh is visually porous.
6. The dressing adds 136 prop colliders.

## Evidence

- [`heron-reach-as-built.png`](heron-reach-as-built.png) shows all five levels. It is drawn from
  the runtime collision boxes and the layered navigation graph, not from the B01 drawings.
  Regenerate it with `npx tsx scripts/maps/heron-reach-as-built.ts` and
  `python3 scripts/maps/draw_heron_as_built.py`.
- [`tests/heron-reach.test.ts`](../../../../tests/heron-reach.test.ts) (17 tests) checks the
  following:
  - the real player capsule climbs every core through each served level and back;
  - both H2 routes work in each orientation;
  - a WWB bot physically takes the cores, including G down to B1 and back;
  - guards hold a sprinting player at gallery, bridge, island and roof edges;
  - the shell connects both yards, the bridges, every +6 island, both roofs and the undercroft
    loop;
  - headroom is at least 2.4 m;
  - the capture counts the ground but not the undercroft below or the galleries above.
- `node scripts/maps/verify-heron-reach.mjs` is an input-driven browser run on the preserved WWB
  runtime: mouse look, aim, fire, reload, pause, jump, then the full fight, capture and round
  reset. The last run (cloud SwiftShader, `&art=0&rain=0`) put all 6 opponents down with the player
  on 96 health, captured The Cage, and reset the round.
- `node scripts/maps/heron-reach-stills.mjs` writes browser stills. These are **inspection
  fixtures**: `?inspect` places the player at fixed viewpoints. They show the real runtime with the
  Blender art, but they are not gameplay evidence.
- Heron Court still passes `scripts/verify-encounter.mjs`: 3 opponents down, capture, reset.

## Performance

Measured in the cloud with **SwiftShader, a software renderer, not a real GPU**. These numbers say
nothing about smooth gameplay on real hardware, and no real-GPU measurement exists yet.

| View (art on, rain on) | Draw calls | Triangles |
| --- | ---: | ---: |
| Roof terrace | 200 | 1.06 M |
| Ground arcade | 254 | 1.12 M |
| L1 gallery | 301 | 1.18 M |
| Undercroft | 296 | 1.21 M |
| Garden Court | 308 | 1.19 M |
| The Corner | 470 | 1.30 M |
| The Cage | 538 | 1.32 M |
| Washhouse Square | 662 | 1.36 M |

Draw calls and triangles include the shadow pass. The mean frame time was about 650 to 700 ms on
SwiftShader. With the blockout (`&art=0`) the same fight runs at about 650 ms per frame with 26 draw
calls and 72k triangles.

Download for the map (excluding the shared game bundle) is about 34 MB: 11.4 MB of meshopt-compressed
models, 21 MB of WebP textures and 1 MB of decals. With RGBA8 and mipmaps, every texture the map
can load would take about 600 MB of GPU memory. Only materials that are actually placed get
loaded, so the real figure is lower. GPU texture compression (KTX2) is the next step if that
proves too much.

What has been done for performance so far:

- Arch meshes are joined per 36 × 30 m chunk and material.
- Every kit asset is instanced.
- Grass is drawn in 8 m tiles hidden beyond 40 m.
- Parked cars use 2.6k-triangle far variants.
- Lamp glows, reflection streaks, puddles and graffiti are batched into four draws.
- ORM maps are at half resolution.
- Software rendering automatically drops bloom, thins the grass and uses fewer point lights.
