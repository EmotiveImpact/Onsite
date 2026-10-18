# ONSITE provenance

**Current runtime update:** [DONOR-MAP.md](DONOR-MAP.md) records the actual WWB module integration after this initial prototype audit. The historical helper table below describes the preserved legacy runtime only.

Current photographic surfaces come directly from Poly Haven (CC0), with source URLs, original/download hashes and output hashes in `public/materials/pbr/provenance.json`. Five source sets serve six roles (stock brick is tinted brick). Two Poly Haven props, utility_box_02 and security_light, are the only WWB-bundled GLBs imported; their fetch/build trail, authors and hashes are recorded in `public/models/polyhaven-provenance.json`. No Tripo/Manus models or donor audio/animation clips are imported. Original procedural textures and Blender files remain preserved; the old first-person GLB is retained but the current weapon uses WWB procedural geometry.


Reviewed 18 October 2026. Code licences do not automatically cover a repository's bundled art, audio, fonts or animations.

## Runtime and tooling

| Dependency | Version | Licence | Use |
| --- | --- | --- | --- |
| Three.js | 0.186.1 | MIT | Renderer, GLTFLoader, RoomEnvironment, BufferGeometryUtils |
| @dimforge/rapier3d-compat | 0.21.0 | Apache-2.0 | WASM physics, capsules, character controllers, ray queries |
| Vite | 8.3.4 | MIT | Local development and build tooling |
| @playwright/test | 1.61.1 | Apache-2.0 | Local Chromium verification |

Exact transitive dependency versions are pinned in package-lock.json; installed packages retain their own licences. Runtime notices are copied verbatim to public/licenses and included in the build. Original project code is private/unlicensed unless separately specified; the upstream MIT grant continues to apply to the adapted portions.

## Preferred gameplay source: WWB

Repository: https://github.com/jeevesh2515/WWB

Reviewed commit: `4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1`.

MIT, copyright (c) 2026 Jeevesh Singale. Complete notice: [WWB-MIT.txt](../../public/licenses/WWB-MIT.txt).

Selective adaptations, translated from TypeScript into the existing plain-JavaScript prototype:

| Upstream source | ONSITE destination | Scope and changes |
| --- | --- | --- |
| src/game/player.ts | src/adapted/gameplay.js, src/sim/Simulation.js | Acceleration/air control and jump-buffer/coyote patterns, metre-scale Rapier capsule movement. Slower estate movement; no slides, armour regeneration or network puppets. |
| src/engine/physics.ts | src/sim/Simulation.js | Character controller and fixed-box approach evaluated; original lightweight owner, one physics step per tick. Render models remain separate. |
| src/engine/input.ts | src/adapted/input.js | Normalised desktop movement and action mapping; no gamepad/debug-forced controls imported. |
| src/engine/loop.ts | src/adapted/loop.js | Fixed-step accumulator, pause/reset; bounded catch-up and terminal-round stop. |
| src/game/weapons.ts | src/adapted/gameplay.js, src/view/WorldView.js | Magazine/reserve accounting and recoil spring; one original fictional weapon with simulation-timed reload. No Tripo assets or animation clips. |
| src/game/rules.ts | src/adapted/gameplay.js | Damage, shot statistics, accuracy and clock helpers. ONSITE has a 180-second eliminate-and-capture encounter instead of WWB's frag race. |
| src/game/combat.ts | src/sim/combat.js | CombatWorld-style query separation; original Rapier-only implementation without rendering/audio/network dependencies. |
| src/game/bots.ts | src/sim/Simulation.js | Perception, reaction delay and last-seen pursuit reviewed as design references; original small bot controller for this encounter. |
| src/game/arena.ts | src/adapted/environment.js | Static geometry grouping/merging and procedural chain-link texture adapted immediately. ONSITE-specific estate dimensions, facade layout, court and lighting. |

WWB's navigation grid stores one floor per x/z cell. Its arena baking excludes surfaces at/above 3 m. Neither implementation was imported. ONSITE uses explicit 3D nodes and stair edges with distinct upper and lower nodes at the same x/z coordinates. This is a small authored graph, not a general navmesh baker.

No WWB cloud, Supabase, duel, lobby or network code is included. Its local race mode is not treated as proof of online multiplayer. At the initial prototype checkpoint no WWB GLBs, textures, fonts, audio, skeletons or clips had been imported. The current exceptions are the two separately reviewed CC0 props described above. Its NOTICE is not a sufficient licence inventory; assets.lock.json only records two share images. Poly Haven fetch records are clearer, but that does not establish rights for its Tripo/Manus or animation assets.

