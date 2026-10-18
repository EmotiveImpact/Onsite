# ONSITE donor map and implementation audit

## What was actually present

Before this integration, `src/main.js` owned input/HUD and called original `src/sim/Simulation.js` and `src/view/WorldView.js`. `src/adapted/` contained translated WWB helper patterns. That was a separate simplified prototype, **not WWB's working runtime**. The old sources/tests, assets and art remain. `legacy.html` retains its entry point. Recovery is documented in [CHECKPOINT.md](CHECKPOINT.md).

The active entry is now `src/onsite/main.ts`. It constructs the imported WWB `Input`, `GameLoop`, `Physics`, `Player`, `Arsenal` and `Bot` classes. `src/onsite/Encounter.ts` implements WWB's `CombatWorld` interface and uses its round/statistics rules. The upstream all-modes `Game` and web shell are intentionally not imported: they couple in the cloud/duel, wave bosses and asset streaming outside this milestone. This is a selectively integrated WWB runtime, not an unchanged copy of its entire application.

## Donor boundaries

| System | Actual implementation | Changes / exclusions |
|---|---|---|
| Physics and player | WWB `engine/physics.ts`, `game/player.ts` | Same Rapier owner, capsule controller, acceleration, jump buffering/coyote, crouch/slide and collision. Estate speeds 4.6/6.8 m/s; no regenerating armour. |
| Input / scheduling | WWB `engine/input.ts`, `engine/loop.ts` | Same unified input and fixed simulation/render interpolation. Added clear-on-pause input reset. No network input path. |
| Weapons | WWB `game/weapons.ts`, `game/guns.ts`, noise helper from `library.ts` | Full Arsenal: fire intervals, spread/bloom, recoil, ADS, reload, impacts and procedural carbine. Remove Tripo loader/upgrades; black materials; original support-hand reload motion; separate weapon-camera rendering. Rifle is the encounter loadout. |
| Bots | WWB `game/bots.ts` | Preserve perception, reaction/focus, hearing, chase/cover, burst fire, reload, damage and aim. Replace single-floor movement/navigation with original layered path nodes and Rapier movement. Remove remote puppet method. One actor movement owner. |
| Character visuals | Original ONSITE `game/robot.ts` adapter + existing Blender GLB | No donor character models, rigs or clips. Current figure remains a stylised placeholder; original simple procedural animation. |
| Effects / audio | WWB `game/fx.ts`, `engine/audio.ts` | Procedural effect fallback. Original synthesized sample fallback; no donor audio/music files requested. |
| Rules | WWB `game/rules.ts` | Round timer, damage, kill/stat accounting. ONSITE encounter wrapper: three opponents, clear and hold court, death/timeout/reset. |
| Environment | ONSITE `level.ts`, `View.ts`; existing WWB-attributed batching helper | Actual 36×30 m two-level layout from supplied proposals; render detail separate from static colliders/nav. No complete donor arena or its bundled models imported. |
| IRONLINE | Read-only design/implementation study | Reviewed `ViewModel.js`, `ReloadChoreo.js`, `Navigation.js`, screenshots/framing docs. Adopted separate viewmodel FOV, sight-alignment and reload-phase ideas through original changes to WWB. **No IRONLINE code, animation tracks or assets copied.** ISC package metadata and embedded third-party animation references are not a complete grant/provenance record. |
| Modern Claudefare | Read-only architecture study | `js/net/index.js`, `prediction.js`, `snapshots.js`: host simulates, guest sends inputs/claims, correction replay, buffered remote views, schema-driven snapshots. No code/assets imported; no networking implemented. |

WWB source is pinned to `4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1`, MIT © 2026 Jeevesh Singale. Imported modules carry headers and the complete notice is shipped in `public/licenses/WWB-MIT.txt`. Type adapters/original files explicitly identify their origin. Asset licensing is separate from the code licence.

## Height-aware bot navigation

`src/onsite/navigation.ts` produces multiple floor nodes at the same x/z and tests headroom against collision solids. Adjacent nodes only connect across walkable height changes. Paths carry y; chase goals retain target height; no 2D shortcut smoothing across the courtyard void. Bot separation ignores actors on different floors. Each bot has a Rapier character controller within the single world. The upstream height-teleport movement is removed. Tests drive the actual bot brain and physical capsule up and down both stairs, rather than only asserting graph connectivity.

## Later online phase (reference findings only)

The mirror describes a PeerJS host-authoritative session, not a deployed dedicated authoritative server. The host validates input and hit claims, owns bots, and serializes combatants. Guest prediction replays pending inputs after correction; remote views use delayed snapshot interpolation. Contracts share the prediction state fields with snapshot fields, and sequence checks reject stale packets. Host departure ends the session; no authority migration is assumed. These are static inspection findings, not a network audit or evidence of robustness. Keep future intent commands, authority, snapshots and presentation separate; do not import the unlicensed implementation or configured remote services.
