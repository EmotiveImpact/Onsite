# Heron Estate — Blender level

The active game loads `public/models/onsite-heron-court.glb`. The architecture is authored in
`assets/blender/onsite-heron-court.blend`, built by `scripts/build-estate.py`. It replaces the
runtime box-building presentation in `View.ts`; the working WWB controller, combat and layered
navigation remain in place.

The editable file has 2,145 architectural objects: residential bays with different roof heights,
window frames/sills, bevelled concrete, gallery balusters/handrails, two dogleg stair cores,
stair nosings/rails, downpipes, conduits, bulkheads, doors, planters/planting, drains, cycle rails,
a service kiosk and shallow puddles. Packed PBR preview materials are included. Ten donor prop
placements appear in a separate collection; see `public/models/donors/provenance.json`.

## Collections and ownership

- `01_RENDER / Heron Estate`: editable architecture, metre scale. GLB is Y-up; Blender is Z-up.
- `02_COLLISION / Rapier source solids`: hidden wire guides from the level manifest; never exported.
- `03_NAVIGATION / stairs and spawns`: hidden route/marker guides; never exported.
- `04_DRESSING / credited donor props`: imported models with editable transforms. Their runtime
  placements are recorded in `src/onsite/dressing.json` and the models load separately.
- `05_PREVIEW / lighting and cameras, not exported`: Blender review setup only.

The export merges architecture by material (14 runtime meshes) and bakes local five-direction
vertex occlusion. It contains no images; Three.js assigns the existing PBR maps by material
name. Blender light objects do not become the game's lighting. `View.ts` constructs lights and
uses the credited Poly Haven HDRI for sky/reflections. Puddles use environment reflections;
there is no screen-space reflection pass.

The `.blend` is the editable visual source. `level.ts` remains the physical layout authority:
changing a major wall/stair in Blender requires updating that collision description and
re-running the navigation tests. Do not derive the nav graph from decorative render triangles.
Large donor obstacles (car, bins, upper barrier) get separate box colliders measured from their
Blender bounds. Small foliage/lighting details are render-only. No second movement controller.

## Rebuild and edit

Open the `.blend` directly in Blender. To rebuild the authored starting level from scripts:

```sh
npm run assets:estate
npm run typecheck
npm test
npm run dev
```

The full build recreates the file from the script; preserve manual edits before running it.
After editing an existing `.blend`, use `blender -b --python scripts/export_estate.py` to export
its architecture. This refreshes packed preview materials and the runtime occlusion bake.
Donor transforms and collision changes must also be reflected in the placement/layout manifests.

`npm run evidence:layout` updates the as-built collision drawing. `npm run evidence:route`
drives the actual player up/down both stairs in the browser, with bots disabled and a visible
verification label. `node scripts/check-presentation.mjs` freezes the real reload clock for
inspectable pose screenshots; it is a test fixture, not ordinary gameplay.

## Asset boundaries

The IRONLINE M4/posed hands, seven Poly Haven props and HDRI are individually licensed art imports.
The rifle's two external arm textures are included. Runtime dark-kit tint and reload IK are
original ONSITE code; WWB still owns ammo, hitscan, recoil and reload completion. No Fab rifle
motion tracks or unlicensed Claudefare implementation are imported. Donor repositories remain
ignored and outside production bundles. Credits ship at `/credits.html` and under `public/licenses`.

Current opponents still use the original stylised hooded Blender model. A detailed black hoodie,
trainer and jogger character with a proper animation rig remains outstanding.
