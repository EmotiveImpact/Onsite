# Courtyard dressing pass — 18 October 2026

Baseline: local commit `e768260`. The prior Blender estate, concepts, original textures and donor files remain recoverable in Git. This pass addresses the clean/repetitive floor, absent rubbish/grass, exposed sleeve ends and flat warm presentation reported by the user.

## Sources and actual use

- Existing WWB gameplay and single Rapier/layered-navigation ownership are unchanged.
- IRONLINE's existing licensed M4/hands remain the active model. The previous camera offset pushed the entire rig too far forward and exposed the cut-off upper sleeves. ONSITE adapts the authored bore-anchor framing with a lower, smaller weapon view and five-degree hip cant; ADS retains its independent alignment. The open sleeve boundaries are also extended in an editable Blender derivative, preserving the authored hands and grip. Cloth is matte, dark and nonmetallic; the old roughness map no longer makes the sleeves look wet/plastic.
- Five additional individually checked Poly Haven models are copied from the pinned IRONLINE clone: cardboard box, old tyre, cement bag, rusted wheel rim and wooden crate. Their original API author metadata, hashes and paths are appended to `public/models/donors/provenance.json`. Existing trash bags are reused for small clusters. No wholesale donor tree or unlicensed mirror content is shipped.
- ambientCG Ground110 and Leaking003 colour/normal/roughness textures come from the same pinned donor, with CC0 confirmed at the original publisher's licence page. Exact hashes and URLs: `public/materials/detail/provenance.json`.
- An original generated asphalt colour texture is preserved under `assets/textures/onsite-dirt-pass`, with prompt summary, source/runtime hashes and encoding recorded. Runtime WebP is about 740 kB. It combines with the existing CC0 asphalt micro-normal/ARM; this is an approximate hybrid material, not a matched scanned PBR set. Opposite-edge differences are slightly higher than adjacent-pixel variation; seamlessness is not asserted solely from the generation prompt.

## Blender assembly

`scripts/dress_estate.py` authors an editable child collection, `06_DETAIL / grass litter weather`, in the estate `.blend`. It creates tapered curved grass blades, varied dried tips, grime patches with feathered vertex alpha, 600 individual chipped paving slabs, folded litter, crushed drinks cans, individual fallen leaves, damp-wall overlays, prop-contact dirt and faded maintenance paint. Separate donor objects remain in collection 04.

The export batches details by material, retains vertex tints/fade alpha and applies the existing occlusion bake. Render detail does not become nav geometry. Small soft litter is decorative. No collision layout is changed in this pass; routes are kept open and tall cover remains the existing physical geometry.

The Three.js scene rebuilds lighting with cooler sky fill and four warm local pools, replacing the prior hardware path's 24 point lights. This is presentation work, not a claim of real-GPU performance.

## Reproduction

```sh
python scripts/import-estate-detail.py
npm run assets:estate
npm run typecheck
npm test
npm run build
```

The generated source is retained in the repository and does not require regenerating an image on rebuild. `scripts/prepare_estate_materials.py` packs the generated asphalt into the editable Blender preview as well as binding it in Three.js.

With `npm run dev` running, `node scripts/capture-detail.mjs` saves actual runtime courtyard, rubbish, gallery and stair inspection stills, plus frozen reload phases. Those fixed views have bots disabled and are explicitly labelled; separate production-preview browser input verifies gameplay.

## Rebuild the Blender-finished rifle

Original donor files remain unchanged. The finishing input is decoded with isolated, pinned tools;
these tools are not production dependencies. The first export exposed an image-packing problem,
which was caught in the browser; explicit PNG transcoding and preserving already-packed images
fixed it. Asset checks now require both base-colour and normal maps, not just a valid GLB.

```sh
npm install --prefix /tmp/onsite-asset-tools --no-audit --no-fund @gltf-transform/core@4.2.1 @gltf-transform/extensions@4.2.1 @gltf-transform/functions@4.2.1 meshoptimizer@0.25.0
node scripts/unpack-carbine.mjs
python scripts/convert-rifle-images.py
blender -b --python scripts/finish-carbine.py
python scripts/compress-carbine.py
```

The runtime derivative is approximately 3.55 MB; normal/ARM maps use WebP quality 94 and colour
uses quality 90. The Blender source preserves packed PNG maps. Hardware rendering enables MSAA;
software mode retains its lower pixel ratio. Real-GPU verification is still outstanding.
