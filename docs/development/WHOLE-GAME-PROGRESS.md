# ONSITE whole-game implementation

19 October 2026. Product goal: [ONSITE-GOAL.md](../ONSITE-GOAL.md).
The current tranche completes the integrated bots-first player journey and improves
character, weapon and estate presentation. It does not complete every product gate.

## Preserve and restore

Baseline: `483cc0ae14a9e498b757fe15e1084a86829c27ec`, also preserved at
`checkpoint/onsite-before-whole-game-2026-10-19`. Create a separate recovery checkout
with `git worktree add /tmp/onsite-before-whole-game 483cc0a`; do not reset the active
checkout over later work. Original characters, concept art, Blender sources,
textures, research and tests remain. No merge or deployment is authorised here.

## Implemented

| Item | Actual change | Ownership |
| --- | --- | --- |
| Player journey | Accurate Court/Reach briefing and map links; lazy interactive kit preview; synchronised title/pause settings; actual terminal results; retry/title; safe versioned preferences and per-map last/best captures. Keyboard tabs/dialog focus and 390 px menu layout. | Original `FrontEnd.ts`, `profile.ts`, HTML/CSS and `main.ts` integration. |
| Settings | Sensitivity and audio feed existing WWB input/audio. Reduced motion attenuates additive camera kick and existing weapon bob, preserving simulated aim/recoil. Balanced caps hardware DPR at 1 and disables bloom; detail/auto retain 1.5 cap. Software stays at 0.5 unless explicitly inspecting. | Original presentation adapter. No new simulation or networking. |
| Operator | Original 20-bone Blender figure, weighted continuous trousers, black hoodie/balaclava/gloves, hood up/down and three trainer meshes. Private skeletons for each bot, analytic walk/aim/recoil/death and barrel socket. | [Operator source/provenance](../characters/OPERATOR.md); stylised foundation, not final scanned character art. |
| Reload | Smoothly blend the imported arms into/out of the original IK reach, ease magazine/bolt stops, retain magazine contact until seating. Actual GLB tests remove the measured 77.4 mm endpoint bone snap. | Licensed IRONLINE rifle/arms remain; original ONSITE motion. [Pose evidence](WEAPON-PRESENTATION-2026-10-19.md). |
| Shop depth | Replace four Corner shelf units with actual two-sided stock and fittings; add supported laundry stock; remove three photographic interior cards and superseded backboards. All geometry stays within existing furniture footprints and clear of door/aisle routes. | Original Blender kit, existing atlas shared. [Provenance and geometry checks](../maps/heron-reach-32/art/SHOP-DEPTH.md). |
| Contact grounding | Floor-aware soft patches under existing props and live bot feet, clipped to their receiving storey and faded when airborne or distant. | Original one-draw procedural mask. [Costs and limits](../maps/heron-reach-32/art/CONTACT-GROUNDING.md). Not physical local-light shadows. |

The active movement, Arsenal, bots, physics, layered navigation, damage and round
rules remain WWB-based. The only donor Input change gates gameplay key capture on
pointer lock so menu Tab/Space/select arrows work. The title and pause now use the
existing audio gates. The kit preview stops outside its panel; the estate backdrop
holds its last frame while that preview renders, avoiding two active scene renders.

No collision or navigation definitions changed. ONSITE’s round adapter now keeps
WWB bookkeeping active until clear-and-capture finishes; donor score-race rules
remain unchanged. Death and deadline take precedence over capture on the same tick. Verbatim `JSON.stringify(solids)`
on both baseline and current Reach produces **2,417** solids and SHA-256
`20dd85b0d070f557aada8b610cf03d6ba887e291792c90e98e1f87225101b1a0`.
This hash uses that exact serialisation, not the earlier layout-export format.

## Measured asset costs

- Operator GLB: **1,150,548 bytes**, 16,714 triangles including hidden alternatives;
  default visible kit 13,874 triangles, 10 active material draws, 20 bones. Two tiny
  original 128² cloth maps are embedded and sourced under `assets/textures/operators/`.
- Shop depth GLB: **184,612 bytes**, 7,944 triangles, 6 batches. Revised lived kit:
  110,100 bytes / 2,242 triangles. Removing the four old shelf units and redundant
  lived panels reduces their combined geometry by **12,402 triangles**, before cards.
- Grounding: 278 static patches plus up to 12 current bot-foot patches, **one draw /
  580 triangles**. Fixed capacity for 32 actors uses approximately 28.7 KB of instance
  attributes; no texture or off-screen target. This capacity is not online support.
- Main production JS remains large: approximately **5.38 MB raw / 1.96 MB gzip**,
  with the existing Vite chunk-size warning. The kit renderer is a lazy chunk.

## Validation and evidence

Frozen integrated runtime source: `3284c4d` (including final capture bookkeeping
and death/deadline precedence fixes). See the evidence build manifest for served
JavaScript hashes.

- **84 tests pass**: 10 preserved simulation tests plus 74 active navigation,
  physical route, material, asset, profile, camera, contact and actual-rig tests.
- Typecheck and production build pass. Each of the four intermediate art/reload
  branch snapshots also independently passes typecheck and build.
