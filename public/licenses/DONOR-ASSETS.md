# ONSITE — selected IRONLINE art

These assets were copied from [IRONLINE](https://github.com/cktang88/3d-fps) at
`130ac2a5c856401ec36e7d35afcfefe40c5801f4`. Individual asset licences apply;
the package's ISC declaration is not used as an asset licence.
The machine-readable [provenance record](../models/donors/provenance.json) includes
source URLs, original author metadata checked 18 October 2026, exact donor paths,
SHA-256 hashes and changes. No Fab animation tracks, unlicensed mirror code,
Tripo/Manus assets or donor audio are included in this import.

## First-person model — CC BY 4.0

`models/donors/m4a1-hands.glb` combines:

- **M4A1** by **Firewarden3D / Firewarden**:
  <https://sketchfab.com/3d-models/40d8ef818c7549a896371cbb1f64fec6>
- **Fps arms** by **DJMaesen / bumstrum**:
  <https://sketchfab.com/3d-models/9452ce4cddde4110a4fd73e555a8e412>
- Arm rig / grip template from **FPS AK-74m animations** by **Cransh / ccransh**:
  <https://sketchfab.com/3d-models/94be8385c402474cacd39bc096c6ca14>.
  The original template credits AK-74M by creationwasteland and arms by DJMaesen;
  the template's AK mesh is not part of the imported M4.

Licence: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
IRONLINE's derivative re-poses/re-rigs/rescales and compresses the textures, removes markings
and bakes AO (per its README credits). ONSITE retains the derivative unchanged on disk,
tints the weapon, gloves and sleeves dark at runtime and adds original procedural reload reach.
The included `grip_vgrip` clip is a static grip pose; the Fab rifle animation JSON is excluded.
Credit for the combined FP rig preparation: the IRONLINE project / cktang88.

## Environment — CC0

[Poly Haven](https://polyhaven.com/license) models, simplified and WebP encoded by IRONLINE:

| Model | Original creator |
| --- | --- |
| Covered Car | MP |
| Rollershutter Door | MP |
| Metal Trash Can | GurJas Studios |
| Trashbag | Benny Weimer |
| Exterior Aircon Unit | Monsta3D |
| Concrete Road Barrier 02 | Amal Kumar |
| Street Lamp 01 | Josh Dean |
| Bambanani Sunset HDRI | Dimitrios Savva (photography), Jarod Guest (processing) |

Placed at metre scale in the Blender estate and in the runtime from the same placement manifest.
Original ONSITE estate architecture, vegetation, vertex-occlusion bake and assembly script
are separate from these donor meshes. Lights in the Blender review scene are not exported;
Three.js constructs its own lighting.
