# ONSITE — Heron Reach / 32-player map design

**Design target: 32 players, initially 16v16.** A separate 144 × 120 metre South London estate,
with five planned height levels and three contested places. This package does not replace the
current Heron Court playable or Claude's visual work. It does not implement networking or claim
that 32-player balance/performance has been proved.

The original ONSITE courtyard, walkway and corner-shop images were visually inspected. Their
blue-hour sky, warm thresholds, rain-darkened ground, stock brick, concrete galleries, planting
and recognisable local shops guide this design. References remain in `docs/concepts/`; these
drawings and the Blender model are new original ONSITE design work, not donor map copies.

## Review the map

- [Nine-sheet PDF](ONSITE-HERON-REACH-32.pdf) — share this with Claude for design review.
- [Interactive drawing book](index.html) — open locally in a browser; switch floors and toggle
  routes, cover, planting, wet ground and lighting intent. No external dependencies.
- [Masterplan](00-masterplan.png) · [ground](01-g.png) · [gallery +3 m](02-l1.png) ·
  [upper homes +6 m](03-l2.png) · [roofs +9 m](04-r.png) · [undercroft −3 m](05-b1.png).
- [Home layouts](06-homes.png) · [landscape and lighting](07-landscape-lighting.png) ·
  [sections](08-sections.png). Every plan also has a same-name editable SVG.
- [Blender design model](../../../assets/blender/maps/heron-reach-32.blend) ·
  [massing GLB](heron-reach-32-massing.glb) · [Blender overview render](09-blender-massing.png).
- [Metric definition](map.json) · [coordination checks](validation.json) ·
  [viewer checks](viewer-check.json) · [Blender build record](blender-build.json) ·
  [GLB dimensions check](model-check.json) · [artifact hashes](PACKAGE.json).

The Blender overview is a **design massing render** with material, window, foliage and light
proxies. It is not an in-game screenshot or the requested final visual fidelity. The model uses
real metre dimensions and stair treads; it remains separate from the playable's collision/nav.

## Structure and height

| Level | Height | Proposed playable areas |
| --- | ---: | --- |
| B1 | −3 m | Partial undercroft loop and a dogleg cross-link; exits through S2, S3, S6 and S7. |
| G | 0 m | Garden Court, The Cage, Washhouse Square, public arcades, shops/community rooms and eight through flats. |
| L1 | +3 m | Continuous 3 m gallery loop, two 24 m bridge links and eight maisonette entrances. |
| L2 | +6 m | Four separate home/landing islands and maisonette upper floors. No upper cross-court bridge or floating floor. |
| R | +9 m | Rowan and Cedar roof terraces only, two public stair exits on each. Ash/Birch roofs are closed. |

The eight public cores are 6 × 6 m. Each 3 m rise has 20 × 0.15 m risers, 0.28 m goings and
1.5 m flights/landings. External gallery landings wrap the cores, leaving openings above the
flights and half landings; south cores mirror their stair direction toward the matching entrance.
The design clearance target is 2.4 m. Final slabs, rails, thresholds and collision must be checked
with the existing WWB capsule before art detail is accepted.

Map coordinates are metres: x increases east, z increases south, origin at the north-west corner,
y is elevation. All plans point north upward. The Blender conversion is `(x − 72, 60 − z, y)`;
GLB export changes Blender Z-up to Three.js Y-up. Sections identify their exact map cut lines.
The B1 plan is partial: grey/hatching is context, not a floor at that height.

## How it should play

**A / Garden Court:** low planters, scattered trees, rear lanes and home exits. The planted north
route favours movement between short sightline breaks. Low shrubs provide texture and some
concealment, while masonry planters provide dependable hard cover.

**B / The Cage:** a 30 × 20 m multi-use court with four gates, low cover and two opaque screens.
It is the most exposed capture area, with visible gallery pressure. It is reached fastest, but
the two other objectives and the undercroft prevent every fight from depending on this space.

**C / Washhouse Square:** a close service square between the washhouse and estate office,
connected to the corner shop, youth room and southern flats. This is the intimate, noisy route
with doorframes, service corners and warm shop spill.

Three main route families let a 16-person side distribute roughly 5 / 6 / 5 players. That is a
design assumption, not an enforced team assignment. Cross-links let small groups change route
without retreating all the way to their start. Primary circulation aims for 4 m; galleries 3 m;
secondary lanes 2.4 m. Private homes deliberately have narrower 1.5 m halls and 1.1 m doors.

| From either staging centre | Planned shortest distance | Walk at 4.6 m/s | Sprint at 6.8 m/s |
| --- | ---: | ---: | ---: |
| Garden Court | 100 m | 21.74 s | 14.71 s |
| The Cage | 82 m | 17.83 s | 12.06 s |
| Washhouse Square | 100 m | 21.74 s | 14.71 s |

These are centreline distances through the design graph. They exclude acceleration, opening
doors, aiming, congestion, combat and human decisions. Equal distances are a useful starting
constraint, not proof that sides have equal visibility or win rates. The active game's speed
values must be checked again when the blockout is integrated.

## Sneaking, counterplay and spawn safety

