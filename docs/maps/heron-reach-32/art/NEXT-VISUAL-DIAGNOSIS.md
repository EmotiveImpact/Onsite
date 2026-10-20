# Cage–Corner–gallery visual diagnosis

19 October 2026. This review uses the final seven-item art-pass evidence, before the next hero
stretch changes. Its source baseline is the code described by
[ART-PUSH-2026-10-19.md](ART-PUSH-2026-10-19.md). The findings below describe that baseline even
when the accompanying implementation subsequently corrects them.

Reviewed the three [native DPR 1 stills](evidence/textures/detail/report.json), their
[DPR 0.5 counterparts](evidence/textures/after/report.json), the original
[ONSITE concept](../../../concepts/onsite-london-fps.png), and concept screens 05, 09 and 10.
Both runtime sets use SwiftShader with its reduced light pool, no sun shadows and no bloom.
These are inspection fixtures, not gameplay or real-GPU measurements. Real-GPU benchmarking
remains deferred by the owner and is not a condition for this work.

## What the pictures actually show

The native images expose the same composition and material problems as the half-resolution
images. Resolution explains softened wire and small text, but does not explain the bright gallery
floor, dark shop bays or matte-looking court. The concept's strongest transferable qualities are
warm practical lighting repeated along a route, dark damp surfaces separated by irregular
reflections, and readable shop depth. Adding more scattered props would not fix those qualities.

| View | Observed baseline | Useful next outcome |
| --- | --- | --- |
| Cage | Broad dark ground with grain, a few small bright streaks, readable green frame; towers form a line of repetitive grey boxes. | Broken warm reflections that lead towards the objective, readable wet/dry regions, a restrained skyline behind the lit court. |
| Corner | Bright lamp over the middle of the words; small image-backed stock panels surrounded by large empty dark bays; central shelving presents a plain back to the viewer. | Legible fascia, a broad warm ceiling, front-facing stock layers and a visible warm threshold. |
| Gallery | Near-white floor and coping under a dark soffit with fine gold stippling; brick mortar/detail competes with the scene. | Damp grey floor with warm pools, quiet rough concrete, locally readable doors and gallery depth. |

For reproducible image checks, coordinates below are pixel rectangles in the 1280 × 720 native
stills, `(left, top, right, bottom)`. Display luma uses `0.2126 R + 0.7152 G + 0.0722 B` on the
saved 8-bit image; it is not scene luminance or an HDR lighting measurement.

- Gallery floor `(450, 540, 580, 610)`: mean 230.1/255, 95th percentile 244.5. The floor is
  visually near-white, although this rectangle is not strictly clipped in all RGB channels.
- Gallery soffit `(250, 30, 500, 100)`: mean 39.3, 95th percentile 105.5. The wide distribution
  corresponds to visible fine bright speckling against the dark ceiling.
- Corner sign/lamp `(450, 208, 600, 282)`: 20.8% of pixels have every RGB channel at least 240.
  This includes intended white lettering, so compare lettering readability as well as the number.
- Empty left shop bay `(201, 324, 289, 424)`: mean 45.1, 95th percentile 51.2; little internal
  contrast survives in a large shopfront region.

## 1. Fix which lights receive the small pool

The baseline `HeronReachAtmosphere.update` in `src/onsite/heronReachArt.ts` ranks anchors by
weighted distance. It does not consider storey or walls. The four software point lights have no
shadows. The ten hardware point lights are also unshadowed: enabling renderer shadows alone
does not make a PointLight cast them. Court fixtures use intensity 850 and range 42 m; street
fixtures 175/25 m; shop fixtures 55/12 m; cores and ceiling fixtures 11/9 m.

Reproducing the baseline sort at the saved cameras gives:

| Camera, renderer coordinates | Baseline four chosen fixtures |
| --- | --- |
| Cage `(-20, 1.7, 0)` | B1 ceiling, B1 wall, north-west court, south-west court. |
| Corner `(38, 1.7, -17)` | Front door wall, street, core, left shop strip. The right strip ranks sixth. |
| Gallery `(-20, 4.7, -22.9)` | North-west court, +3 core, ground core, street. |

This explains why increasing every light is the wrong first adjustment: the Cage spends half
its pool beneath the ground, the shop loses one of its two practicals, and the gallery receives
an unshadowed floodlight plus lamps from other storeys.