- The isolated interface fixture was rerun with the final operator and passes nine
  groups: real Input listener keyboard
  behaviour, actual kit asset, persistence, focus, once-only results and narrow layout.
  Its synthetic terminal states are interface evidence, not combat evidence.
- The **production runtime flow** passes actual title/kit loading, live settings,
  keyboard entry and pointer lock, pause/audio freeze/resume, return to title,
  persisted preferences, real map switching and Court movement. 390 px menu checked.
- Heron Court: **10 browser check groups pass**, all three opponents cleared,
  captured and reset; 72 health remaining, 44 shots / 15 hits, 35.28 simulated seconds.
  Its completed win is saved exactly once.
- Heron Reach: **9 browser check groups pass**, all six opponents cleared, captured
  and reset; 84 health remaining, 86 shots / 36 hits, 95.75 simulated seconds.
  The final shot is retained, the capture clock continues and the completed result
  is saved exactly once. No page or failed/HTTP-error requests on either final run.
- [Matched evidence and renderer labels](evidence/whole-game/README.md) distinguish
  camera-placement, reload-clock, interface-fixture and actual combat captures.
  All four reload phases and the separate final operator viewpoint pass without
  console/page/request errors; a 25-second unretimed combat excerpt is retained.

Issues found and resolved during verification: native menu keys were swallowed by
the gameplay input handler; reduced-motion initially affected only weapon bob;
old navigation fixtures supplied an empty visual scene and now load the actual rig
without weakening route assertions. First operator previews exposed garment gaps,
which were refined before the final export. A new material-sharing loader initially
allocated every library material; it now fetches only required names, avoiding six
unused fallback maps (about 25 MB estimated mip allocation). The inherited art
capture label incorrectly said bots were frozen; the runtime keeps them active,
and the script/report labels have been corrected without changing bot simulation.
A full Reach run exposed a real integration bug: the last kill ended the donor
score race before capture, freezing its clock and discarding the final shot. The
ONSITE adapter now uses an unreachable frag threshold for the fixed opponent roster;
its own capture/death/deadline state remains authoritative. A review also caught
same-tick capture overriding a loss; the production step now returns on death or
timeout. Regression tests cover both rosters, final-shot statistics, the continuing
deadline and simultaneous capture/death/timeout. The failed Reach state and image
are retained separately from the final passing run.
The baseline reload fixture initially
lacked its imported map JSON files; adding the exact baseline files restored it.

All cloud screenshots and frame timings use **Chromium / ANGLE SwiftShader**, a
software renderer. Native-resolution inspection captures explicitly use DPR 1;
normal gameplay keeps DPR 0.5. They do not demonstrate real-GPU frame time, smooth
play, final character quality or production readiness. Real-GPU verification is
still deferred by the owner and has not been silently treated as complete.

## Software-renderer measurements

1100 × 700 viewport, normal DPR 0.5, Chromium 154 / ANGLE SwiftShader. Samples are
render wall time during automated input with video recording, not real-GPU benchmarks.

| Encounter | Samples | Mean | Median | p95 | Approximate FPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Court | 144 | 518.33 ms | 511.90 ms | 648.00 ms | 1.93 |
| Reach | 360 | 694.25 ms | 684.80 ms | 879.30 ms | 1.44 |

The cloud renderer is far below the eventual performance target. No smoothness or
production-readiness claim follows from passing the encounter. Draw and triangle
counts are view-dependent; consult the JSON reports rather than extrapolating a
single camera to the whole map. Reach’s final view reports 412 calls / 1,222,938
triangles. Its 82 architecture WebP fallbacks estimate 328,996,233 bytes including
mips; this is a texture-allocation estimate, not measured total process/GPU memory.
The hardware compressed-texture path is not exercised by this SwiftShader run.

## Launch and verify

```sh
npm ci                         # Node 24
npm run dev                    # / or /?map=heron-reach
npm test
npm run typecheck
npm run build
npm run preview -- --port 4184
ONSITE_URL=http://127.0.0.1:4184 node scripts/verify-runtime-flow.mjs
ONSITE_URL=http://127.0.0.1:4184 npm run test:browser
ONSITE_URL=http://127.0.0.1:4184 node scripts/maps/verify-heron-reach.mjs
# Against Vite for the non-production UI and reload fixtures:
ONSITE_URL=http://127.0.0.1:5173 node scripts/verify-player-flow.mjs
ONSITE_URL=http://127.0.0.1:5173 node scripts/check-presentation.mjs
```

Run browser captures/encounters serially against an immutable build. Keep Blender
and other browsers stopped during frame-time recording. The implemented map is
unchanged; use [the as-built plans](../maps/heron-reach-32/as-built/README.md).

## Remaining product gates

The next high-value work is richer character sculpt/cloth and authored animation,
physical local-light shadow/contact and scene-reflection quality, greater facade
and home/interior variation, properly sourced spatial ambience and impacts, and
human combat/approach-route playtesting. The synthetic audio fallback is still a
placeholder. There is no completed stealth system, content progression, online
service or tested 32-player load/balance. Hardware profiling and a device budget
remain necessary before declaring performance adequate. Continue from the whole-game
goal; do not restart the engine or treat this tranche as the entire finished game.