- Eight H1 flats provide front-to-rear passage without forcing players through a bedroom or bath.
  Eight H2 maisonettes connect the +3 m gallery to the +6 m rear landing by private stairs.
- The undercroft provides a slower hidden route and four exits. No required crouch tunnels,
  ladders, one-way drops or dead-end public routes. Rooms off circulation may be optional dead
  ends; do not place compulsory objectives in them.
- Public stairs and warm entrance pools expose transitions. Gallery privacy panels, shop returns
  and service screens break long views. Keep useful close views around 8–25 m, medium views
  around 25–40 m, and treat longer views as intentional exceptions to verify in the blockout.
- Roofs have no capture objective. Plant rooms and opaque screens split their view; spawn-facing
  rear walls remain opaque. Do not add new overlooking windows during the visual pass without
  checking the opposing starts and exits.
- Stealth uses sightline breaks, timing and surface sound. Characters in black clothing must
  remain readable against dark corners. Avoid making shadow quality or foliage graphics settings
  determine whether an opponent is visible. Leaf cards never substitute for authoritative cover.
- The 32 marked positions are **initial staging placements**, not a respawn algorithm. Each
  side has three exit branches, with an offset central exit and sight screens. Runtime spawning
  still needs enemy proximity checks, multiple candidate anchors, line-of-sight rejection,
  occupied-position checks and a fallback when the preferred area is contested.
- Capture volumes must be floor-aware. An actor on the gallery above a ground capture area must
  not count as standing in it. No side-switch, scoring or spawn rules were added to the game here.

## Homes and usable frontage

H1 is a 9 × 8 m gross one-bedroom through flat, with kitchen, living/dining, bathroom/utility
and a cross hall. H2 is a 9 × 8 m gross two-bedroom maisonette across two floors, 144 m² total.
It has a kitchen/living lower floor, upper bedrooms/bath, central clear hall and a 1.2 m private
stair. These are intentionally generous gameplay layouts, not surveys of actual council flats.
Wall finishes and furniture will reduce net areas. Door swings, appliance clearance and room
details need reconciliation during modelling.

The ground sheet places eight H1 units; +3/+6 sheets place eight H2 units. Southern instances
flip their entry direction so lower entrances face their gallery and upper exits face the rear.
Brown block area outside the specified home and circulation modules reserves facade/services;
it is not a promise that every anonymous door or window opens. The massing floor plates are broad
coordination surfaces, not finished walk polygons or a room-level collision specification.

Repeat structural kits while varying occupancy clues: curtains, lamps, kitchen colours, drying
racks, mats, notices and wear. Keep the building silhouette and address numbering consistent.
Homes should feel inhabited without furnishing away the movement clearance.

## Landscape, dirt, materials and light

The separate landscape sheet coordinates **20 tree placements, ten grass/soil zones, seven wet
patches, twenty light-intent positions and five detail zones**. Large forms stay identical across
quality settings; blades, leaves and scraps are visual detail.

| Layer | Treatment | Gameplay / technical constraint |
| --- | --- | --- |
| Ground | Worn paving, rain-dark asphalt, slab edges, wheel tracks, dirt at drains | Keep 4 m primary routes and stair approaches readable; puddles do not change collision. |
| Trees | Plane/birch forms, 2.7 m clear canopy base, defined trunk collision | Low-poly collision trunk; multiple foliage LODs; avoid alpha overdraw walls. |
| Grass / soil | Grass seams, bed edges, root heave, low planting, leaf litter | Shrubs below 0.7 m near main routes. Clear paths through planted edges remain visually legible. |
| Rubbish | Receipts/crates at shops, bags at bin bays, leaves under trees | Small scraps do not collide. Large bins/containers need measured static colliders. |
| Weathering | Moss on shaded concrete, rain trails below sills, rust below fixings | Reuse dirt/wetness masks and decal atlases; do not paint uniform grime everywhere. |
| Light | Cool blue-hour ambient, 2700 K entrances/shops, 3000 K court | Circles show intention, not lux. Prioritise doorway/stair readability and visible black outfits. |

Start from six shared material families: stock brick, concrete, asphalt, paving, painted metal,
soil/grass. Use the existing credited PBR inventory where appropriate and preserve source
provenance. Original generated colour candidates need seamless-repeat and lighting-neutrality
checks before becoming full PBR sets. Normal/roughness maps must describe the same actual
surface, not generic noise added to every material. Keep full source images out of runtime.

Review-only Blender lamps do not become Three.js lights. Use emissive fixtures plus baked/local
ambient treatment for most of the twenty intentions; select a small measured subset of real-time
lights. Lighting and ground wetness need to be tuned together so the centre stays readable rather
than becoming a mirror. A matched camera/lighting test against the original reference should
precede modelling hundreds of tiny props.

## Runtime budgets to measure, not claims

The existing small playable measured about 1.7 FPS in cloud SwiftShader. This larger design has
**not** been integrated or profiled. A 32-player design cannot inherit a smooth-performance claim
from screenshots or graph checks.

