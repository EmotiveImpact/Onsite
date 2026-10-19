"""GLB export test for the Heron Reach props kit.

    python3 scripts/maps/art/export_heron_props_test.py OUT_DIR [NAME,NAME,...]

Exports each named asset collection from props-kit.blend as its own GLB (WebP images),
then reads the GLB JSON chunk back and checks materials, images, alpha mode and emission.
Prints a JSON summary and exits non-zero when an expectation fails.
"""

import json
import os
import struct
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
KIT = os.path.join(ROOT, "assets", "blender", "heron-reach", "props-kit.blend")

DEFAULT = ["CAGE_PANEL_2_5M", "LAMP_COLUMN", "SHOP_FRIDGE"]
# what each test asset must show in the exported file
EXPECT = {
    "CAGE_PANEL_2_5M": {"mask": "hr_prop_cage_mesh"},
    "LAMP_COLUMN": {"emissive": "hr_lamp_emit"},
    "SHOP_FRIDGE": {"emissive": "hr_prop_fridge_light", "blend": "hr_prop_glass_clear"},
    "SHOP_SIGN_CORNER": {"emissive": "hr_prop_sign_letters"},
}


def read_glb_json(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not a GLB"
    clen, ctype = struct.unpack_from("<II", data, 12)
    assert ctype == 0x4E4F534A, "first chunk is not JSON"
    return json.loads(data[20:20 + clen].decode("utf-8")), length


def export_one(name, out_dir):
    bpy.ops.object.select_all(action="DESELECT")
    col = bpy.data.collections[name]
    obs = list(col.all_objects)
    for ob in obs:
        ob.hide_set(False)
        ob.hide_select = False
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    path = os.path.join(out_dir, name.lower() + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_image_format="WEBP",
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
    )
    return path


def check(name, path):
    gj, size = read_glb_json(path)
    mats = gj.get("materials", [])
    report = {
        "file": path,
        "bytes": size,
        "meshes": len(gj.get("meshes", [])),
        "materials": [],
        "images": [{"name": i.get("name"), "mimeType": i.get("mimeType")} for i in gj.get("images", [])],
        "extensionsUsed": gj.get("extensionsUsed", []),
        "problems": [],
    }
    for m in mats:
        ext = m.get("extensions", {})
        pbr = m.get("pbrMetallicRoughness", {})
        report["materials"].append({
            "name": m.get("name"),
            "alphaMode": m.get("alphaMode", "OPAQUE"),
            "alphaCutoff": m.get("alphaCutoff"),
            "doubleSided": m.get("doubleSided", False),
            "baseColorTexture": "baseColorTexture" in pbr,
            "normalTexture": "normalTexture" in m,
            "emissiveFactor": m.get("emissiveFactor"),
            "emissiveTexture": "emissiveTexture" in m,
            "emissiveStrength": ext.get("KHR_materials_emissive_strength", {}).get("emissiveStrength"),
        })
    by = {m["name"]: m for m in report["materials"]}
    exp = EXPECT.get(name, {})
    if "mask" in exp:
        m = by.get(exp["mask"])
        if not m or m["alphaMode"] != "MASK" or not m["doubleSided"] or not m["baseColorTexture"]:
            report["problems"].append(f"{exp['mask']} is not a double-sided textured MASK material")
    if "emissive" in exp:
        m = by.get(exp["emissive"])
        if not m or not (m["emissiveFactor"] and max(m["emissiveFactor"]) > 0):
            report["problems"].append(f"{exp['emissive']} has no emission")
    if "blend" in exp:
        m = by.get(exp["blend"])
        if not m or m["alphaMode"] != "BLEND":
            report["problems"].append(f"{exp['blend']} is not BLEND")
    for img in report["images"]:
        if img["mimeType"] != "image/webp":
            report["problems"].append(f"image {img['name']} is {img['mimeType']}")
    return report


def main():
    args = sys.argv[1:]
    out_dir = args[0]
    names = args[1].split(",") if len(args) > 1 else DEFAULT
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=KIT)
    results = [check(n, export_one(n, out_dir)) for n in names]
    print("GLB_TEST " + json.dumps(results, indent=1))
    failed = [r for r in results if r["problems"]]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
