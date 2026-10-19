# South London gap-fill assets for Heron Reach

Props the main build's kits did not already cover, built by the project's South London research thread from its reference guide (kept in the project's shared files, `south-london/research/south-london-estate-reference.md`). This folder holds the editable `.blend` sources and the `build_*.py` scripts (run with `python3`, needs the `bpy` 5.2 package). The game loads meshopt-compressed copies from `public/models/heron-reach/heron-reach-sl-{signs,lights,structures,extras}.glb`, and `src/onsite/heronReachDressing.ts` places them.

## Conventions (until the main build's CONVENTIONS.md replaces them)

- Metres. Blender Z-up in source, glTF Y-up on export.
- Ground items: origin at base centre. Wall items: origin at back centre, front faces -Y in Blender (+Z in glTF/Three.js). Ceiling items: origin on the ceiling face. Run items (conduit, tray, pipes) run along +X.
- Names: `hr_prop_<thing>[_<variant>]`, `hr_decal_<thing>`, materials `mat_<surface>`.
- Shared surface materials carry no textures so the build can swap in its PBR sets by name: `mat_brick_london_stock`, `mat_brick_red`, `mat_concrete_cast`, `mat_roof_felt`, `mat_steel_black_painted`, `mat_galvanised_steel`. Their UVs are world metres (1 UV = 1 m); a source-30 tile covering 2 m needs repeat 0.5.
- Textures are only embedded where they are unique to the kit (sign atlas, numerals, hazard stripes).

## Kits

| Folder | File | Tris | Contents |
| --- | --- | --- | --- |
| `signs/` | `hr_prop_signs_kit.glb` | 760 | 30 estate signs on one atlas (estate board, block names, NO BALL GAMES, dogs, fly tipping, private parking, CCTV, anti-climb paint, danger of death, fire exit, fire door, dry riser, bins day, garage boards, level plates, max headroom, lobby note, notice board paper, flat numbers) plus 8 painted level numeral decals (G, 1 to 4, B1, G1, R). Placement per sign in `textures/hr_sign_atlas_layout.json`. |
| `lights-services/` | `hr_prop_lights_services_kit.glb` | 2.1k | Fluorescent batten (normal, twin, dead), round bulkhead (warm, cool), caged underpass wall lamp, conduit runs and riser, cable tray, ceiling pipes, dry riser inlet and landing valve, satellite coax drop. |
| `structures/` | `hr_prop_structures_kit.glb` | 4.2k | Bike hangar (Lambeth spec, 2.55 x 2.03 x 1.37 m), 3-bay bin store with hit-and-miss brick and galvanised gate leaf, substation with louvred doors, palisade fence panel (galvanised, green), lock-up garage bay and end wall, garage doors in green, blue, white, rust and raised-open. |
| `security-carpark-extras/` | `hr_prop_security_carpark_extras_kit.glb` | 2.9k | Window grilles (white, black), flat door security gate, void sheets for window and door, pigeon spikes, hazard column wrap, wheel stop, height barrier, rubber speed hump, grit bin, drying-area posts, clothes airer with washing, dumped sofa, dumped CRT TV, pallet, nitrous oxide canister litter. |

## Placement notes

- Garages: the bay origin is the centre of the front opening at floor level; bays repeat every 2.6 m along +X, close the row with `hr_prop_garage_end_wall`. Doors sit in the opening at the same origin.
- Bin store gate leaf: origin at the hinge side, base. Put one at each end of the store front (x = ±1.47 m, y = -0.85 m from the store origin), mirror the right one, and swing one open 20 to 40 degrees.
- Bike hangars go on the road edge in half a parking bay, door side facing the pavement, one or two per street.
- Substation: on a corner of the car park or by the garages, with the palisade fence 1 to 2 m off it and the danger sign on the doors.
- Hazard wraps on every undercroft car park column; wheel stops at the back of each bay; height barrier at the car park entrance with the max headroom sign on the bar.
- Window grilles and void sheets on ground floor flats only; one or two void sheets per block reads as real.

## Licences

All geometry and textures here are original to this project. Sign text was rasterised with Inter (SIL Open Font Licence) and DejaVu Sans; no font files are shipped. All names, phone numbers and wording are fictional.
