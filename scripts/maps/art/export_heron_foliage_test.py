"""Test-export one plane tree and one grass patch from the foliage kit to GLB and inspect them.

Run:  python3 scripts/maps/art/export_heron_foliage_test.py [OUT_DIR]
Checks that leaf materials export as alphaMode MASK (cutoff 0.5), doubleSided, and that
textures are embedded in the GLB binary chunk. Prints a JSON summary.
"""
import json
import os
import struct
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BLEND = os.path.join(REPO, "assets", "blender", "heron-reach", "foliage-kit.blend")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "tmp-foliage-test")


def read_glb(path):
    with open(path, "rb") as fh:
        data = fh.read()
    magic, ver, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not a GLB"
    off = 12
    js, binlen = None, 0
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            binlen = clen
        off += 8 + clen
    return js, binlen


def export(coll_names, path, fmt):
    bpy.ops.object.select_all(action="DESELECT")
    for cn in coll_names:
        for o in bpy.data.collections[cn].all_objects:
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_image_format=fmt,
                              export_vertex_color="MATERIAL", export_yup=True, export_apply=True)


def summarise(path):
    js, binlen = read_glb(path)
    mats = [{"name": m.get("name"), "alphaMode": m.get("alphaMode", "OPAQUE"), "alphaCutoff": m.get("alphaCutoff"),
             "doubleSided": m.get("doubleSided", False),
             "textures": [k for k in ("normalTexture", "occlusionTexture") if k in m] +
                         [k for k in ("baseColorTexture", "metallicRoughnessTexture") if k in m.get("pbrMetallicRoughness", {})]}
            for m in js.get("materials", [])]
    imgs = [{"name": i.get("name"), "mimeType": i.get("mimeType"), "embedded": "bufferView" in i and "uri" not in i}
            for i in js.get("images", [])]
    prims = []
    for me in js.get("meshes", []):
        for p in me["primitives"]:
            prims.append({"mesh": me.get("name"), "attributes": sorted(p["attributes"].keys()),
                          "material": js["materials"][p["material"]]["name"] if "material" in p else None})
    return {"file": path, "bytes": os.path.getsize(path), "binary_chunk_bytes": binlen, "materials": mats,
            "images": imgs, "primitives": prims, "extensionsUsed": js.get("extensionsUsed", [])}


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    # make sure the LOD collection is visible so its objects can be selected if needed
    for lc in bpy.context.view_layer.layer_collection.children:
        lc.hide_viewport = False
        lc.exclude = False
    results = []
    for fmt in ("WEBP", "AUTO"):
        for name, colls in (("tree-plane-a", ["TREE_PLANE_A"]), ("grass-patch-1m", ["GRASS_PATCH_1M"])):
            path = os.path.join(OUT, "%s-%s.glb" % (name, fmt.lower()))
            export(colls, path, fmt)
            results.append(summarise(path))
    print("SUMMARY_JSON " + json.dumps(results))


if __name__ == "__main__":
    main()