There is also a separate receiver bug. After the runtime changes court heads to 6.35 m,
`surfaceBelow` assigns both southern court streaks to an overlapping +6 m deck. The two north
court streaks remain at ground. A lamp's supporting street floor is semantic information; it
cannot always be inferred from the highest surface beneath its elevated head.

The new pure helper `src/onsite/heronLightSelection.ts` implements:

- Cached receiver identity, with court/street/shop at ground, core fixtures at their authored
  landing, explicit `floorY` overrides and supporting-floor lookup for other lamps.
- A same-storey pool using existing floor solids, followed by segment/AABB visibility through
  the physical geometry. Glass and porous Cage fences transmit light.
- A small tolerance for the initial exit from a fixture's mounting wall. Intervening walls and
  structural slabs are never waived by this tolerance.
- A perceptual contribution score using square-root intensity and range attenuation, so distant
  floodlights do not monopolise a nearby shop view. Sorting and visibility run on the existing
  quarter-second lighting tick; bounds and receiver lookups are cached at construction.

Six tests in `tests/heron-light-selection.test.ts` passed with
`npx tsx --test tests/heron-light-selection.test.ts`. They cover the actual saved viewpoints,
the +6 court receiver problem, transparent/porous surfaces, parallel segment intersections,
mounting-wall tolerance and blocking slabs. The Corner retains both shop strips; the gallery
retains a visible wall lamp on its own storey, and the Cage spends no slots in B1.

Integration: prepare lights from all anchors and existing floor solids, prepare occluders from
all existing solids, and call `selectReceiverLights` in the lighting tick. Returned positions
already include the current 0.35 m downward offset. Reuse `lightReceiverFloor` for streak planes.
No collider or navigation data is changed by these helpers.

Limit: this selection test is not per-pixel shadowing. A selected unshadowed light can still
shine through another wall elsewhere in the frame. Ray visibility to the camera is also a
conservative approximation: it may reject a hidden fixture whose light would spill through an
opening onto a visible surface. For this pass, explicit local practicals, shelter response and
contact occlusion have more predictable cost than adding shadowed point lights to every lamp.

## 2. Quiet the hard surfaces before adding detail

The gallery's floor is `hr_concrete_cast`; its soffit is `hr_concrete_board`.
`scripts/maps/art/heron_art_arch.py::slabs` assigns ordinary +3/+6 slab tops cast concrete and
their undersides board concrete. GLB inspection at the saved gallery camera confirmed upward
floor and downward soffit normals, metre-scaled UVs and plausible vertex colours. The cast
concrete colour texture averages RGB 123/122/119; its 95th-percentile values are 148/147/145.
The source is not a white texture. Do not hide the lighting defect by globally blackening it.

`HeronReachMaterials.get` currently sets every architecture normal scale to 0.8. The procedural
brick normal starts from 7 mm relief; board concrete from 3.5 mm relief, with high-frequency
detail. Under close, strong point lights this produces competitive fine highlights. The runtime
also overwrites material roughness with `wet ?? 1` when an ORM map finishes loading. For cast
concrete, the mean green ORM value 221.6/255 is multiplied by `wet: 0.8`, giving roughly 0.695;
the material also gets environment intensity 1.6. This is a response choice, not missing PBR.

Practical first settings to A/B, rather than claims of final calibration:

- Add per-material normal strength. Try cast/board concrete 0.20–0.35, stock/red brick
  0.35–0.50; keep tile joints and authored metal detail separate.
- Keep dry concrete/soffit roughness around 0.80–0.95 and use neutral dielectric metalness.
  Expose an explicit ORM roughness multiplier so a legacy `wet` value cannot silently control
  every surface of that material. The current lossy ORM WebPs contain a small non-zero blue
  channel even for non-metals; enforce metalness zero for known masonry/concrete materials.
- Restrict wet response to upward exposed ground/gallery faces. `wetGroundNames` currently
  includes asphalt, paving, red pavers and court, but excludes the gallery cast concrete.
  Do not simply wet every cast-concrete wall, sill and soffit.
- Add broad base dampness, wall-floor contact and roof shelter before more high-frequency grime.
  Existing AO is texture cavity AO, not geometric contact shadow. The global hemisphere fill
  (1.8) and smooth environment fill do not distinguish open sky from a covered gallery.

