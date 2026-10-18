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

The Blender visual pass supersedes the screenshots in checkpoint `d5faf61`. The concept artwork in
`docs/concepts` remains a visual target, not runtime evidence. See [current validation](../CURRENT-VALIDATION.md)
for actual results and rendering limitations.

The physical route screenshots were captured before the final foliage detail and reload-pose
adjustments. Their collision/layout is unchanged. The combat and presentation captures show
the final art pass. Frozen poses and scripted routes are labelled in the HUD and are not
presented as human gameplay or concept images.