For a chosen representative desktop GPU, start with a 60 FPS / 16.7 ms frame target at 1080p;
measure CPU simulation and GPU rendering separately. Initial budget hypotheses: under 200 visible
draw calls, 1.5 million visible triangles including actors, 256 MB texture residency, and under
25 MB compressed initial playable download. Revise them from actual measurements, especially
foliage overdraw, skinned avatars, point lights and shadows. They are not measured results or
universal browser limits. Keep doors/rooms, static architecture, props and vegetation in spatial
chunks; instantiate repeated pieces and use LODs. Do not export the design GLB wholesale as the
shipping level: it favours editable objects over runtime batching.

## Checks actually run

[validation.json](validation.json) records **46 passed design checks**, 127 route nodes, 189 edges
and 6,293 sampled upper/service route points. Checks cover unique IDs, connectivity,
all-floor reachability with any one public stair's flights blocked, four graph approaches per
objective, 16 separated placements per side, route bounds, stair dimensions, home placement,
floor presence under sampled routes, avoidance of stair voids on upper horizontal routes, and
0.35 m centreline clearance from planned hard cover/trunks.

These checks caught cover intersecting perimeter paths and home-to-stair approaches; the
placements/routes were adjusted. Coordination review also moved homes clear of the rear landing
and wrapped upper circulation around stair openings rather than placing a slab over the half
landing. They do not substitute for capsule collision, complete route
width checks, correct rail openings, line-of-sight tests or a real navmesh. The graph does not
simulate 32 moving actors, player preferences, bullets, sound propagation or network latency.

The standalone book passed nine page selections, five layer toggles and a 390 px overflow check,
with no page errors. Nine PNGs and a nine-page PDF were exported through Chromium. The active
gameplay code, dependencies, existing art and its previously reported test results are unchanged;
existing gameplay tests are not evidence that this new map is playable.

The Blender model has 1,602 editable mesh objects; the 2.09 MB design GLB contains 21,544
triangles. Its exported bounds verify a 144 × 120 m footprint, with the undercroft below ground
and roof screens above +9 m. No lights, camera or external images are required by that GLB.
The overview was rendered in Cycles on CPU at 64 samples without denoising; this Blender build
does not include OpenImageDenoise. These are offline design artifacts, not game performance results.

## Claude implementation handoff

Continue the WWB/ONSITE runtime already on main. Do not replace its controller or add a second
physics/nav owner. Keep this map as an **additional selectable level** while the small Heron Court
encounter remains the regression baseline. Do not expand networking as part of this design task.

1. Review the PDF, metric JSON and Blender model with the original references. Keep the model's
   level/guide collections separate. Check for newer Claude work before changing shared code.
2. Produce authoritative collision solids for this level and layer-aware navigation using the
   current single Rapier world. Start with the ground plus both ends of one gallery loop; then
   public stairs, undercroft, homes and roof limits. Preserve the 6 m stair footprints and meter
   coordinates. Design route curves are guides, not a replacement nav system.
3. Walk every route with the actual capsule. Test ascent/descent, headroom, rail openings, window
   bounds, falls, door widths and both exits of every home. Add sightline rays from roofs/galleries
   to spawn positions and exits. Record fixes in `map.json`, then regenerate the plans.
4. Start with 8v8 bot occupancy, then 12v12 and a 32-actor stress scene. Test doorway queues,
   stairs, separation, replanning and ground-aware objectives. This tests local simulation load,
   not online multiplayer. Keep capture/spawn changes isolated from presentation.
5. Human-playtest which routes are used and where fights stall before completing art. Collect
   spawn-to-contact times, deaths soon after spawn, objective pressure, route occupancy and
   upper-floor dominance. Equal graph distances do not establish fair match outcomes.
6. Build one finished street/gallery/home composition against the reference lighting, measure it
   on a real GPU, then repeat the proven asset kit. Preserve individual donor licences/notices.
7. Update evidence with actual runtime frames and frame-time measurements. Keep concept artwork,
   diagram exports, Blender previews and game screenshots clearly identified.

## Rebuild this design package

Run from the ONSITE repository root; Node/Python/Blender, Chromium and Ghostscript are already present in the
current cloud session. No new npm dependencies or setup configuration were needed.

```sh
python3 scripts/maps/validate_heron_reach.py
python3 scripts/maps/draw_heron_reach.py
node scripts/maps/export_heron_reach.mjs
blender -b --python-exit-code 1 --python scripts/maps/build_heron_reach_blender.py
```

`map.json` is the editable metric source. The drawing script emits SVGs/HTML; the browser export
emits PNG/PDF. The Blender builder creates only `assets/blender/maps/heron-reach-32.blend` and its
design exports here. It starts an empty Blender scene and replaces that specific design file;
save manual edits separately before rerunning it. It does not touch
`assets/blender/onsite-heron-court.blend` or anything in `src/` or `public/`.

In Blender, hide `00_SITE` to inspect the undercroft. Toggle floor collections for cutaways;
`08_ROUTE_GUIDES` is hidden by default and omitted from the GLB. The GLB contains render/massing
geometry only. Physics, production nav and lights require explicit runtime integration. All
new geometry/material proxies are original procedural ONSITE work; existing donor licences and
reference clones are unaffected.
