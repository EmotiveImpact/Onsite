# ONSITE — whole-game goal

Owner direction, 19 October 2026. This is the goal for the entire project, not
just the next art pass. It supersedes narrower work prompts as the product brief;
the repository's preservation, provenance and review rules continue to apply.

## Goal prompt

Build ONSITE into a complete, replayable first-person shooter for the browser,
set on a fictional South London council estate. The player should choose a kit,
enter a convincing place, move and aim confidently, read threats and routes,
fight or flank through an encounter, secure the objective, and finish, retry or
change map without friction. Make the whole experience coherent: presentation,
movement, weapons, opponents, sound, menus, clothing, architecture and atmosphere.

Continue the existing Three.js / Rapier / WWB game. Improve and integrate its
working systems rather than rebuilding a parallel prototype. Keep one simulation,
one physics owner and layered navigation. Use Blender for original or individually
licensed assets, retain editable sources and metre scale, and separate rendering
from collision and navigation. Preserve Heron Court as a working compact encounter
and Heron Reach as the larger estate. Every import needs its own provenance;
repository size or a package licence is not blanket permission for bundled art.

The visual identity is the original ONSITE concept art: blue-hour air, warm windows
and practical lamps, wet paving, weathered stock brick and concrete, glazed stair
cores, a believable football cage, homes, shops, services, grass, winter trees,
rubbish and a layered London skyline. Build a place with signs of use, not a field
of unrelated props. Readable routes and convincing architectural junctions matter
as much as detail count. Keep the cream/amber/charcoal interface and ONSITE name.

Represent the established Black British character direction through original or
cleared character art. Keep the initial clothing range black: hoodies, balaclavas,
gloves, joggers and selectable trainers. Give hands, garments, weapons and bodies
believable proportions, contact, joints and animation. Kit choices must correspond
to actual visible assets and remain cosmetic unless a later design explicitly
introduces gameplay differences.

Make combat satisfying through reliable controls, aligned sights, readable recoil,
credible reloads, responsive impacts and clear audio. Opponents must perceive,
hear, pursue, use routes and cover, take damage and die consistently. Preserve
vertical navigation: overlapping floors, stair approaches, landings and galleries
must work for real actor capsules. Make opportunities to flank and approach quietly
understandable through level design and feedback; do not claim a stealth system
or invent AI capabilities that have not been implemented and tested.

Deliver the bots-first game before expanding into online matches. The longer-term
Heron Reach target is a tested 32-player map with an authoritative online service,
prediction, reconciliation and interpolation. Keep simulation boundaries suitable
for that phase, but do not build networking now. A 32-player design drawing is not
proof of 32-player performance, balance or implemented multiplayer.

Treat AAA as a reference for consistency and craft, not a label earned by cloning
projects or adding effects. Establish quality through matched runtime evidence,
playtesting and measured costs. Target responsive real-GPU play, efficient assets,
clear settings, accessible navigation and robust loading/recovery. Real-GPU testing
is deferred by the owner and must not stop useful implementation; leave hardware
claims explicitly unverified until measured. Retain the software-rendering fallback.

Work through the gaps autonomously, checkpoint before structural or generated-asset
changes, preserve previous art and tests, and make focused reviewable commits and
PRs. For each delivered change, run the relevant tests, typecheck, production build
and both maps' browser checks. Show actual before/after captures and retain failures
and their resolutions. Update the handoff so another session can continue. Do not
merge or deploy without separate instruction.

## What “complete” means

