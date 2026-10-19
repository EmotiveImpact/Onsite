# ONSITE / Heron Reach — B01 blueprints

**17 dimensioned A1 drawing sheets for Claude to build in Blender.** This is the
technical development of the separate 144 × 120 m / 32-player map proposal. It
preserves the original placements and adds precise home walls, openings, stairs,
floor holes, elevations, assembly rules and coordinate schedules.

The current Heron Court playable and the earlier Heron Reach massing are unchanged.
This package is a proposed game environment modelling contract. It does not certify
32-player playability or represent a real-world construction project.

- **[Drawing book — PDF](ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf)** — 17 vector pages,
  searchable text and bookmarks. A1 landscape, 841 × 594 mm; print at **100%**.
- **[Claude build brief](CLAUDE-BUILD-BRIEF.md)** — start here when implementing.
- **[Blender guide file](../../../../assets/blender/maps/heron-reach-32-B01-guides.blend)**
  — new file; original model preserved. Ground visible initially; enable floor
  collections to inspect the upper levels and undercroft.
- [Browser drawing book](index.html) — select individual sheets; no dependencies.
- [Build specification](build-spec.json) — dimensions and module geometry in metres.
- [Home instances](home-instances.csv), [home openings](home-openings.csv),
  [public cores](core-instances.csv), [trees](tree-placements.csv),
  [lights](light-placements.csv), [cover](cover-placements.csv).
- [Coordination checks](coordination-check.json), [Blender guide checks](blender-guide-check.json),
  [drawing export checks](drawing-check.json), [package hashes](PACKAGE.json).

## Drawing index

| Sheet | Content | Printed scale at A1 |
| --- | --- | --- |
| B000 | Issue index, source hierarchy and coordinate conventions | 1:500 / NTS |
| B100 | Site setting-out, block origins, core schedule and grid | 1:250 |
| B101 | Ground floor, eight through flats, shops and initial placements | 1:250 |
| B102 | +3.00 galleries, bridge links and maisonette entrances | 1:250 |
| B103 | +6.00 upper homes and four separate landing islands | 1:250 |
| B104 | +9.00 accessible roofs, closed roofs and core overruns | 1:250 |
| B105 | −3.00 partial undercroft and four exits | 1:250 |
| B200 | Enlarged typical block: ground and gallery | 1:125 |
| B201 | Enlarged typical block: upper homes and roof | 1:125 |
| B300 | H1 through flat, clear room sizes, furniture and opening schedule | 1:25 |
| B301 | H2 lower/upper plans, private stair, exact upper slab opening | 1:50 / 1:25 |
| B302 | Public stair plan, unfolded section, risers and landings | 1:25 |
| B400 | Home front/rear elevations, 3 m facade bay and component schedule | 1:50 / 1:25 |
| B401 | Building/core section, levels, slab edge and opening dimensions | 1:100 / 1:25 |
| B500 | Shop and service shells, portals, court fence and gates | 1:100 |
| B600 | Coordinated planting, dirt/wetness and light positions | 1:250 |
| B700 | Blender collections, pivots, material families and ground detail | 1:25 / NTS |

Every sheet has a same-name SVG and PNG. SVG/PDF carry the physical print scale;
PNG is a screen preview. Dimensions govern over image measurements. The floor-plan
grid is 12 m; facade subgrid is 3 m. Home room sizes are **clear between wall faces**.

## What changed from the earlier proposal

This issue keeps `../map.json` unchanged and pins its SHA-256. Its site placements
remain authoritative. `build-spec.json` now governs the detailed modules; it
supersedes the earlier schematic home subdivisions and massing builder details.

- Shells are 200 mm, partitions 120 mm, slabs 200 mm below finished floor. The
  nominal 1.50 m home hall is now explicitly clear after accounting for walls.
- H1 exterior door centres move 0.20 m within the same hall to leave usable jambs.
  The old abstract route endpoint still lies inside the opening; capsule clearance
  must be checked again when the runtime route is built.
- Public/private stairs use **10 risers and 9 goings per half-flight**. The tenth
  rise ends on the landing. Each flight runs 2.52 m, and each storey rises 3.00 m.
- H2 has one lower front entrance and one upper rear exit. Its upper slab opening
  stops before the full-level landing. Southern stairs and holes mirror together.
- Common concourses, rear landings and reserved service strips are identified
  within the broad block floor plates. Six shop shells have explicit doors.
- The top public core cap is 2.80 m above its highest served floor. There is no
  extra flight above the last floor and no playable route across that cap.

The guide `.blend` contains **1,757 mesh objects and 250 opening-label empties**:
unioned floor guides with holes, home walls with real apertures, corrected public
and private stairs, public-core walls/caps, shop shells, reserved strips and cover
guides. It uses solid guide materials. It intentionally omits final guards, common
hall facade kits, undercroft perimeter walls, landscape and lighting; the drawings
and brief specify that work. It is not a finished environment or a runtime GLB.

## Verification

**169 offline coordination checks passed.** These include room/door dimensions,
non-overlapping openings, mirrored placement, stair arithmetic and slab openings.
A 0.35 m radius body was sampled on a 0.10 m 2D grid through each home type, with
the planned furniture: all 16 room areas across the three module plans and the
required exits/landings were reachable. Furniture clears the planned door sweeps.
This is a design clearance check, not a 3D Rapier capsule simulation.

The actual Blender guide was inspected at **144 home doorway/arch centres**;
none was inside a built wall solid. This checks real generated apertures but does
not establish their complete capsule clearance or the stair headroom sweep.

The exported drawing viewer passed all 17 page selections, a 390 px width check
and sheet-edge text checks with no page errors. The final PDF has 17 physical A1
pages, 17 bookmarks, searchable text and vector paths. It is not a raster screenshot
book. The earlier 46 site-route design checks are retained in `../validation.json`;
they were not extended into a new runtime playtest here.

Remaining implementation verification: actual capsule movement/headroom, complete
route widths through shared spaces, floor-aware bots, spawn visibility, human
combat balance, 32-actor load and real-GPU performance. No game test result or old
frame-time report is presented as validation of this larger map.

## Rebuild this package

Run from the repository root. Python 3, Node with the existing Playwright dependency,
Chromium, PyMuPDF, Ghostscript and Blender 4.3.2 were used in this workspace.

```sh
python3 scripts/maps/make_heron_blueprint_spec.py
python3 scripts/maps/draw_heron_blueprints.py
python3 scripts/maps/validate_heron_blueprints.py
node scripts/maps/export_heron_blueprints.mjs
blender -b --python-exit-code 1 --python scripts/maps/build_heron_blueprint_guides.py
python3 scripts/maps/package_heron_blueprints.py
```

The guide builder writes **only the new B01 guide filename**; rerunning it replaces
manual edits in that file. Make an authored working copy before editing. The older
`heron-reach-32.blend` and the active `onsite-heron-court.blend` are not touched.
The packager refreshes hashes and writes an ignored transfer ZIP under
`test-results/blueprints/`. It includes repository-relative paths and a start file.

All new drawings, module geometry and scripts are original ONSITE work. No donor
assets were imported for this technical package. Existing runtime asset notices
and the original London references remain authoritative for later art work.
