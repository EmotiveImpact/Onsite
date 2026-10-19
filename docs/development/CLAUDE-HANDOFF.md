# ONSITE — handoff for Claude

## Current: Heron Reach scene depth — 19 October 2026

Continue from `codex/heron-reach-scene-depth`, based on the complete seven-item art
stack below, in [PR #12](https://github.com/EmotiveImpact/Onsite/pull/12). The owner asked for more detail and a deeper, convincing London scene;
[the working prompt and remaining production gaps](NEXT-QUALITY-GOAL.md) record that
goal. [This pass's work log](../maps/heron-reach-32/art/SCENE-DEPTH-2026-10-19.md)
contains the actual implementation, matched before/after views, sources and checks.
No merge or deployment is authorised for this pass.

The existing WWB gameplay stays intact. Additions are Blender shop/service detail;
two individually licensed Poly Haven scan types from IRONLINE; corrected storey/
visibility selection for the fixed light pool; quieter dry/wet material response;
cleaner gallery netting; and an MIT height-fog adaptation from Operation Blackout.
Claude of Duty is a pinned MIT research clone, not a shipped subsystem. All five
reference clones remain clean, ignored and outside the bundle. Read
[the donor review](../research/NEXT-QUALITY-DONORS.md) before further imports.

New Blender files are `lived-detail.blend` and `scanned-detail.blend` under
`assets/blender/heron-reach/`; generators and exact provenance are recorded beside
them. Do not overwrite original 5.2 sources using the available 4.3 CLI. Render-only
additions total 621,826 bytes, 5,888 triangles and 15 exported primitives; this exceeds
the initial 12-batch target by three. Shader hooks compose surface → wetness → fog.
The two replaced shop fixture groups are found through `userData.name`, because
GLTFLoader sanitises authored names. The actual-GLB regression protects this path.

Launch with `npm ci`, `npm run dev`, then `/?map=heron-reach`; plain `/` remains
Heron Court. Run `npm test`, `npm run typecheck`, `npm run build`, then the two browser
encounters sequentially against a production preview. Use the work log's saved
viewpoints for comparisons. Real-GPU benchmarking is still deferred, not a blocker.

Final validation: all 55 tests, typecheck, build and both full browser encounters
passed. Reach cleared six bots/captured/reset at 76 health; Court cleared three at
84 health. Mean frame times were 676.45 ms / 588.57 ms on SwiftShader, not a real GPU.
The original failed Reach run is retained; a reviewed correction bounds automation
fire bursts and removes stale aim snapshots, preserving normal input and the full
victory assertion. Thirteen fixed-camera captures passed with no console/page/network
errors. The work log links the raw reports and an unretimed closing gameplay excerpt.

Most valuable next work: measured local/contact shadows, then optional masked
scene reflections, plus replacing flat shop panels with deeper authored stock.
Characters, hand animation, audio and encounter/stealth quality need separate
passes. More donor clones do not by themselves solve those production gaps.

## Previous seven-item visual stack

### Heron Reach visual pass — 19 October 2026

The owner explicitly deferred real-GPU benchmarking. Work continued on the existing Heron Reach
runtime (`/?map=heron-reach`), preserving Heron Court and the WWB simulation. **Nothing from this
visual pass has been merged by this session.** The complete result is on the final branch in the
[review stack](../maps/heron-reach-32/art/ART-PUSH-2026-10-19.md#recovery-and-review); use that branch
to inspect all seven items together. Main remains the live baseline. PRs [#5](https://github.com/EmotiveImpact/Onsite/pull/5) through
[#11](https://github.com/EmotiveImpact/Onsite/pull/11) form the ordered review stack.

Read [the visual work log](../maps/heron-reach-32/art/ART-PUSH-2026-10-19.md) for matched runtime
screenshots, raw browser reports, rebuild commands, provenance and limitations. These are actual
SwiftShader captures, not concept artwork or evidence of hardware performance.

The pass adds patchy wet PBR ground and floor-aware lamp streaks; warm pools and blue-grey haze;
a Blender football cage kit; lit shop cards behind existing 3D stock; frosted stairwell glazing,
fluorescents and service details; eight middle-distance towers and winter trees; KTX2 architecture
textures with WebP fallback; Blender gallery netting and an amber objective marker.

Keep using the existing architecture. Collision/navigation remain in `heronReach.ts` and the
layered navigation module. This is still a six-bot playable on a map designed for future 32-player
matches, not an implemented 32-player online mode.

Current environment: Node 24.19, Three.js 0.186.1, Rapier 0.21, Blender 4.3.2 CLI, Chromium 154 /
ANGLE SwiftShader. No hardware GPU. Original Blender 5.2 sources are preserved; 4.3 cannot read
them. New compatible files rebuild from the original Python generators. A fixed Blender 4.3
UV/colour-layer issue now has generator and exported-GLB regression checks.

The KTX2 library is 34.71 MB versus 20.04 MB for its WebP sources: a GPU allocation optimisation,
not a download-size reduction. Normal maps use UASTC for quality. Embedded kit textures remain
WebP and are the next compression target. Actual GPU timing, VRAM, bloom, shadows and fine
alpha-detail quality still need hardware verification. Wet reflections currently use the dusk
environment plus local lamp streaks, without scene-object SSR/planar reflections.

To launch the combined branch locally:

```sh
git switch codex/heron-reach-textures-dressing
npm ci
npm run dev
# Open /?map=heron-reach; plain / is the Heron Court regression map.
```

For repeatable verification use Node 24, `npm test`, `npm run typecheck`, `npm run build`, then a
production preview. Run `scripts/maps/verify-heron-reach.mjs` and `npm run test:browser` sequentially
with `ONSITE_URL` pointing to that preview. Saved camera fixtures and capture commands live in
the visual work log. No gameplay code or collision/nav data changed in this pass; the physical
solid count is still 2,417. No research clone is tracked or bundled.

Final validation: all 43 tests, typecheck, production build, eight matched inspection views,
three texture/fallback probes and both full browser encounters passed. Reach cleared six bots,
captured and reset (60 health); Court cleared three, captured and reset (96 health). No page or
request errors. Rolling SwiftShader frame means were 680.89 ms / 563.57 ms — around 1–2 FPS,
not smooth. The visual work log links raw reports and an unretimed gameplay excerpt.

Next valuable work: real-GPU captures at the saved viewpoints; tune bloom/shadow/foliage budgets
from those results; assess a measured optional ground reflection pass; compress embedded kit maps
and reduce duplicate texture allocations; review room/interior depth and distant-window repetition.
Do not treat passing tests as proof of concept-art parity or smooth gameplay.

Prepared 18 October 2026 for the user's requested push and merge. Gameplay/assets checkpoint:
`debebb46aaa6895af080bf633d928d61a1b46173`. This handoff changes documentation only; the previous
four local implementation commits are included in the publication. Start from the current remote
`main` after the handoff merge, inspect `git status`, and make a new working branch.

## Continue this build

ONSITE is a browser FPS on a fictional South London estate, Heron Court SE15. The immediate target
is a convincing, enjoyable courtyard encounter against bots. The user explicitly wants the actual
WWB gameplay foundation, suitable licensed IRONLINE art, Blender-authored homes/levels, dirty
ground, grass and rubbish. Preserve original art and the consistent ONSITE interface. Black
British characters, black hoodies, balaclavas, gloves, joggers and selectable trainers remain the
character direction. Detailed character modelling/rigging and kit selection are not finished.

Do useful implementation work on this foundation. Do not restart with another simplified shooter,
add networking now, or treat passing tests as proof of visual quality or satisfying combat.

Read [HANDOFF.md](HANDOFF.md), [DONOR-MAP.md](DONOR-MAP.md),
[CURRENT-VALIDATION.md](CURRENT-VALIDATION.md), [BLENDER-LEVEL.md](BLENDER-LEVEL.md),
[SOUTH-LONDON-HOMES.md](SOUTH-LONDON-HOMES.md), and the original
[modelling notes](../concepts/MODELLING-NOTES.md) and [texture pack](../concepts/TEXTURE-PACK-30.md).

## Existing parallel Claude work

At publication inspection, [PR #1](https://github.com/EmotiveImpact/Onsite/pull/1) was open on
`claude/threejs-estate-prototype-21bnx5`, head `4c7bde99992524edcfd0af661d6a1f6b9d8578ed`.
It adds a separate `game/index.html` prototype using Three.js 0.170.0 and custom box movement.
That branch is preserved, not merged as part of this handoff. Its PR description reports some
browser checks; those were not independently rerun here. Inspect it before selectively using
useful presentation work, but do not merge two controllers or replace the newer WWB/Blender runtime.
Check the PR's current state because this is a dated observation.

## What actually runs

| Area | Implementation and ownership |
| --- | --- |
| Entry | `index.html` → `src/onsite/main.ts`; Three.js 0.186.1, Rapier 0.21.0. |
| Gameplay | Actual imported WWB `src/wwb/engine/{input,loop,physics}.ts` and `game/{player,weapons,bots,rules,combat}.ts`, plus effects/audio. `src/onsite/Encounter.ts` implements `CombatWorld`. No WWB cloud backend/duel/web shell. |
| Navigation | Original `src/onsite/navigation.ts`: layered nodes retain multiple floors per x/z cell; real Rapier capsules traverse stairs. One physics world and one movement owner per actor. |
| Level | Blender estate render GLB; `src/onsite/level.ts` owns collision/navigation solids. `dressing.json` records donor placements and measured colliders. `View.ts` owns Three.js lighting/materials. |
| Weapon | Individually licensed IRONLINE M4A1/posed arms, Blender sleeve/material finishing, original `DonorRifle.ts` framing and reload reach. WWB owns ammo, timing, recoil and hitscan. No donor motion clips. |
| Other donor art | Twelve verified Poly Haven props and one HDRI through IRONLINE; two ambientCG surface sets; two traced Poly Haven props from WWB. Exact credits/provenance under `public/licenses/` and material/model manifests. |
| Original work | Estate, homes, layered navigation, encounter/presentation adapters, original generated textures, stylised hooded opponent and Blender dressing. |
| Reference only | Unlicensed Modern Claudefare mirror; no code/assets imported and no networking implemented. Other unreviewed donor assets remain excluded. |

The active encounter has three opponents. Clear them and hold within 4 m of the court centre on
ground level for 2.5 s; death or a 180 s timeout loses. WASD moves, mouse looks, LMB fires,
RMB aims, R reloads, Shift sprints, Space jumps, C crouches/slides, Escape pauses. Reset restores
the encounter. The original earlier prototype remains in source and at the development
`/legacy.html` entry; it is not the active game.

## Implemented level and editable assets

- Playable footprint: **36×30 m**; ground court/rooms, two dogleg stairs, continuous gallery at
  **3 m**. Proposed user floor-plan artwork guided the layout; use the
  [as-built plan](evidence/as-built.svg) and [collision/spawn data](evidence/layout.json) for truth.
- One accessible furnished **Flat 01**, with kitchen/living area and bedroom. Real furniture and
  partition collision, player and bot traversal. [Flat plan](evidence/home-plan.svg).
- Stock-brick homes, deep window openings, curtains/blinds, 20 private balconies, six terraced
  houses and two point blocks. **Higher balconies and surrounding houses are scenery, not
  additional playable routes.** Bathroom, working doors/appliances and detailed domestic finishes
  remain unfinished.
- Editable level: `assets/blender/onsite-heron-court.blend` (**63.32 MB**). Runtime:
  `public/models/onsite-heron-court.glb` (**17.79 MB**), 6,773 source render objects → 25 material
  meshes. Separate render, collision/nav guide and preview-light collections.
- Editable rifle: `assets/blender/onsite-carbine.blend`; active runtime:
  `public/models/onsite-carbine.glb`. Preserve both external donor arm textures and notices.
- Existing dirty paving, grass, litter, cans, leaves, damp patches and donor props are retained.
  Stock-brick and generated asphalt colour are generated sources, not scanned complete PBR sets.
- Four Dawson's Heights/Brandon Estate photographs were visually studied. Source URLs/hashes are
  in `research/SOUTH-LONDON-REFERENCES.json`; photograph pixels are not shipped.

Blender is metre-scaled, Z-up; GLB is Y-up. Three.js reconstructs lighting; Blender lamps do not
automatically transfer. Physical edits require corresponding `level.ts`/placement updates and
navigation tests. Never derive another movement system from decorative triangles.

## Launch and verify

Tested with Node 24.19.0, Blender 4.3.2 and Chromium 154. A fresh checkout contains the runnable
GLBs/materials; donor clones and a Blender rebuild are not required to play.

```sh
npm ci
npm run typecheck
npm test
npm run build
npm run dev
```

For the input-driven browser check, start `npm run preview -- --port 4173` in one terminal, then:

```sh
npx playwright install ffmpeg
ONSITE_URL=http://127.0.0.1:4173 npm run test:browser
```

The current active browser script explicitly uses `/usr/bin/chromium`; install Chromium there
or update that launch path for the new environment. Reports/videos go to ignored
`test-results/encounter/`. It uses SwiftShader and may take minutes. Do not claim its automated
aim/route decisions demonstrate human combat feel. Fixed inspection and physical flat-route
fixtures are `scripts/capture-homes.mjs` and `scripts/capture-home-route.mjs`, with the dev server
running; these have bots disabled and are separate from normal input combat.

Before rebuilding, preserve manual Blender edits. Read the workflow documents:

```sh
# Regenerate the as-built drawing from physical solids.
npm run evidence:layout
# Incremental homes builder replaces its scripted residential collection and exports.
blender -b --python-exit-code 1 --python scripts/build_homes.py
# Export the existing estate. Check the stored homes revision before editing/re-exporting.
blender -b --python-exit-code 1 --python scripts/export_estate.py
# Full scripted rebuild; replaces the authored scene. Preserve manual changes first.
npm run assets:estate
```

The incremental homes build and export were executed; a full fresh-scene rebuild was not rerun
for the last residential pass. The rifle finishing pipeline also uses temporary intermediates;
inspect its scripts rather than assuming every asset command is a standalone fresh-clone build.

## Verified results and limitations

For this handoff, `npm run typecheck`, `npm test` (**22 passed**, no skips) and `npm run build`
were rerun successfully against `debebb4`. No runtime changes follow that checkpoint in this
handoff. There are no configured GitHub Actions workflows; these are local checks, not CI results.

The earlier residential browser run passed **10 input-driven checks**, killed all three bots,
captured the court and reset: **88 health, 41 shots / 14 hits**, victory at **29.20 simulation
seconds**. No page errors or failed/HTTP-error requests. The independent continuous flat route
passed four checkpoints in **1,915 ticks**. These browser runs were not repeated for the
documentation-only handoff. Exact reports are linked in CURRENT-VALIDATION.md.

**Performance is unresolved:** combat averaged **589.91 ms/frame (~1.70 FPS)** over 149 active
samples on SwiftShader at 1100×700, DPR 0.5, no MSAA/sun shadows, six local world lights. Capture
overhead is included. Real-GPU mode enables MSAA/sun shadows and has not been measured. The
production directory is about **51 MB**, including unused preserved assets; the main JS is
**5,119.15 kB / 1,881.14 kB gzip**, with Vite's large-chunk warning. No smooth-play claim.

Actual renderer evidence: [courtyard homes](evidence/homes/homes.png),
[living area](evidence/homes/living.png), [bedroom](evidence/homes/bedroom.png),
[gallery](evidence/homes/gallery.png), [first person](evidence/homes/first-person.png),
[ADS](evidence/homes/aiming.png), [combat video](evidence/homes/combat-input.webm),
[flat walk](evidence/homes/flat-walk.webm). Fixed inspection views use DPR 1 and sun shadows;
the neighbourhood view is an elevated inspection camera, not a player-accessible position.
The manifest `evidence/homes/build.json` records hashes of the measured assets/source.

## Donor clones, licensing and recovery

`research/reference-clones/` is ignored, untracked and outside the production bundle. All three
copies were present and clean when preparing this handoff. Fresh checkouts will not contain them.
Optional study copies can be cloned from these URLs and checked out at the listed revisions;
do not execute the unlicensed mirror's configured remote services.

| Local path under `research/reference-clones/` | Repository | Pinned revision |
| --- | --- | --- |
| `wwb` | https://github.com/jeevesh2515/WWB | `4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1` |
| `ironline` | https://github.com/cktang88/3d-fps | `130ac2a5c856401ec36e7d35afcfefe40c5801f4` |
| `open-claudefare` | https://github.com/jasonkneen/open-claudefare | `51bdc6e94e60c60abfae9c23f39851bb01e088fd` |

WWB code is MIT; bundled assets require separate provenance. IRONLINE package ISC metadata does
not clear its whole tree. Imported art has individual CC-BY/CC0 records in
`public/licenses/DONOR-ASSETS.md` and `public/models/donors/provenance.json`. No Fab animation,
uncleared Tripo/Manus art/audio or Modern Claudefare code/assets is shipped. Preserve notices.

Recoverable implementation commits, all retained in history:

- `d5faf61`: full WWB courtyard checkpoint before Blender/donor visual integration.
- `e768260`: Blender estate and individually licensed IRONLINE art integration.
- `0ce5a14`: dirty floor/grass/rubbish and rifle sleeves.
- `debebb4`: South London homes and navigable furnished flat.

Use a separate `git worktree` to inspect a prior checkpoint; do not reset over ongoing work.
[CHECKPOINT.md](CHECKPOINT.md) also records an older archive under `/workspace/checkpoints/`.
That archive and ignored donor clones are local to the original cloud session, not remotely
backed up. All tracked original art, Blender sources, textures, tests and evidence are preserved.

## Next priorities

1. Profile a representative real GPU and separate render, simulation and loading costs. Reduce
   delivered unused assets and measured draw/lighting/geometry costs while preserving source art.
2. Improve the actual first-person hands/weapon and reload choreography, then a properly rigged
   black-clothed character. Preserve Arsenal timing and individual asset licensing.
3. Finish Flat 01's bathroom/domestic materials and varied facade detail against the original
   references. More accessible homes require deliberate collision, nav and encounter work.
4. Human-playtest movement, aim, recoil, bot pressure and feedback; cover crowding/replanning at
   doors and stair transitions with meaningful regression scenarios.

Keep one coherent simulation and preserve useful work. Update the handoff and actual screenshots
after changes. Future publishing/deployment needs authorization for that task; this handoff
publication is not a request to deploy or merge unrelated branches.
