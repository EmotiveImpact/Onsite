# South London homes pass

Baseline / safe recovery: local commit `0ce5a14`. Create a separate checkout from that commit to
inspect the earlier courtyard; do not reset or overwrite newer work. Original concepts, source
textures, donor imports, weapon Blender file and courtyard dressing are retained.

## Photographs actually inspected

Four photographs were downloaded and visually inspected on 18 October 2026. Exact image URLs and
hashes are recorded in `research/SOUTH-LONDON-REFERENCES.json`. They are references only: no
photograph pixels are used as textures or bundled into the game.

- [Dawson's Heights, East Dulwich](https://en.wikipedia.org/wiki/Dawson%27s_Heights): the overall
  stepped roofline and the Overhill Road courtyard photograph. Yellow stock brick, white window
  frames, horizontal slab bands, paired openings and projecting private balconies inform the new
  upper homes. The reference also has planted edges and individual curtains/satellite dishes.
- [Brandon Estate](https://en.wikipedia.org/wiki/Brandon_Estate): point blocks surrounded by green
  space, plus the close-up of ribbed exposed-aggregate concrete below domestic windows. These
  inform two background point blocks, concrete spandrel ribs and more varied window treatments.

Heron Court remains a fictional SE15 estate. It is not a reconstruction of either photographed
estate. The proposed 36×30 m arena continues to guide the playable footprint.

## What was built

`scripts/build_homes.py` is an idempotent Blender pass over the existing `.blend`. It replaces the
old upper residential window boxes with closed rear elevations and deeper stock-brick piers, sill/lintel courses, varied
stepped roofs, uPVC-style frames, curtains/blinds, 20 private balconies, planters and drying rails.
The gallery front doors gain casings, mats, letter plates, handles and bells. The complete scene exports 6,773 editable render objects to 25 material meshes (17.79 MB GLB). Concrete panels
have physical ribs rather than a baked photograph.

The north-west ground-floor room is now **Flat 01**, about 12×6 m gross. Its existing courtyard
and lobby openings remain. The flat contains a kitchen with cabinets/sink/hob/fridge, a living
area with sofa/table, a separated bedroom with bed/wardrobe, radiators, plaster finishes and
closed windows. It is an initial home interior; bathroom, appliances/doors that operate,
interactions and final domestic texture detail remain unfinished.

The surrounding visual context adds six pitched-roof terraced houses, chimneys, garden walls,
a road edge/footway and two taller point blocks. These buildings and the private balconies
above the playable gallery are **visual surroundings, not accessible new routes**. The 36×30 m
combat bounds and single layered navigation system are retained. The accessible flat is an
actual navigable change within those bounds, with furniture and partition collision.

## Ownership, materials and export

- `07_HOMES / South London residential` is an editable child of the Blender render collection.
- Major flat furniture and the partition derive collision from `src/onsite/level.ts`; matching
  wire guides are kept in `02_COLLISION`. Render meshes never become a second physics/nav owner.
- Three.js rebuilds lighting. Two local interior lamps supplement the four courtyard pools.
  An original overcast sky dome replaces the rural HDRI background; the credited HDRI remains
  the reflection/lighting source.
- Stock brick uses the project's original generated `01-london-stock-brick-color.png`, encoded
  to WebP without painting/cropping. Provenance is in `public/materials/homes/provenance.json`.
  It uses constant roughness and geometric occlusion; it is not claimed to be a scanned PBR set.
- Plaster/fabric/wood colours are original materials with vertex variation. Detailed domestic
  fabric/wood normal maps are still future work. All existing licensed donor notices remain.

To rebuild just the residential pass, preserving the existing estate:

```sh
npm run evidence:layout
blender -b --python-exit-code 1 --python scripts/build_homes.py
npm run typecheck
npm test
npm run build
```

`npm run assets:estate` also includes this pass when rebuilding the whole estate from scripts.
Preserve manual edits before running either builder; only ordinary export preserves manual
residential changes when its stored revision matches. Blender commands now use
`--python-exit-code 1` so script exceptions cannot masquerade as a successful asset build.

With the dev server running, `node scripts/capture-homes.mjs` takes fixed inspection views;
`node scripts/capture-home-route.mjs` continuously walks the real WWB capsule through Flat 01
with bots disabled and no teleports after spawn. Main `npm run test:browser` checks normal
mouse/keyboard combat separately. See CURRENT-VALIDATION.md for the actual latest results.