Hold exposure at its existing baseline for the first local comparison. Lowering exposure alone
would darken the already weak court and shop while leaving the allocation error intact.

## 3. Make wetness reflect a recognisable lighting structure

`src/onsite/wetGround.ts` already has a real roughness/normal wetness mask: approximately 23% of
its texels are above the 0.72 full-pool threshold, roughness can reach 0.075, and wet normals blend
84% towards the unperturbed surface normal. The missing wet look is not solved solely by lowering
roughness further. The PMREM in `heronReachArt.ts` contains only the smooth graded sky. It cannot
show tower, fence or lamp geometry. Local streaks are additive image planes, not scene reflections.

For the next stretch, retain this honest inexpensive approach and make the lamp structure
coherent: correct receiver floors, confine streaks to upward local wet surfaces, and break their
length with the same world-space wetness mask. Use quieter broad wet areas separated by dry
aggregate; inspect actual camera motion for swimming or obvious camera-facing patches. Keep
the darkest ground in a readable blue-grey range and let local reflections carry the warm values.
Avoid a blanket bright amber wash across all paving.

An optional local planar reflection could later produce recognisable silhouettes on the Cage
floor, but it entails another scene render, clipping and transparent-surface rules. It is not
necessary to unblock the current material/lighting correction, and no unmeasured performance
benefit is claimed for it.

## 4. Turn the shop into one warm volume

`src/onsite/heronShopArt.ts` correctly makes the reused image cards emissive. The
`build_heron_shop_detail.py` cards only occupy the rear wall on either side of a 2.1 m rear-door
gap. Existing physical shelves stand in front. That creates local patches of stock but leaves
the large sidewalls, front ceiling and parts of the floor comparatively empty. The two new
shop point lights compete with unrelated anchors in the old pool.

The sign conflict is geometric: `heronReachDressing.ts` places a wall lamp over every exterior
door, then centres the Corner fascia over the same door. The lamp sits directly over the
lettering. The fascia letters additionally emit at 1.3. Moving or masking that render-only
wall fixture for the Corner, with a corresponding relocated light anchor, is more reliable than
another global bloom-threshold change. Software screenshots have no bloom already.

Use the two front practicals to illuminate the ceiling and threshold, add restrained warm
emission to the ceiling strip/bounce surfaces, and face stock towards the glass. Preserve rear
exit and aisle clearance. Shelf orientation and the plain panel currently facing the front
should be checked against the existing shelf asset before changing placement. Add wall-bound
stock or shallow display detail within existing footprints; avoid new generic obstacles.

First review targets: the entire fascia is readable; both front bays show warm depth rather
than isolated bright cards; the doorway remains visibly traversable; the floor retains tile
variation under the warm spill. A photograph card will still flatten at oblique angles, so this
does not establish complete three-dimensional shop fidelity.

## 5. Quiet the repeated skyline after the hero surfaces work

`heron_art_context.py::towers` gives 26 distant towers only two elevation images, repeated in
17 m horizontal bays. All four faces of each tower use the same chosen image; the UV variation
is only an offset of 0 or 0.5. Both runtime elevation materials use emissive intensity 1.8.
The eight newer near towers have modelled balcony slabs and ribs, but their facade window
helper still places flat cards. Its `frame` argument currently does not create frames.

Keep the silhouette ring, but reduce distant emission first (A/B roughly 0.4–0.8 rather than
1.8), then vary coherent apartment/window groups and colour per building. In the Cage hero
view, give only the nearest one or two visible towers deeper jambs/sills and a distinct balcony
rhythm. This is a better use of geometry than extending detailed towers around the entire map.
Keep the established fog depth layering; increasing fog alone would hide the repeated pattern
while flattening the new near architecture.

## Review order and limits

Compare matched DPR 1 gallery, Corner and Cage captures after light assignment, then material
response, then shop/route detail. Also retain a DPR 0.5 pass for the actual software fallback.
Reject a change that makes the gallery less white by making the Corner unreadable. Use moving
inspection views to detect reflection swimming and pool transitions, and run the existing
navigation/encounter checks after runtime integration. The pure light tests prove selection
logic, not the appearance of the integrated scene.

The planned work remains render-only and preserves the existing 2,417 physical solids. No
browser was launched for this diagnosis, no physics/nav source was edited, and no build or
real-GPU performance claim follows from the image analysis or the six new tests.
