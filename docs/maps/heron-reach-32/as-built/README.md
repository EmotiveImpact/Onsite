# Heron Reach as-built: step 1, Rowan House

This is step 1 of the [B01 build brief](../blueprints/CLAUDE-BUILD-BRIEF.md): one complete block
and both stair types, checked with the real WWB capsules before any repeated detail is added.
Heron Court is still the default level and the regression baseline.

## Play it

Run `npm run dev` and open `/?map=heron-reach`. Use the plain URL for Heron Court.

## What is built

[`src/onsite/heronReach.ts`](../../../../src/onsite/heronReach.ts) generates the level from
`build-spec.json` (walls, openings, stairs, voids) and `map.json` (gallery and apron rectangles,
cover, lights). There is no hand placement. The render meshes are built from the same boxes as the
collision, so the two cannot drift apart.

- **Rowan House:** the 36 × 18 m block, with G, L1 and L2 floors and the playable roof at +9 m.
  Reserved solid strips, the common hall and the ground arcade are included.
- **Homes:** NW-H1-1 and NW-H1-2 at G, and the NW-H2-1 and NW-H2-2 maisonettes across +3 and +6
  with their ST-H private stairs. The +6 floor has the H2 void cut out once.
- **Public cores:** S1 serves G to R and S2 serves G to R (ST-P). Each storey has 10 risers and
  9 treads per flight, a half landing, door thresholds, a well balustrade, a 1.2 m well guard and
  a non-walkable cap above the top storey.
- **Galleries:** the L1 north gallery and the core aprons at L1, L2 and R. Floor rectangles are
  unioned, then the cores are subtracted. Every exposed edge gets an automatic 1.2 m guard,
  placed outside the clear width.
- **Doors and windows:** doors are held open. Glazing is closed, so it blocks movement, bullets
  and bot sight.
- **Objective:** a temporary floor-aware capture in the Rowan ground arcade. The galleries above
  it never count.

## Deviations from B01

1. B01 has S2 serving B1. The undercroft is not built yet, so S2 starts at G and the ground
   inside the core stays closed.
2. The L1 north gallery stops at x = 63, at the end of the S2 apron, with a temporary guard. The
   24 m bridge to Ash House and the west gallery spur come in later steps.
3. A 2.4 m site hoarding closes the 54 × 42 m step-1 pad. It is removed as neighbouring blocks
   are built.

No southern block is built yet. The mirror transform is implemented in the generator, but it has
not been verified: the mirrored south core and home still need their own capsule run in step 2.

## Evidence

- [`rowan-step1-as-built.png`](rowan-step1-as-built.png) is drawn from the runtime collision
  boxes and the layered navigation graph, not from the B01 drawings. Regenerate it with
  `npx tsx scripts/maps/heron-reach-as-built.ts`.
- [`tests/heron-reach.test.ts`](../../../../tests/heron-reach.test.ts) runs in `npm test` and
  checks the following:
  - the actual player capsule climbs S1 and S2 from G to R and back down;
  - the player takes the H2 route (front door at +3, private stair, rear door at +6) both ways
    without using a public core;
  - a WWB bot physically takes S1 and S2 to L2 and back;
  - a sprinting player is held at gallery, concourse and roof edges (with the guards removed,
    the same runs fall);
  - stair and landing headroom is at least 2.4 m;
  - the capture area ignores the floors above it.
- `node scripts/maps/heron-reach-stills.mjs` writes browser stills to `test-results/heron-reach`.
  These are **inspection fixtures**: `?inspect` places the player at fixed viewpoints. They show
  the real runtime but are not gameplay evidence.

## Performance

Measured with cloud SwiftShader, not a real GPU: about 310 ms per frame, 18 draw calls and
49.5k triangles with the blockout and three bots. This says nothing about smooth gameplay.
Bundling the two map JSON files adds about 75 kB to the main script before gzip.
