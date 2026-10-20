# Heron Reach — building construction, ground and planting

20 October 2026. The owner prioritised stairs and buildings, followed by more
convincing ground, growth, plants and trees. This continues the verified public
stair pass on `9adc2923233d3a95c6ba450a58093cdcb8a65830` (PR #18).

## Goal and scope

Make the estate read as constructed and maintained over time: connected stairs,
supported architectural details, credible building junctions and drainage, then
weathered ground with planting concentrated where it can grow. Retain the
South London blue-hour direction and the existing WWB game. Improve visible
construction rather than adding unrelated props to every open area.

Collision, navigation, door clearances and objective/spawn routes remain owned by
the existing simulation. New trees must correspond to existing trunk colliders
or sit outside the accessible site; small growth must not imply new solid cover.
Original Blender 5.2 sources stay intact. Additive sources use the available
Blender 4.3 CLI, metre scale and the existing material library.

The review sequence is building/stair construction first on
`codex/heron-reach-building-detail`, then ground/planting on a branch above it.
The building item is [PR #19](https://github.com/EmotiveImpact/Onsite/pull/19),
stacked on #18, pushed and unmerged. Each item records its actual exported costs,
matched runtime views and checks.
Real-GPU performance remains unverified and deferred. No merge or production
deployment was invoked. The repository's existing Vercel integration automatically
built a PR preview after the authorised branch push.

## Recovery

The clean starting revision is preserved by local ref
`checkpoint/onsite-before-building-ground-2026-10-20`. Existing sources, images,
tests and PR #18 remain available. Restore individual files from the starting
revision only after checking for later work; do not reset the shared checkout.

## Building implementation

The eight H2 maisonettes had full ceiling and upper-floor finish sheets crossing
otherwise valid private stair voids. The return flight had only about 0.54 m of
visible headroom at one sampled tread. Its solid physical central divider was
also invisible. An additive Blender model replaces the sixteen private flights,
144 exact treads, supported handrails, opaque dividers and guards. New finish
panels follow the real mirrored voids. Original landing slabs and home finishes
outside those precise sheets remain.

Doorway review also found render-only jambs and held-open leaves crossing
physically clear approaches. The narrow surrounds are moved outside their existing
openings; affected leaves are held against supporting walls. Actual Rapier capsule
clearance and combined old/new render geometry are checked together. No door
opening, collision box or route is moved to accommodate the artwork.

Exterior construction adds entrance surrounds, gallery fascia/coping joints,
window drip edges, drainage pipes with collars/brackets, column bearings and
supports attached to existing pendant positions. The exact source and provenance
record is [BUILDING-CONSTRUCTION.md](BUILDING-CONSTRUCTION.md). New surfaces reuse
existing PBR maps; there is no additional texture library or donor download.

The runtime retires narrowly selected old triangle indices only after replacement
geometry and materials load. It never overwrites the original architecture GLB.
A failed additive load retains the original scene. Public stair replacements from
PR #18 still compose with this layer.

## Evidence and validation

The code/asset checkpoint is `2608c6e`. Typecheck and production build pass. The
frozen build is `index-CjzkdkVd.js`, SHA256
`3be35f28f8e6ea788c0a65911df1375c77363fb4be22ac488fa8d312caf3b79e`.
The final additive model is **484,816 bytes / 35,344 triangles / 52 material batches**,
SHA256 `437d8c49fc2cb5cd00232d655d663f42718920181338b8e925b9d68dc829f8fa`.
Four of the batches carry entrance glass; this raises the initial 48-batch target
to 52 explicitly. Exact legacy retirement is **4,576 triangles**, so the net
addition is **30,768 triangles**. The old download and vertex attributes remain
available; their memory is not claimed as reclaimed. No new textures or lights.

All **100 tests pass** (10 retained legacy and 90 current), with no skips. Seven
construction groups decode the actual compressed geometry: all 144 private treads,
mirrored routes, full headroom and finish voids, visible physical dividers/guards,
supported leaves and clear standing door approaches. Fingerprints preserve the
original partitions, window glass outside the eight retired entry panes, frames,
landings and public architecture. Loader failure preserves the old scene.

All ten final building views loaded without page/console errors or failed requests.
The nine paired poses match the baseline exactly; the tenth is the ground pass's
north-boundary baseline. Intermediate iterations remain local under
`test-results/building-ground`; final images are archived below. Matched captures
use the same requested camera positions, 1280 × 720,
DPR 1 and Chromium/ANGLE SwiftShader. Bots remain active in inspection mode.
Private stair walks use the actual WWB player, Rapier and layered navigation with
one initial spawn and no subsequent teleport; these scripted fixtures disable bots.
Normal mouse/keyboard combat checks remain separate from both kinds of art evidence.

## Ground continuation

Implemented separately on `codex/heron-reach-ground-growth`: irregular bare soil,
moss at paving edges, small leaf drifts, low weeds, planting within existing raised
planters, sixteen additional perimeter trees and corrected grass blade winding.
That branch owns its own matched screenshots and regression checks; these building
captures intentionally show the preceding ground state.


## Matched building viewpoints

These are actual running-build captures, not concept art. Before and after use the
same requested pose and renderer settings. A tenth north-boundary view provides
the ground pass with its own baseline; it has no pre-building counterpart.
The [capture report](evidence/building-construction/after/report.json) records
served script/model hashes, renderer, actor state and draw submissions.

| View | Before | After |
| --- | --- | --- |
| Private stair entry | [Before](evidence/building-construction/before/private-stair.png) | [After](evidence/building-construction/after/private-stair.png) |
| Private dogleg and floor opening | [Before](evidence/building-construction/before/private-stair-turn.png) | [After](evidence/building-construction/after/private-stair-turn.png) |
| Public stair entrance | [Before](evidence/building-construction/before/stair-elevation.png) | [After](evidence/building-construction/after/stair-elevation.png) |
| Public stair interior | [Before](evidence/building-construction/before/stair-core.png) | [After](evidence/building-construction/after/stair-core.png) |
| Gallery construction | [Before](evidence/building-construction/before/gallery-edge.png) | [After](evidence/building-construction/after/gallery-edge.png) |
| Garden Court | [Before](evidence/building-construction/before/garden-court.png) | [After](evidence/building-construction/after/garden-court.png) |
| Washhouse Square | [Before](evidence/building-construction/before/washhouse-square.png) | [After](evidence/building-construction/after/washhouse-square.png) |
| The Corner | [Before](evidence/building-construction/before/the-corner.png) | [After](evidence/building-construction/after/the-corner.png) |
| Roof/skyline | [Before](evidence/building-construction/before/roof-skyline.png) | [After](evidence/building-construction/after/roof-skyline.png) |

## Run and reproduce

Use Node 24, `npm ci`, then `npm run dev`; open `/?map=heron-reach`. The plain `/`
route remains Heron Court. Use WASD/mouse, Shift to sprint, Space to jump, C to
crouch, RMB to aim, LMB to fire, R to reload and Escape to pause.

```sh
npm test
npm run typecheck
npm run build
npm run preview -- --port 4189
ONSITE_URL=http://127.0.0.1:4189 OUT=test-results/building-court node scripts/verify-encounter.mjs
ONSITE_URL=http://127.0.0.1:4189 OUT=test-results/building-reach node scripts/maps/verify-heron-reach.mjs
```

Run those production encounters serially. The private traversal HTML is a test-only
Vite fixture, so use the dev server for it:

```sh
ONSITE_URL=http://127.0.0.1:5184 HOME_ID=NW-H2-1 OUT=test-results/private-nw node scripts/maps/verify-private-stair-walk.mjs
ONSITE_URL=http://127.0.0.1:5184 HOME_ID=SW-H2-1 OUT=test-results/private-sw node scripts/maps/verify-private-stair-walk.mjs
```

Use `npm run dev -- --port 5184 --strictPort` for that example. Prefer serial runs
on a warm development server: an initial simultaneous cold start aborted Vite
module requests in the SW browser after completing all eight physical checkpoints.
The failed report is retained in
[initial-failures/private-sw-aborted.json](evidence/building-construction/initial-failures/private-sw-aborted.json).
Its page errors were empty; the strict request assertion failed. The unchanged
route then passed serially in 218 seconds with all ten assertions, no page errors
and no failed requests. No assertion was relaxed. The
[final SW report](evidence/building-construction/private-sw/report.json) records
eight grounded checkpoints and the complete +3 → +6 → +3 m traversal.

The [NW traversal report](evidence/building-construction/private-nw/report.json)
records eight grounded checkpoints, one initial spawn, 1,407 physics ticks and a
maximum capsule movement of 0.05668 m per tick. Its
[short descent clip](evidence/building-construction/private-nw/descent-software.webm)
is an unaltered stream excerpt from the software-rendered fixture, with bots
disabled. Full videos remain under `test-results/building-ground`; the reports'
original video filenames refer to those local files, not additional tracked media.

## Visible result and remaining work

The private entry now shows an open stair volume above the first flight; the
return view reveals the upper void and the solid centre divider instead of a
finish sheet across the player route. Rails have capped ends and supported wall
fixings. The gallery view shows the new window sill, fascia joints and drainage
against the existing architecture. The eight public cores retain the preceding
stair construction. The new floor holes are render corrections to existing
physical routes, not newly opened gameplay paths.

Private interiors are still dark and sparsely furnished. Local shadows, stronger
interior light response, varied finishes and room-aware culling remain necessary;
this construction pass does not establish finished visual quality. Calls rise
from 259 to 273 at private entry, 795 to 842 at the private turn, and 594 to 624
on the gallery. Inspection submits roughly 1.08–1.45 million triangles at those
views. These are observed draw costs, not a measured GPU frame-time comparison.

## Final normal-input encounters

Both production encounters passed serially against the frozen building build on
port 4189, with other browsers and heavy exports/tests stopped. All models and
materials loaded; pointer lock/look, aiming alignment, firing/reload, pause/resume,
jump/landing, combat, objective capture, exactly-once result persistence and reset
passed. The Court check also crosses its lobby doorway. Court defeats three bots;
Reach defeats six. Page/console errors and failed requests are empty in both reports.

| Encounter | Result | Mean / median / p95; active samples | Final calls / triangles |
| --- | --- | --- | --- |
| Heron Court | [10 checks](evidence/building-construction/court/report.json); 44 health; 46 shots / 14 hits | 478.01 / 467.70 / 608.70 ms; 127 samples | 84 / 266,993 |
| Heron Reach | [9 checks](evidence/building-construction/reach/report.json); 64 health; 63 shots / 32 hits | 687.22 / 677.40 / 895.30 ms; 360 samples | 473 / 1,281,384 |

Chromium uses ANGLE SwiftShader at 1100 × 700, DPR 0.5, with bloom disabled by the
software fallback. These timings include automation overhead and are roughly
1–2 FPS, not smooth play. They do not establish a hardware performance improvement.
**Real-GPU performance remains deferred and unverified.** Draw submissions, local
shadows/reflections, interior lighting, authored character motion and spatial sound
remain production work. No collision/navigation or WWB gameplay code changed.
