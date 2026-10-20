# Heron Reach — constructed public stairs

20 October 2026. Continuing the [whole-game goal](../../../ONSITE-GOAL.md).
Branch: `codex/heron-reach-stair-construction`, based on the complete player-flow
review tip `5d381091d3fad2a42a648923cce62c390a350b38` (PR #17).
Review: [PR #18](https://github.com/EmotiveImpact/Onsite/pull/18), stacked on #17;
pushed for review, not merged or deployed.
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

Final code/asset source is `8c08fad`; its runtime JavaScript is unchanged from
`5ac9298`. Subsequent commits add evidence and documentation.
The frozen production script is `index-BqdiVh_h.js`, SHA256
`1e047cbc2820b224501afbbd93cd84e6809ab528e1df9c35613e3ef60ae73059`.
The new model is **405,636 bytes, 29,904 triangles, 28 material batches**, with no
embedded textures or lights. Its hash is
`dd8c0896c64c5e2852a3a62cc98afa690d7ebd54243b7fd5eca4831ba1514be2`.
Removing the 35,072 old triangles gives a net reduction of **5,168 rendered triangles**.
The original download and vertex attributes remain: this is not a claim that all
their memory has been reclaimed. The additive draw batches can still increase calls.
The editable 3,586,994-byte Blend packs its 15 existing PBR source images.

The same S1 inspection view records **334 → 340 draw calls** and
**1,206,825 → 1,201,861 rendered triangles**. The gallery view records
**576 → 592 calls** and **1,328,088 → 1,319,848 triangles**. These are actual
frame counts with active actors, not a frame-time improvement claim. Estimated
architecture texture mip allocation remains **328,996,233 bytes**, using the same
82 WebP textures on SwiftShader. The still-large indoor submission count is evidence
for future room/portal culling and asset budgets, not a solved performance problem.

- **93 tests passed**: ten retained legacy and 83 current tests, no skips.
  The six construction groups decode the actual shipped meshes. They check all
  432 tread surfaces, clear standing routes/headroom, mirrored rails and opaque
  separators, plus preservation of landing faces, walls and private stairs.
  Three lighting groups cover 384 standing/crouched route samples across all cores.
- Typecheck and production build pass. The build retains its large-chunk warning:
  roughly 5.38 MB main JavaScript / 1.96 MB gzip. No new dependencies.
- Eight matched before/after inspection views pass with no page, console or failed
  asset requests. Requested camera poses are programmatically compared. These are
  **1280 × 720, DPR 1, Chromium/ANGLE SwiftShader** inspection captures; bots remain
  active. They are not gameplay or real-GPU performance evidence.
- Review caught the rain renderer's exterior orange proxies selecting indoor strips.
  Core lights are now omitted from those proxies, as well as outdoor glow/streak cards;
  actual warm-neutral indoor illumination remains in the existing light pool.
- Close image review caught raised panel seams hiding the inner rail at crossings.
  Recessed seam notches preserve the continuous opaque backing sheets. New first-hit
  rays reproduce the old defect and check that the rail stays visible on every flight
  and landing. Corner rail ends correctly enter their support posts by 42 mm;
  tests check the joint and exposed rail outside the post, rather than requiring a
  view through the support. The initial S1 walk passed before this cosmetic correction; final
  evidence is captured again against the corrected asset.

Raw [tests](evidence/stair-construction/tests.log),
[typecheck](evidence/stair-construction/typecheck.log),
[build](evidence/stair-construction/build.log) and
[after capture report](evidence/stair-construction/after/report.json) are retained.
Baseline reports: [core/exterior/gallery](evidence/stair-construction/before/report-core.json)
and [route viewpoints](evidence/stair-construction/before/report-routes.json).
The frozen baseline is the prior `3284c4d` runtime, unchanged at the `5d38109` review tip.

| Same requested viewpoint | Before | After |
| --- | --- | --- |
| S1 first flight | [Before](evidence/stair-construction/before/stair-core.png) | [After](evidence/stair-construction/after/stair-core.png) |
| S1 entrance elevation | [Before](evidence/stair-construction/before/stair-elevation.png) | [After](evidence/stair-construction/after/stair-elevation.png) |
| Gallery edge | [Before](evidence/stair-construction/before/gallery-edge.png) | [After](evidence/stair-construction/after/gallery-edge.png) |
| S1 half landing / return flight | [Before](evidence/stair-construction/before/stair-turn.png) | [After](evidence/stair-construction/after/stair-turn.png) |
| S1 underflight | [Before](evidence/stair-construction/before/stair-underflight.png) | [After](evidence/stair-construction/after/stair-underflight.png) |
| Mirrored S5 first flight | [Before](evidence/stair-construction/before/stair-south.png) | [After](evidence/stair-construction/after/stair-south.png) |
| S2 basement | [Before](evidence/stair-construction/before/stair-basement.png) | [After](evidence/stair-construction/after/stair-basement.png) |
| S1 top landing | [Before](evidence/stair-construction/before/stair-top.png) | [After](evidence/stair-construction/after/stair-top.png) |

Both continuous browser stair routes pass against the final asset. Each uses one
initial spawn, the real WWB player, Rapier and layered navigation, then scripted
steering without teleporting. Opponents are explicitly disabled. All seven checkpoints
are grounded: entry, first flight, half-landing turn, return flight, upper landing,
descending half landing and original entry. This is physical-route evidence, not
normal-input combat evidence.

| Fixture | Physical route | Ticks | Largest per-step displacement | Result |
| --- | --- | --- | --- | --- |
| [S1 report](evidence/stair-construction/walk-s1/report.json) | 0 → +3 → 0 m | 1,513 | 0.05618 m | Nine checks; returned to y=0.017 m |
| [Mirrored S7 report](evidence/stair-construction/walk-s7/report.json) | −3 → 0 → −3 m | 1,487 | 0.05649 m | Nine checks; returned to y=−2.980 m |

The final routes ran concurrently with each other on SwiftShader, 1280 × 800 at the
normal DPR 0.5 fallback. Their raw timing fields include contention and capture
overhead; they are **not** the performance sample. The serial production encounters
below supply that sample. Both routes have zero page/console errors or failed requests;
the only warnings are existing Three.js deprecations for `Clock` and `RGBELoader`.

Both production encounters passed **serially**, after the route fixtures and with no
Blender/test/encoding work running alongside them. They use normal mouse/keyboard
input, 1100 × 700 at the normal DPR 0.5 software fallback. Both load the actual rifle
and hands, align ADS, fire/reload, pause/resume, jump/land, defeat every opponent,
capture, persist one completed result and reset. No page/console errors or failed
requests occurred. Gameplay/physical/nav files remain identical to `5d38109`.

| Production encounter | Result | Mean / median / p95 frame time | Final render counts |
| --- | --- | --- | --- |
| [Heron Court report](evidence/stair-construction/court/report.json) | Ten checks; three bots; 84 health; capture/reset | 457.15 / 452.00 / 591.90 ms; 120 samples | 71 calls; 249,913 triangles |
| [Heron Reach report](evidence/stair-construction/reach/report.json) | Nine checks; six bots; 88 health; capture/reset | 622.24 / 599.30 / 819.10 ms; 360 samples | 441 calls; 1,246,752 triangles |

The means correspond to approximately **2.19 FPS Court / 1.61 FPS Reach**, including
automation/capture overhead. These are slow software runs, not evidence of smooth
play or an attributable speed-up. **Real-GPU performance remains unverified.**
The original 32-player design remains a bots-first playable, not an online service.

[Full S1 physical walk](evidence/stair-construction/video/walk-s1.webm) ·
[Full mirrored S7 physical walk](evidence/stair-construction/video/walk-s7.webm) ·
[Reach combat/capture excerpt](evidence/stair-construction/video/reach-closing.webm).
Videos preserve wall-clock speed; sharing copies are reduced to 960 × 600 / 10 FPS.
Their [encoding manifest](evidence/stair-construction/video/manifest.json) records
source/output hashes, durations and commands. Full original recordings remain in
ignored `test-results/stair-construction/`. Route clips are scripted, bots-disabled
fixtures; the Reach clip is actual normal-input combat evidence.

## Reproduce and recover

```sh
npm ci
npm run dev                           # open /?map=heron-reach; / is Heron Court
npm test
npm run typecheck
npm run build
npm run preview -- --port 4173
```

Run browsers serially against that production preview:

```sh
ONSITE_URL=http://127.0.0.1:4173 node scripts/verify-encounter.mjs
ONSITE_URL=http://127.0.0.1:4173 node scripts/maps/verify-heron-reach.mjs
```

The physical stair fixture runs against Vite dev and is explicitly labelled scripted
steering with bots disabled. It uses the existing player, Rapier and layered navigation:

```sh
ONSITE_URL=http://127.0.0.1:5173 CORE=S1 BASE=0 node scripts/maps/verify-stair-walk.mjs
ONSITE_URL=http://127.0.0.1:5173 CORE=S7 BASE=-3 node scripts/maps/verify-stair-walk.mjs
```

Saved inspection poses are in `scripts/maps/art-review-views.json`. Use
`scripts/maps/capture-art-review.mjs` with `QUERY='&dpr=1'`, an `OUT` directory and
`VIEWS=stair-core,stair-elevation,gallery-edge,stair-turn,stair-underflight,stair-south,stair-basement,stair-top`.
Set `EXTRA_ASSETS=/models/heron-reach/stair-detail.glb` to record the model hash.

To inspect or recover the previous implementation without overwriting current work:

```sh
git worktree add ../Onsite-before-stairs checkpoint/onsite-before-stair-construction-2026-10-20
# The portable equivalent is: git worktree add ../Onsite-before-stairs 5d381091d3fad2a42a648923cce62c390a350b38
```

The new Blender source is additive. Do not open or resave the original Blender 5.2
estate files with this machine's 4.3 CLI. See the construction record for the scoped
rebuild command and source/texture provenance.

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
