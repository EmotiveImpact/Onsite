# Heron Reach — constructed public stairs

20 October 2026. Continuing the [whole-game goal](../../../ONSITE-GOAL.md).
Branch: `codex/heron-reach-stair-construction`, based on the complete player-flow
review tip `5d381091d3fad2a42a648923cce62c390a350b38` (PR #17).
Local recovery ref: `checkpoint/onsite-before-stair-construction-2026-10-20`.
Do not reset the working checkout over later work. Original Blender files,
architecture GLB, private stairs, reference art and tests are retained.

## Problem and implementation

The public-core railing generator reused the same rising rail direction on both
flights, then repeated it every half-storey regardless of the actual mirrored
flight. It produced crossed, floating and excessive rails. Treads were separate
slab boxes, the first tread of each flight lacked the other steps' finish, and
the return flight lost its local light behind the central separator.

This pass replaces the public-core render assembly around the existing physical
steps. The additive Blender source contains coherent flight bodies, tread edges,
nosings, connected rails and supported fixings, with metre-scale material mapping.
The [construction and provenance record](STAIR-CONSTRUCTION.md) owns source and
export details. No new texture library or third-party model is imported.

The existing central dividers are full-height, opaque steel colliders: they block
players, bullets, sight and light. New opaque slim well panels make that contract
visible; the handrails follow the real flight direction. They are not presented
as open, shoot-through guardrails. Existing windows remain exterior art backed by
solid walls. A genuinely open glazed stair core would need a separate, deliberate
visibility/collision design change; this pass does not fake it with transparent walls.

At load time, `heronStairArt.ts` removes only the original public tread/rail triangle
indices after the new asset and materials load. The original source GLB remains
unchanged. The exact old asset retires 35,072 triangles: 5,184 tread triangles and
29,888 rail triangles in 32 material meshes. Its 984 m combined skyline bounds
produce about 15 mm quantisation steps, so the tested retirement tolerance is 8 mm.
Walls, glazing, landings and private-home stairs are preserved. If the additive
asset fails to load, the original stairs remain visible.

Sheltered new concrete reuses the existing maps with a dry material, without the
outdoor wet-ground shader. The 32 full-landing fittings remain; 24 new half-landing
fittings illuminate the return flights. Half-landings explicitly belong to the
lower storey for light selection. The existing pool stays at four software or ten
hardware lights; no new shadow system or physics owner is introduced. Stair strips
use warm-neutral light and their modelled lenses, without outdoor amber glow sprites
or wet-pavement reflection cards.

## Validation and evidence

Implementation is in progress. Final geometry costs, test/build results, matched
runtime captures and both input-driven encounters will be recorded here before review.
All cloud captures are Chromium/ANGLE SwiftShader software rendering. Real-GPU
benchmarking remains deferred and unverified; passing a browser check is not evidence
of smooth performance or completed AAA quality.

## What still separates ONSITE from the quality target

| Gap | Evidence in the current implementation | Next production work |
| --- | --- | --- |
| Reflections and local shadows | Environment reflection contains the graded sky; lamp cards approximate streaks. Point lights have no shadow maps; contact patches are proxies. | A bounded, quality-controlled scene reflection path and local shadow strategy, with a measured hardware budget. |
| Character motion | The original 20-bone operator uses analytic poses; no authored locomotion clips, foot planting or cloth. | Better sculpt/weights and authored movement, aim/reload transitions, ground contact and silhouette review. |
| Sound | Cues still use short synthesised fallback buffers; no finished sourced estate ambience. | Recorded/cleared material-specific steps, impacts, weapons and spatial estate ambience with a coherent mix. |
| Architecture and interiors | Repeated facade/room treatments, opaque window cards and private stairs remain. | Better construction joins, home variation, meaningful room detail and clear visibility contracts. |
| Combat and readability | Automated normal-input encounters prove function, not human fairness or enjoyable pacing. | Human tests of approach routes, cover, spawn pressure, threat/audio readability and objective flow. |
| Performance | Software captures run around 1–2 FPS; no real-GPU benchmark. Large JS and texture costs remain. | Hardware measurements, device budgets, culling/LOD and measured texture/render optimisation. |

More clones or detail counts do not close these gates by themselves. Keep using the
working WWB systems and individually cleared assets; preserve the London blue-hour
direction and improve each part with actual runtime evidence. Networking stays deferred.