## Other evaluated sources

- DIVE: https://github.com/Mugen87/dive at `7176136cf6c29eddfd620df2bf0d09a532680763`. Code MIT, copyright 2019 Dive authors; Three.js 0.113.0. Reviewed Enemy.js and WeaponSystem.js for perception, memory, navigation and reaction delay. No code copied. Its models README explicitly lists the rifle as CC BY-NC and the soldier licence as "None"; no DIVE assets imported.
- three-fps: https://github.com/mohsenheydari/three-fps at `625a18c2240687796a0440190cfe3dd7f3ce45a2`. Code MIT, copyright 2021 Mohsen Heydari; Three.js ^0.127.0. Reviewed Weapon.js/WeaponFSM.js for reload, hitscan and animation state patterns; no code or assets copied.
- Rapier: https://github.com/dimforge/rapier at `475caa3ff4646fd9a796b67d14116256f4962bc7`. Apache-2.0. Reviewed character controller autostep/snap-to-ground implementation; runtime comes from the pinned npm package, not this source checkout.

## Assets used by the playable

| Asset | Source | Status |
| --- | --- | --- |
| Four GLBs: estate-lamp, estate-bench, hooded-opponent, first-person-prop | Original scripts/build-assets.py, generated in Blender 4.3.2 | Original prototype geometry; no imported scans, rigs or animation clips. Editable .blend files in assets/blender. Metres, GLB Y-up. |
| Six PBR materials / 18 maps | Original scripts/build-materials.py | Procedurally authored colour, OpenGL +Y normal and roughness maps, 512×512. No external texture samples. Manifest contains hashes. |
| Estate architecture, rails, court, planting, signs | src/sim/level.js and src/view/WorldView.js | Original procedural geometry, with WWB-attributed batching/chain-link helper. |
| Shot/reload/hit sounds | src/main.js Web Audio oscillators | Original synthesized sounds, no sound files imported. |
| Existing concept sheets / texture candidates | Earlier user-directed image generation in this repository | Preserved unchanged; visual reference only. None of the large source PNG pack is loaded at runtime. No independent third-party provenance claim is made for generated art. |

The hooded opponent is a stylised placeholder with black clothing and trainers, not a finished Jay/Alex likeness. Limb motion is procedural, not a skinned animation rig. Blender scene lights are not relied on: all gameplay lighting is explicitly created in Three.js.

## Additional visual reference

IRONLINE: https://github.com/cktang88/3d-fps — requested for contemporary industrial detail, weapon presentation and elevated walkway design. Separate code/asset licensing review is pending. A package ISC declaration is not evidence that every bundled asset is cleared. No IRONLINE code or assets have been imported into this prototype.

The two ignored local study clones (IRONLINE and Open Claudefare), their pinned commits and additional licence caveats are recorded in [research notes](../../research/README.md) and [source manifest](../../research/SOURCES.json). Neither is bundled or imported. Open Claudefare is an unlicensed personal mirror; no reuse grant is assumed.

## Blender/donor visual pass, 18 October 2026

Superseding earlier statements that no IRONLINE art was imported: selected CC BY first-person M4/arms
and CC0 props/HDRI are now active. See [the shipped detailed credits](../../public/licenses/DONOR-ASSETS.md)
and [per-file provenance](../../public/models/donors/provenance.json), including original API metadata
and hashes. No Fab motion data or IRONLINE engine code is copied. `DonorRifle.ts` and the Blender
estate generation/export scripts are original adapters. The level is editable in the new `.blend`;
its render export excludes collision/navigation guides and uses the existing PBR library.

## Additional courtyard dressing

The dirt pass adds five CC0 Poly Haven props and ambientCG Ground110/Leaking003 maps through the same pinned IRONLINE clone. Original publisher metadata/licence and payload hashes are retained in the donor/material manifests. Original generated asphalt source and encoding records are preserved in `assets/textures/onsite-dirt-pass`. Blender grass, folded litter, cans, fallen leaves and placement are original ONSITE work; read [DIRT-PASS.md](DIRT-PASS.md).

## South London residential pass

Original Blender homes/furniture and visual surroundings: `scripts/build_homes.py`, `assets/blender/onsite-heron-court.blend`. Four Dawson's Heights/Brandon Estate photographs were visually studied; URLs/hashes in `research/SOUTH-LONDON-REFERENCES.json`. No photograph pixels or new donor assets were imported. Stock brick uses the existing original generated source, encoded by `scripts/prepare-home-material.py`; provenance at `public/materials/homes/provenance.json`.
