# Current architecture

The sections below describe the **preserved initial prototype**. The active WWB runtime integration, simulation ownership and height-aware navigation are documented in [DONOR-MAP.md](DONOR-MAP.md) and [HANDOFF.md](HANDOFF.md). Do not use the old one-bot/one-stair description as the current map.

# Bots-first playable foundation

## Boundaries

`src/sim/level.js` describes collision in metres. `Simulation` owns one Rapier world, 60 Hz fixed steps, command validation, player/bot movement, ray queries, health, ammunition, reload clocks and encounter state. It imports no Three.js, DOM or audio code. Input commands carry sequence, movement/look and button intent, never hit/damage claims. Snapshots are plain copied data and events.

`src/sim/combat.js` is the physics query adapter. `src/sim/navigation.js` is an authored 3D walk graph with both floor levels and a connected 16-riser staircase. Collision boxes, navigation nodes and render GLBs are distinct. Changes to the estate layout must keep all three aligned; tests verify the core stairs and graph heights.

`src/main.js` owns browser events, pause, fixed-step scheduling, HUD and synthesized sounds. `src/view/WorldView.js` owns Three.js, original GLBs, static geometry batching, lighting, PBR materials and presentation-only recoil. Read-only browser diagnostics expose snapshots/metrics, not teleport or damage commands.

This is an in-process bot simulation, with no networking code. The boundary is suitable for moving authority into a separate process later, but no server compatibility, prediction, reconciliation, lag compensation or cross-platform deterministic replay is claimed.

## Encounter

Spawn at the south entrance. Walk/sprint/jump through the courtyard, or take the west stairs to the 3.2 m walkway. Eliminate the patrolling hooded opponent, then remain within 3 m of the court marker for three seconds. A round ends on capture, player death or the 180-second limit. Escape/blur pauses simulation and clears held input; resume requires pointer lock. Restart clears the round and ammunition state.

The single bot patrols authored court waypoints, checks a vision cone/range and physics line of sight, waits 1.2 seconds before firing, and remembers the last seen location. The explicit 3D graph supports investigation via the stairs. It is not a full tactical AI, dynamic navmesh, squad system or general obstacle planner.

## Assets and performance

Six original 512 px PBR sets total about 3.2 MB on disk. Source PNG references and editable Blender files stay outside public runtime assets. GLBs contain only visual geometry. Painted steel is dielectric paint (metalness 0); bare exposed metal would need a separate metalness mask. The maps have exactly equal opposing edges; that alone does not eliminate visible pattern repetition. Inspect material scale and repetition in future art passes.

Static boxes are merged per material. Window/fence structural elements are instanced. Hardware render pixel ratio is capped at 1.25. Detected SwiftShader/llvmpipe software rendering uses a reduced pixel ratio and disables shadow maps. Browser diagnostics record uncapped wall-clock frame durations, while simulation catch-up is bounded to avoid stalls. This software-rendered cloud session is not a gaming-GPU benchmark.

## Known scope limits

- Desktop mouse/keyboard only; no touch or gamepad flow yet.
- Character likenesses, rigging, detailed weapon animation, weather and final environmental art remain future work.
- Fence panels block bullets as a whole even though their visual wire mesh is open.
- Some decorative props are non-colliding; core architecture, cover, stair risers, court fences and lamp poles have collision.
- No crouch, aiming down sights, pickups, multiple weapons, multiplayer, persistence or backend.
- Browser load errors are shown; there is no automated GPU compatibility fallback beyond software-renderer resolution scaling.
