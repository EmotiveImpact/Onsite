# Runtime evidence

These are actual browser renders, not generated concepts.

| Evidence | Context |
|---|---|
| first-person.png, aiming.png, combat.png, victory.png | Production preview, normal mouse/keyboard automation |
| combat-input.webm | Input-driven combat recording, including the real cloud frame pacing |
| report.json | Interaction checks, console/request failures and frame-time sample |
| courtyard.png, stairs.png, upper-route.png, stair-b.png, return.png | Continuous physical traversal of the Blender level, bots disabled, labelled in HUD |
| route-report.json | Actual physical positions reached and route-render measurements |
| courtyard-weapon.png | Actual Three.js presentation fixture, idle weapon, bots disabled; pixel ratio 1 and sun shadows for visual inspection |
| stair-detail.png | Same runtime at a fixed stair A inspection position, bots disabled; separate from the physical traversal proof |
| reload-35.png, reload-55.png, reload-85.png, presentation-report.json | Same renderer with the real reload clock frozen at labelled phases, half pixel ratio; hand/magazine reach checks |
| observed-death.png, observed-death.json | Earlier failed full-round attempt: two bots down, player killed; retained as death-screen evidence, not a passing test |
| as-built.svg, layout.json | Generated from collision solids and spawns, including measured donor obstacles |

The original Blender visual pass supersedes the screenshots in checkpoint `d5faf61`. The concept artwork in
`docs/concepts` remains a visual target, not runtime evidence. See [current validation](../CURRENT-VALIDATION.md)
for actual results and rendering limitations.

The physical route screenshots were captured before the final foliage detail and reload-pose
adjustments. Their collision/layout is unchanged. Those root-level combat and presentation captures show
the previous art pass at e768260, not the subsequent dirt/rubbish pass. Frozen poses and scripted routes are labelled in the HUD and are not
presented as human gameplay or concept images.

## Dirt/rubbish and sleeve pass at 0ce5a14

`dirt-pass/` contains captures of the preceding pass. `court.png`, `rubbish.png`, `gallery.png` and
`stair.png` use the actual game renderer at fixed inspection cameras, bots disabled,
1280×800 at pixel ratio 1 with sun shadows. `reload-*.png` freeze the real reload clock.
`report.json` records finite poses and the extracted magazine/hand reach checks.
These stills are visual inspections, not a performance sample or input-driven gameplay.
`dirt-before.png` is the unmodified courtyard capture from baseline e768260 for comparison.

The collision layout remains unchanged (see the current GLB manifest's layout SHA).
The continuous physical browser route evidence above belongs to the earlier visual pass;
actual-brain bot and player stair/collision regressions were rerun for the current pass.

`dirt-pass/first-person.png`, `aiming.png`, `combat.png`, `victory.png`, `combat-input.webm` and
`combat-report.json` are the new production-preview input-driven run. Three bots down, victory,
76 health; software mean 461.57 ms over 141 frames. These use the lower-resolution software
configuration and are distinct from the fixed high-resolution inspection stills.

## South London residential expansion

`homes/` is the current pass. `homes.png`, `living.png`, `bedroom.png`, `gallery.png` and
`neighbourhood.png` are fixed-camera runtime inspections, bots disabled, pixel ratio 1 with
sun shadows. The elevated neighbourhood camera shows visual context outside the playable bounds;
it does not prove that the surrounding houses are accessible.

`home-plan.svg` and the updated `as-built.svg` are derived from current collision solids.
Physical route and live combat evidence, including exact rendering contexts and measurements,
are linked in [CURRENT-VALIDATION.md](../CURRENT-VALIDATION.md). Older pass directories are kept
for comparison, not presented as current timing or geometry evidence.

`homes/flat-walk.webm`, `walk-*.png` and `route-report.json` record the new continuous physical
route. All four checkpoints passed in 1,915 ticks; no page/request errors. Final 180-sample
software mean 611.46 ms, at half pixel ratio. It is scripted physics traversal with bots disabled.

`homes/combat-input.webm`, `first-person.png`, `aiming.png`, `combat.png`, `victory.png` and
`combat-report.json` are the final normal mouse/keyboard production-preview run: all three bots,
capture and reset passed, 88 health, 589.91 ms software mean over 149 frames.
`capture-before-waypoint.json` is a separate earlier automation failure after the game had already
won; the exact-waypoint assumption was corrected without changing gameplay or the victory assertion.
