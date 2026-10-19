# ONSITE: the next quality goal

Owner instruction, 19 October 2026: revisit the existing game and donor repositories, raise
detail and depth, and implement the next improvement rather than returning another plan.

## Working prompt

Continue the existing WWB / Three.js / Rapier game on Heron Reach. Make the Cage–Corner–gallery
stretch feel like one inhabited, weathered South London estate at blue-hour dusk. Use the
original concept art as the visual target. Improve what the player sees within 15 metres first:
coherent warm practical light, grounded materials, readable shop depth, functioning-looking
services, restrained signs and rubbish, and believable architectural junctions. Detail must
explain how the place is used; avoid filling clear routes with unrelated props.

Fix lighting and material defects before adding expensive effects. Stop nearby light pools
washing gallery floors white and lighting through storeys. Reduce noisy concrete/brick normals,
keep sheltered soffits dry, and give the exterior wet surfaces a controlled response. Maintain
cool daylight in the sky, warm windows and local lights, with depth haze rather than a uniformly
dark filter. Use original Blender geometry and appropriately licensed donor assets where they
provide a visible improvement. Keep editable sources and record provenance for every import.

Reinspect WWB and IRONLINE. Study other clearly licensed contemporary military FPS projects
for small compatible rendering and presentation systems, not another engine migration. Do not
copy proprietary Call of Duty content, assets of unclear origin, or the unlicensed Claudefare
mirror. Retain one simulation and one physics owner. Networking remains deferred.

Preserve collision, navigation, movement, weapons, bots, rounds and Heron Court. No new playable
storeys or walk-through furniture in this art pass. Architectural depth is visual; any future
layout expansion is a separate measured level-design task. Work on a review branch, with matched
runtime screenshots, source-asset costs, tests, typecheck, build and both full browser encounters.
Real-GPU benchmarking remains deferred; report software results honestly. Do not merge or deploy.

## This delivery

- Branch: `codex/heron-reach-scene-depth`, based on the complete visual stack at `45258da`.
- Recovery: `checkpoint/heron-reach-before-depth-2026-10-19` retains that starting point.
- First work item: a coherent lighting/material correction and additive Blender detail kit for
  the existing hero stretch, with matching gallery, shop and Cage views.
- Donor review: [NEXT-QUALITY-DONORS.md](../research/NEXT-QUALITY-DONORS.md).

## Quality gates

1. The gallery keeps visible floor texture and subdued soffits; shop signs remain legible.
2. New details sit on existing surfaces/furniture, keep doors clear and do not invent collision.
3. Shop depth is visible in actual runtime views; package colour does not become visual noise.
4. Added geometry targets under 35,000 triangles and 12 material batches; no new light per prop.
5. All existing automated checks pass, both maps complete their encounters, and actual before/
   after captures include costs and limitations. Passing checks does not establish visual parity.

## What a larger production would still need

AAA is a quality ambition, not a feature or a credible claim for this prototype. Beyond this pass,
the major gaps are photographed/scanned material quality and authored variation; consistent
contact shadows and scene reflections within a measured GPU budget; bespoke Black British
character/hand models, rigging and animation; authored recoil/reload/audio polish; richer interior
set dressing; encounter and stealth playtesting; spatial audio; accessibility; streaming/LOD and
device profiling. Prioritise those by visible impact and measurements rather than the size of a
donor repository. The 32-player map design does not establish online multiplayer readiness.
