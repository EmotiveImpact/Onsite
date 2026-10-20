# The Corner: lived detail kit

19 October 2026. This additive Blender kit gives The Corner a deeper, weathered shopfront,
legible small notices and practical service fittings. Its initial interior additions have moved
to the [dimensional shop kit](SHOP-DEPTH.md). It follows the
existing native close view in `evidence/textures/detail/the-corner.png` and the original
`docs/concepts/screens/05-corner-shop.png`. The concept is a visual reference; no pixels were
copied from it. Runtime screenshots and gameplay verification belong to the combined quality pass.

The source is `assets/blender/heron-reach/lived-detail.blend`, generated in Blender 4.3.2.
The original Blender 5.2 sources are untouched. All geometry is accumulated through
`heron_art_mesh.Builder` in metre map coordinates. Exported glTF already uses world
`x = mapX − 72`, `y = mapY`, `z = mapZ − 60`; the loader must not add another offset.

The kit adds 2,242 triangles in five material batches. The compressed GLB is **110,100 bytes**;
the raw export is 285,432 bytes. No lights, animation, collision or navigation data are added.
The sole embedded 1024² opaque WebP is 78,676 bytes (approximately 5.33 MiB decoded RGBA8
including a full mip chain). The authoritative hashes and compression version are in
`assets/blender/heron-reach/lived-detail-manifest.json`.

| Material | Loader treatment |
| --- | --- |
| `hr_steel_black` | Reuse `HeronReachMaterials.get(name)` |
| `hr_steel_aged` | Reuse `HeronReachMaterials.get(name)` |
| `hr_steel_galv` | Reuse `HeronReachMaterials.get(name)` |
| `hr_rubber` | Reuse `HeronReachMaterials.get(name)` |
| `hr_lived_atlas` | Preserve the embedded material and its shared colour/emissive image |

The atlas material is opaque and single-sided, with roughness 0.78, metalness 0 and a restrained
0.08 emissive factor. It does not cast light. Every mesh exports `COLOR_0`; muted scuff and trim
tints multiply the shared surfaces. The five nodes are named `lived/corner-and-service / <material>`.
Nodes and material names survive `gltfpack`. These small details can receive shadows; they do not
need to cast them.

| Addition | Attachment and clearance evidence, in metre map coordinates |
| --- | --- |
| Shutter housings and glazing beads | Fixed to existing north wall/window frames. Window housings occupy y=2.205–2.41; the separate door head begins y=2.405, above the existing 2.4 m opening. Jamb guides remain outside x=110–112. There is no lowered shutter. |
| Printed window notices | Mounted on existing closed glazing at z=48.06–48.08. They cover under 10% of the two 6.9×1.6 m glazed bays. No notice crosses the doorway. |
| Open-leaf pushbar | Attached to the existing door leaf at x=110.06–110.105, z=48.22–50.10. The thin bar reaches x=110.130 and does not cross the clear route beyond x=110.14. |
| Front conduit and rainwater pipe | Cable hugs the solid jamb at x=112.26. The 90 mm pipe sits on the north-east brick pier at x=119.72, z=47.94. |
| Drain grates | At (x,z)=(119.72,47.61), (105.02,47.52), and (117.56,57.34). Their top surfaces are y=0.005 over the existing y=0 ground. No raised kerb or new obstacle. |
| Rear ventilation and electrical detail | Mounted to existing solid rear masonry, east of x=113.60. Maximum projection is 12 cm. The rear opening remains x=110.25–111.75. |

The builder checks each generated polygon against three protected route volumes before saving:
the front route x=110.14–111.86, the complete 2 m centre aisle x=110–112, and the 1.38 m rear
frame clearance x=110.31–111.69. The existing front/rear portal widths and every existing
collider are unchanged. These geometric checks supplement the parent pass's actual browser
route checks; they are not gameplay evidence.

The earlier shelfback notices, top stock and photo-card mounting rails are retired from this
kit. The dimensional shop pass replaces all four shelf render instances inside their existing
collision footprints and removes the old photographic interior cards. The old result remains
in the preceding checkpoint; this kit now supplies exterior and service-surface detail only.

Rebuild from the repository root:

```sh
python3 scripts/maps/art/make_heron_lived_texture.py
blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_lived_detail.py
```

The Blender builder exports the raw GLB and then invokes the repository's locked npm gltfpack
0.22.0 with `-cc -kn -km -kv -vtf`, writing the compressed GLB and final cost/hash manifest.
It asserts the expected shop layout, four shelf placements, clear route volumes, triangle budget
and material count. It never opens or rewrites another Blender source.

All geometry and print artwork are original procedural ONSITE work. The atlas uses fictional
package names, original simple food illustrations and the existing system Open Sans font under
Apache-2.0. The generator is `scripts/maps/art/make_heron_lived_texture.py`; the source PNG is
retained in `assets/textures/heron/lived/`. Runtime WebP, atlas metadata, licence notice and hash
provenance are in `public/materials/heron/lived/`. No downloaded donor asset or concept-art pixels
enter this kit.
