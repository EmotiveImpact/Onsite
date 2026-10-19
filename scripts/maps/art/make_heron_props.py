"""Build the Heron Reach street furniture and props kit.

Run from the repository root:
    python3 scripts/maps/art/make_heron_prop_textures.py   # textures first
    python3 scripts/maps/art/make_heron_props.py           # kit .blend + manifest
Optional: --only NAME[,NAME] builds a subset into a scratch file (no manifest).

Writes assets/blender/heron-reach/props-kit.blend (images packed) and
assets/blender/heron-reach/props-manifest.json. Every mesh is generated here
from code; nothing is imported. The build is deterministic.
"""

import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

import heron_props_lib as L  # noqa: E402
import heron_props_materials as M  # noqa: E402
import heron_props_street as street  # noqa: E402
import heron_props_cage as cage  # noqa: E402
import heron_props_shop as shop  # noqa: E402
import heron_props_litter as litter  # noqa: E402
import heron_props_vehicles as vehicles  # noqa: E402

OUT_BLEND = os.path.join(ROOT, "assets", "blender", "heron-reach", "props-kit.blend")
OUT_MANIFEST = os.path.join(ROOT, "assets", "blender", "heron-reach", "props-manifest.json")

GROUPS = [
    ("HR_PROPS_STREET", street.BUILDERS),
    ("HR_PROPS_CAGE", cage.BUILDERS),
    ("HR_PROPS_VEHICLES", vehicles.BUILDERS),
    ("HR_PROPS_SHOP", shop.BUILDERS),
    ("HR_PROPS_LITTER", litter.BUILDERS),
]


def set_backface_culling(objects):
    """Cull back faces on every material whose faces are closed in all objects using it.

    Materials on open sheets (nets, wire mesh, single-skin panels, alpha cards) stay
    double-sided. Returns the sorted list of double-sided material names.
    """
    import bmesh
    open_mats = set()
    used = set()
    for ob in objects:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        slots = [ms.material.name if ms.material else None for ms in ob.material_slots]
        for f in bm.faces:
            name = slots[f.material_index]
            used.add(name)
            if name in open_mats:
                continue
            if any(len(e.link_faces) < 2 for e in f.edges):
                open_mats.add(name)
        bm.free()
    for m in bpy.data.materials:
        if m.name not in used:
            continue
        alpha = m.node_tree and m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].is_linked
        blended = getattr(m, "surface_render_method", "") == "BLENDED"
        m.use_backface_culling = not (m.name in open_mats or alpha or blended)
    return sorted(m.name for m in bpy.data.materials if m.name in used and not m.use_backface_culling)


def main(argv):
    only = None
    out_blend = OUT_BLEND
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    if "--out" in argv:
        out_blend = argv[argv.index("--out") + 1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    mats = M.build_all(ROOT)
    root_col = bpy.data.collections.new("HERON_PROPS")
    scene.collection.children.link(root_col)
    manifest = {
        "kit": "heron-reach-props",
        "blend": "assets/blender/heron-reach/props-kit.blend",
        "units": "metres, Blender Z up (glTF Y up), front faces -Y",
        "origin": "footprint centre on the ground unless mount is 'wall' (then the wall face, see notes)",
        "builder": "scripts/maps/art/make_heron_props.py",
        "textures": "public/materials/heron/props/ (made by scripts/maps/art/make_heron_prop_textures.py)",
        "sharedMaterialsArePlaceholders": True,
        "assets": [],
    }
    total = 0
    built = []
    for group_name, builders in GROUPS:
        gcol = bpy.data.collections.new(group_name)
        root_col.children.link(gcol)
        for b in builders:
            a = b()
            if only and a.name not in only:
                a.bm.free()
                continue
            ob = a.build(mats, gcol)
            built.append(ob)
            st = L.stats(ob)
            total += st["triangles"]
            meta = a.meta
            entry = {
                "name": a.name,
                "collection": a.name,
                "group": group_name,
                "category": a.category,
                "triangles": st["triangles"],
                "bounds": {"min": st["bounds_min"], "max": st["bounds_max"]},
                "size": st["size"],
                "footprint": [st["size"][0], st["size"][1]],
                "mount": meta.get("mount", "ground"),
                "needsCollision": bool(meta.get("needsCollision", False)),
                "collider": meta.get("collider"),
                "materials": list(a.mats),
                "notes": meta.get("notes", ""),
            }
            if "lightAnchor" in meta:
                entry["lightAnchor"] = meta["lightAnchor"]
            if "budget" in meta:
                entry["budget"] = meta["budget"]
            manifest["assets"].append(entry)
            print(f"{a.name:26s} {st['triangles']:6d} tris  size {st['size']}")
    manifest["totalTriangles"] = total
    manifest["doubleSidedMaterials"] = set_backface_culling(built)
    print("double-sided:", manifest["doubleSidedMaterials"])
    os.makedirs(os.path.dirname(out_blend), exist_ok=True)
    # drop unused images/materials that no asset references
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
    print("saved", out_blend)
    if not only:
        with open(OUT_MANIFEST, "w") as fh:
            json.dump(manifest, fh, indent=2)
            fh.write("\n")
        print("wrote", OUT_MANIFEST, "total tris", total)


if __name__ == "__main__":
    main(sys.argv[1:])