| Area | Acceptance gate |
| --- | --- |
| Player flow | Accurate title/map choice → actual kit/options → loading → pointer-locked play → pause/resume → clear victory/death/timeout results → retry or title. Keyboard focus and narrow screens remain usable. No dead controls or fake modes. |
| Settings and progress | Sensitivity, volume/sound, camera-effects preference and quality choice persist safely. Last/best local results describe completed runs accurately; corrupted or unavailable storage cannot stop the game. |
| Movement and world | Walk, sprint, crouch, jump, land and traverse the implemented multilevel routes without clipping or floor confusion. Existing doorways, capture volumes and cover stay consistent with collision. |
| Weapons | ADS aligns; fire cadence, spread, recoil, ammunition, reload timing and hit/damage feedback agree. Hands remain attached to grips/magazines; reloads return to the original pose. |
| Opponents | Actual perception, hearing, cover/chase, stairs, damage, defeat and reset work. Character joints and weapon presentation follow the simulated actor. Difficulty and fairness require human playtesting as well as automation. |
| Character kit | All options use real assets with original/cleared provenance; black clothing and the Black British direction remain consistent. The preview shows the saved operator, without implying online character replication exists. |
| Estate quality | Grounded props, coherent wet/dry response, local light/contact, depth haze, credible interiors, architecture and skyline. Reference viewpoints show material and spatial improvement without invented playable space. |
| Audio | Adjustable, legible weapon/impact/movement cues and spatial ambience with proper source rights. Pause/mute/resume work. A synthesised placeholder is not labelled a finished sound library. |
| Performance | Asset bytes, draw/triangle counts, texture allocation estimates and frame-time distributions are recorded. Eventual target: 60 FPS at 1080p on an agreed mid-range desktop GPU, with a useful lower quality profile. This is a target, not a current result. |
| Robustness | Loading/error states, repeated map changes, pause/restart/title cycles and browser errors are checked. No research clones or source PNG packs enter runtime accidentally. |
| Later online phase | Authoritative service, input validation, prediction/reconciliation, interpolation, reconnect/session handling and tested 32-player load/balance. Deferred until the local game and device budgets are demonstrated. |

## Work order and present state

**20 October continuation:** the initial whole-game tranche is reviewed in
[its implementation log](development/WHOLE-GAME-PROGRESS.md). The owner then
prioritised properly constructed stairs and asked what else prevents the quality
target. The active [public-stair pass](maps/heron-reach-32/art/STAIR-PASS-2026-10-20.md)
rebuilds all eight Heron Reach public cores around their existing physical routes.
It records the remaining reflection/shadow, character, sound, architecture,
playtesting and hardware gates. This does not declare those gates complete.

The baseline is `483cc0ae14a9e498b757fe15e1084a86829c27ec`, preserved as
`checkpoint/onsite-before-whole-game-2026-10-19`. It has a working WWB encounter,
layered physics/navigation, licensed rifle/hands and the first Heron Reach visual
passes. It does **not** meet every acceptance gate above. Prior evidence and
limitations are in [the scene-depth work log](maps/heron-reach-32/art/SCENE-DEPTH-2026-10-19.md).

1. Complete the player-facing loop, accurate map descriptions, saved options and
   honest local results. Keep existing start/retry controls and default encounters.
2. Replace the floating-piece opponent presentation with an original articulated
   Blender operator, black kit variants and an actual kit preview; preserve bot
   simulation and collision.
3. Improve weapon presentation within the existing Arsenal and align animation
   with its established timing. Validate actual imported rig poses.
4. Replace flat shop-depth imagery with authored stock and fittings in existing
   physical furniture footprints. Add subtle floor-aware contact grounding for
   props and feet, with measured geometry/render cost.
5. Integrate and verify the whole loop on both maps; record actual evidence,
   remaining defects and performance. This is the active implementation tranche.
6. Continue towards the remaining gates: better contact/local shadows and scene
   reflections, authored facade/interior variation, richer original character and
   animation work, spatial audio, human encounter/stealth playtests and hardware
   profiling. Avoid declaring those complete from a screenshot or unit test alone.
7. Begin the online phase only after its scope is explicitly activated. Current
   work preserves that possibility without importing a cloud backend or second engine.

The active tranche is tracked in [the whole-game implementation log](development/WHOLE-GAME-PROGRESS.md).
This document is the continuing goal; the log must distinguish shipped/review-ready,
tested, partial and deferred work. Finishing one tranche does not finish the entire game.
