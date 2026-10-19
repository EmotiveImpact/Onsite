# Heron Reach: scene depth and lived detail

19 October 2026. This is the next review item after the seven-part visual stack,
on `codex/heron-reach-scene-depth`, based on `codex/heron-reach-textures-dressing`.
The [working goal](../../../development/NEXT-QUALITY-GOAL.md) is to improve the
Cage–Corner–gallery stretch as one inhabited South London estate. This is an art
and lighting pass on the existing playable, not a new level or multiplayer system.

## What changed

- **Lighting now selects the correct storey and visible fixtures.** The old Cage
  selection spent two of four software light slots on basement fittings; the
  gallery admitted court and other-storey lights, washing out the floor. Selection
  now uses supporting surfaces, explicit court/strip receivers and structural
  segment occlusion. The Corner retains both shop lights. The sign lamp moves to
  the left pier, clearing the lettering. Two subtle gallery strips stay within the
  existing fixed light pool. This is selection visibility, not per-pixel shadows:
  selected unshadowed lights can still leak behind nearby objects.
- **Material response is calmer and more directional.** Concrete, brick and paving
  use appropriate normal strength, with fine detail fading over 7–35 m. Sheltered
  soffits stay rough and dry. Only upward concrete receives the exterior wetness
  response. Non-metal ORM materials retain zero metalness. Lamp reflection streaks
  fade near the camera and at grazing angles; exterior ground receivers stay at
  ground level beneath overlapping decks.
- **Height-aware haze adds depth.** A small MIT adaptation from Operation Blackout
  integrates height and distance fog, with restrained blue-hour directional colour.
  It is scoped to Reach's stock fogged materials and composes with the existing
  surface/wetness hooks. It does not replace global Three.js shader chunks or affect
  the first-person weapon scene. Near 10 m haze is approximately 1.25% standing on
  the street and 1.91% on the checked crouched basement ray; 150 m haze is 47.57%.
- **Original Blender shop and service details:** shutter housings, glazing trim,
  notices, shelf-end prices, small packages, drain grates, conduit, ventilation and
  a door pushbar. Existing furniture and wall footprints contain the new geometry;
  the front door, centre aisle and rear route remain clear. An integrated close
  view exposed coplanar shelf notices; the final export separates them by 5 mm.
- **Actual scanned donor art:** two Poly Haven manhole covers and four selected
  fluorescent fittings, adapted from individually cleared IRONLINE derivatives in
  Blender. Two are inside The Corner; two sit under the upper gallery soffit with
  2.775 m head clearance. Original Corner fittings are hidden only after the new
  kit loads. A regression test parses the real compressed shop GLB and checks
  Three.js's sanitised names via preserved `userData.name`.
- **Cleaner gallery netting:** an original periodic cord texture replaces repeated
  feather silhouettes. The earlier generated artwork and Blender sources remain.

## Donor mapping and asset costs

WWB remains the actual movement, weapon, combat, bot and round foundation. Those
modules are unchanged. IRONLINE supplies individually licensed art, not a second
engine. Operation Blackout supplies the small fog adaptation with its full MIT
notice. Claude of Duty is a newly pinned MIT study reference for later reflections,
contact shadows and warm-up; no code or assets from it ship in this pass. The
unlicensed Open Claudefare mirror remains reference-only.

Read the [source review](../../../research/NEXT-QUALITY-DONORS.md),
[fog provenance](../../../research/OPERATION-BLACKOUT-NOTICE.md),
[original detail kit](LIVED-DETAIL.md) and
[individual scan notices](../../../../public/licenses/polyhaven-scanned-notice.md).
Both new research clones are ignored; no nested repository is tracked or bundled.

| New runtime asset | Bytes | Geometry / materials |
| --- | ---: | --- |
| `heron-reach-lived.glb` | 121,404 | 3,404 triangles, 5 batches, original embedded 1024² atlas |
| `heron-reach-scanned.glb` | 499,580 | 2,484 triangles, 3 materials, 7 preserved embedded maps |
| `pigeon-net-clean.webp` | 842 | Reuses existing gallery geometry |
| **Total added runtime payload** | **621,826** | **5,888 triangles; 8 material batches across the new kits** |

The lived atlas is 78,676 bytes, already included in its GLB; its separate public
copy is not additionally fetched by the loader. Source PNGs, original donor GLBs
and editable `.blend` files stay outside the runtime directory. There is no new
light per prop and no second render of the scene. GPU texture allocation has not
been measured. Embedded scan/atlas images still use WebP rather than KTX2.

## Recovery and reproduction

`checkpoint/heron-reach-before-depth-2026-10-19` preserves starting commit
`45258da7479177a439376ac808775e8958ebd29f`. Commit or stash ongoing work before
switching to that checkpoint; return to the feature branch to continue. Original
art, generated images and Blender 5.2 sources remain intact. New sources use the
available Blender 4.3.2 CLI in metre scale and export render geometry only.

Rebuild commands and source/output hashes are in the kit documents and manifests.
Do not run a whole-scene generator over manual Blender work without a checkpoint.

```sh
npm ci
npm run dev
# Open /?map=heron-reach. Plain / is Heron Court.
npm test
npm run typecheck
npm run build
npm run preview -- --port 4173
# In another terminal, sequentially:
ONSITE_URL=http://127.0.0.1:4173 node scripts/maps/verify-heron-reach.mjs
ONSITE_URL=http://127.0.0.1:4173 npm run test:browser
```

Final evidence and measured results are recorded below after the frozen-build run.

## Remaining quality gaps

This does not establish AAA quality. Physical contact shadows and reflections of
scene objects are still missing; current wetness uses the environment and lamp
streaks. Shop rear imagery still reads as flat panels from some angles. Repeated
facade modules, domestic interiors, bespoke characters and animation, spatial
audio, stealth behaviour and encounter balance need dedicated work. Real-GPU
frame time, bloom, shadows, texture allocation and thin-alpha stability remain
unverified. The software fallback is slow and is not a performance target achieved.

The next highest-value rendering experiment is bounded local/contact shadowing
at the saved Corner/gallery viewpoints, followed by optional ground reflections
with measured GPU costs. Donor SSR requires depth, normals, velocity/history and
material integration; copying it wholesale would not be a safe drop-in upgrade.
