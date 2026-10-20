"""Adapt individually licensed existing Poly Haven props for Heron Reach.

Run with Blender 4.3+: blender -b --python-exit-code 1 --python
scripts/maps/art/build_heron_world_props.py

Original donor files and original estate/kit Blender sources are never written.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import subprocess
import tempfile

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "public/models/donors"
OUT = ROOT / "public/models/heron-reach/heron-reach-world-props.glb"
BLEND = ROOT / "assets/blender/heron-reach/world-props.blend"
MANIFEST = BLEND.with_name("world-props-manifest.json")
PROVENANCE = json.loads((SOURCE / "provenance.json").read_text())
SPECS = [
    ("WORLD_TRASH_BAG", "trashbag", "trashbag"),
    ("WORLD_BIN_RUST", "metal_trash_can", "metal_trash_can_rust"),
    ("WORLD_AIRCON_RUST", "exterior_aircon_unit", "exterior_aircon_unit_rusted"),
    ("WORLD_CARDBOARD_BOX", "cardboard_box_01", "cardboard_box_01"),
    ("WORLD_WOODEN_CRATE", "wooden_crate_02", "wooden_crate_02_crate"),
    ("WORLD_TYRE", "old_tyre", "old_tyre"),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def glb(path):
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + length])
    binary = data[28 + length:]
    return doc, binary


def bounds(points):
    return {"min": [float(min(p[i] for p in points)) for i in range(3)],
            "max": [float(max(p[i] for p in points)) for i in range(3)]}


def world_bounds(points):
    # Blender world Z-up -> glTF Y-up.
    bb = bounds([(p.x, p.z, -p.y) for p in points])
    bb["size"] = [bb["max"][i] - bb["min"][i] for i in range(3)]
    return bb


def components(mesh):
    """Position-welded connectivity for identifying disconnected source parts only."""
    ids, indices = {}, []
    for v in mesh.vertices:
        key = tuple(round(c, 5) for c in v.co)
        indices.append(ids.setdefault(key, len(ids)))
    parent = list(range(len(ids)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for face in mesh.polygons:
        a = find(indices[face.vertices[0]])
        for v in face.vertices[1:]:
            parent[find(indices[v])] = a
    groups = {}
    for i, v in enumerate(mesh.vertices):
        groups.setdefault(find(indices[i]), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


def source_record(stem, node):
    path = SOURCE / (stem + ".glb")
    provenance = next(p for p in PROVENANCE if p["file"] == "models/donors/" + path.name)
    assert provenance["licence"] == "CC0-1.0"
    doc, binary = glb(path)
    images = []
    for im in doc.get("images", []):
        view = doc["bufferViews"][im["bufferView"]]
        data = binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]]
        images.append({"name": im.get("name"), "mimeType": im["mimeType"],
                       "bytes": len(data), "sha256": sha(data)})
    return {"file": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()),
            "node": node, "licence": provenance["licence"], "creators": provenance["creators"],
            "sources": provenance["sources"], "donor": provenance["donor"],
            "donorCommit": provenance["commit"], "donorPath": provenance["donorPath"],
            "priorModifications": provenance["modifications"], "sourceImages": images}


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1
bpy.context.preferences.filepaths.save_version = 0
collection = bpy.data.collections.new("HR_WORLD_PROPS")
bpy.context.scene.collection.children.link(collection)
records = []

for root_name, stem, selected_name in SPECS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE / (stem + ".glb")))
    imported = set(bpy.data.objects) - before
    selected = [o for o in imported if o.type == "MESH" and o.name == selected_name]
    assert len(selected) == 1, (root_name, [o.name for o in imported])
    src = selected[0]
    assert src.matrix_world.determinant() > 0
    old = src.data
    points = [src.matrix_world @ v.co for v in old.vertices]
    normal_matrix = src.matrix_world.to_3x3().inverted().transposed()
    normals = [(normal_matrix @ c.vector).normalized() for c in old.corner_normals]
    source_bb = world_bounds(points)
    rotations = {}
    excluded = set()
    changes = []

    if root_name == "WORLD_BIN_RUST":
        parts = components(old)
        body = parts[0]
        body_bb = bounds([points[i] for i in body])
        lids = [v for v in parts if min(points[i].x for i in v) < -.85
                and max(points[i].z for i in v) < .56]
        assert len(lids) == 2 and sorted(map(len, lids)) == [21, 217]
        disc = max(lids, key=len)
        handle = min(lids, key=len)
        centre = sum((points[i] for i in disc), Vector()) / len(disc)
        array = np.array([tuple(points[i] - centre) for i in disc])
        eigenvalues, eigenvectors = np.linalg.eigh(np.cov(array.T))
        normal = Vector(eigenvectors[:, int(np.argmin(eigenvalues))])
        handle_centre = sum((points[i] for i in handle), Vector()) / len(handle)
        if normal.dot(handle_centre - centre) < 0:
            normal.negate()
        rotation = normal.rotation_difference(Vector((0, 0, 1)))
        rotated = {i: rotation @ (points[i] - centre) for part in lids for i in part}
        disc_bb = bounds([rotated[i] for i in disc])
        translation = Vector(((body_bb["min"][0] + body_bb["max"][0]
                               - disc_bb["min"][0] - disc_bb["max"][0]) / 2,
                              (body_bb["min"][1] + body_bb["max"][1]
                               - disc_bb["min"][1] - disc_bb["max"][1]) / 2,
                              body_bb["max"][2] - .008 - disc_bb["min"][2]))
        for i, p in rotated.items():
            points[i] = p + translation
            rotations[i] = rotation
        changes.append({"operation": "Close disconnected original lid and its handle over the can rim",
                        "partVertexCounts": [len(disc), len(handle)], "rimOverlapMetres": .008,
                        "rotationQuaternionWXYZ": list(rotation),
                        "rotationPivotBlenderXYZ": list(centre),
                        "translationAfterPivotRotationBlenderXYZ": list(translation)})

    if root_name == "WORLD_AIRCON_RUST":
        dangling = [v for v in components(old) if min(points[i].z for i in v) < -.10]
        assert len(dangling) == 1 and len(dangling[0]) == 33
        excluded.update(dangling[0])
        changes.append({"operation": "Omit the disconnected drain pipe hanging below the original support feet",
                        "removedVertexCount": len(excluded),
                        "removedBounds": world_bounds([points[i] for i in excluded]),
                        "reason": "The cabinet and original feet rest on roof/bench support without a pipe entering the floor."})

    if root_name == "WORLD_TYRE":
        rotation = Matrix.Rotation(-math.pi / 2, 3, "X").to_quaternion()
        points = [rotation @ p for p in points]
        rotations = {i: rotation for i in range(len(points))}
        changes.append({"operation": "Lay the original upright wheel flat, detailed outer face upward",
                        "rotationBlenderX": -math.pi / 2})

    if root_name == "WORLD_WOODEN_CRATE":
        rotation = Matrix.Rotation(math.pi / 2, 3, "Z").to_quaternion()
        points = [rotation @ p for p in points]
        rotations = {i: rotation for i in range(len(points))}
        changes.append({"operation": "Turn the original long side across X", "rotationBlenderZ": math.pi / 2})

    faces = [p for p in old.polygons if not any(v in excluded for v in p.vertices)]
    used = sorted({i for p in faces for i in p.vertices})
    bb = bounds([points[i] for i in used])
    offset = Vector((-(bb["min"][0] + bb["max"][0]) / 2,
                     -(bb["min"][1] + bb["max"][1]) / 2, -bb["min"][2]))
    points = [p + offset for p in points]
    remap = {v: i for i, v in enumerate(used)}
    mesh = bpy.data.meshes.new(root_name + "_mesh")
    mesh.from_pydata([points[i] for i in used], [], [[remap[v] for v in p.vertices] for p in faces])
    mesh.update()
    for material in old.materials:
        mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="UVMap")
    old_uv = old.uv_layers.active
    new_normals = []
    for p, previous in zip(mesh.polygons, faces):
        p.material_index = previous.material_index
        p.use_smooth = previous.use_smooth
        for li, old_li in zip(p.loop_indices, previous.loop_indices):
            vi = old.loops[old_li].vertex_index
            uv.data[li].uv = old_uv.data[old_li].uv
            n = normals[old_li]
            new_normals.append(tuple(rotations[vi] @ n if vi in rotations else n))
    mesh.normals_split_custom_set(new_normals)
    obj = bpy.data.objects.new(root_name + "_geometry", mesh)
    collection.objects.link(obj)
    root = bpy.data.objects.new(root_name, None)
    collection.objects.link(root)
    obj.parent = root
    root["licence"] = "CC0-1.0"
    root["collision"] = "Render only; runtime preserves existing physical placement envelopes."
    root["origin"] = "glTF metre coordinates, centre X/Z and minY=0."
    root["front"] = "+Z; the flat tyre has its detailed face +Y."
    triangles = sum(len(p.vertices) - 2 for p in mesh.polygons)
    record = {"name": root_name, "source": source_record(stem, selected_name),
              "sourceSelectedBounds": source_bb, "bounds": world_bounds([points[i] for i in used]),
              "origin": "centred X/Z; base minY=0", "front": root["front"],
              "sourceSelectedTriangles": sum(len(p.vertices) - 2 for p in old.polygons),
              "triangles": triangles, "normalisationBlenderXYZ": list(offset), "modifications": changes,
              "materials": [m.name for m in mesh.materials]}
    records.append(record)
    for o in imported:
        bpy.data.objects.remove(o, do_unlink=True)

# Delete unused variants and their images; the source file contains only selected assets.
bpy.data.orphans_purge(do_recursive=True)
materials = list(bpy.data.materials)
image_plans = {}
for material in materials:
    original_name = material.name
    material.name = "hr_world_" + original_name
    for record in records:
        record["materials"] = [material.name if m == original_name else m for m in record["materials"]]
    for node in material.node_tree.nodes:
        if node.type != "TEX_IMAGE" or node.image is None:
            continue
        image = node.image
        role = "normal" if "_nor" in image.name else ("colour" if "_diff" in image.name else "data")
        small = original_name == "old_tyre"
        size = 512 if (role == "colour" and not small) or (role == "normal" and original_name == "metal_trash_can_rust") else 256
        prior = image_plans.setdefault(image.name, {"image": image, "size": size, "role": role, "materials": []})
        assert prior["size"] == size and prior["role"] == role
        prior["materials"].append(material.name)
    if original_name == "exterior_aircon_unit_rusted_02":
        # Its source glTF says BLEND, but the supplied colour image is RGB and
        # its opacity is one everywhere. Keep those pixels opaque, without
        # inventing a transparency mask from the misleading filename.
        bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        for link in list(bsdf.inputs["Alpha"].links):
            material.node_tree.links.remove(link)
        bsdf.inputs["Alpha"].default_value = 1
        material.diffuse_color = (*material.diffuse_color[:3], 1)

image_manifest = []
with tempfile.TemporaryDirectory(prefix="heron-world-props-") as temp_name:
    temp = Path(temp_name)
    for name, plan in image_plans.items():
        image, size = plan["image"], plan["size"]
        image.scale(size, size)
        image.filepath_raw = str(temp / (name + ".png"))
        image.file_format = "PNG"
        image.save()
        image.pack()
        assert image.packed_file and tuple(image.size) == (size, size)
        packed_bytes = bytes(image.packed_file.data)
        image.filepath = "//world-props-packed/" + name + ".png"
        image_manifest.append({"name": name, "role": plan["role"], "size": [size, size],
                               "materials": sorted(set(plan["materials"])),
                               "packedSourcePNGBytes": len(packed_bytes), "packedSourcePNGSHA256": sha(packed_bytes)})
    assert len(image_manifest) == 21
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
    raw = temp / "world-props.raw.glb"
    bpy.ops.export_scene.gltf(filepath=str(raw), export_format="GLB", export_yup=True,
                             export_apply=True, export_image_format="AUTO", export_extras=True)
    # Re-encode the resized packed PNGs. All normal/data maps remain lossless;
    # editable packed PNGs are preserved independently in the Blend.
    # gltfpack then drops the old unused PNG buffer views and compresses geometry.
    conversion = r'''
from pathlib import Path
from PIL import Image
from io import BytesIO
import json,struct,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); n=struct.unpack_from('<I',raw,12)[0]
g=json.loads(raw[20:20+n]); binary=bytearray(raw[28+n:])
for im in g.get('images',[]):
 v=g['bufferViews'][im['bufferView']]; data=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 image=Image.open(BytesIO(data)); name=im.get('name','')
 lossless=('_nor' in name or '_rough' in name or '_metal' in name or 'MetallicRoughness' in name)
 output=BytesIO(); image.save(output,'WEBP',lossless=lossless,quality=90,method=6)
 while len(binary)%4:binary.append(0)
 im['bufferView']=len(g['bufferViews'])
 g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(output.getvalue())})
 binary.extend(output.getvalue()); im['mimeType']='image/webp'
for t in g.get('textures',[]):
 source=t.pop('source',None)
 if source is not None:t.setdefault('extensions',{})['EXT_texture_webp']={'source':source}
for k in ['extensionsUsed','extensionsRequired']:
 if 'EXT_texture_webp' not in g.setdefault(k,[]):g[k].append('EXT_texture_webp')
while len(binary)%4:binary.append(0)
g['buffers'][0]['byteLength']=len(binary)
j=json.dumps(g,separators=(',',':')).encode()
while len(j)%4:j+=b' '
p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\x00')+binary)
'''
    subprocess.run(["python3", "-c", conversion, str(raw)], check=True)
    flags = ["-cc", "-kn", "-km", "-kv", "-vpf", "-vtf"]
    subprocess.run(["npx", "--no-install", "gltfpack", "-i", str(raw), "-o", str(OUT), *flags],
                   cwd=ROOT, check=True)

doc, binary = glb(OUT)
textures = []
for im in doc["images"]:
    view = doc["bufferViews"][im["bufferView"]]
    data = binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]]
    # PIL lives in the system Python, not Blender's Python. Ask it to measure
    # actual exported images in one batch below, without creating runtime files.
    textures.append({"name": im.get("name", ""), "mimeType": im["mimeType"],
                     "bytes": len(data), "sha256": sha(data)})
inspection = r'''
from pathlib import Path
from PIL import Image
from io import BytesIO
import json,struct,sys
b=Path(sys.argv[1]).read_bytes(); n=struct.unpack_from('<I',b,12)[0]
g=json.loads(b[20:20+n]); binary=b[28+n:]; result=[]
for im in g['images']:
 v=g['bufferViews'][im['bufferView']]
 image=Image.open(BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]))
 w,h=image.size; size=[w,h]; mip=0
 while True:
  mip+=w*h*4
  if w==1 and h==1:break
  w=max(1,w//2);h=max(1,h//2)
 result.append({'size':size,'estimatedMipBytesRGBA8':mip})
print(json.dumps(result))
'''
measurements = json.loads(subprocess.check_output(["python3", "-c", inspection, str(OUT)], text=True))
for texture, measure in zip(textures, measurements):
    texture.update(measure)
tris = sum(doc["accessors"][p["indices"]]["count"] // 3 for m in doc["meshes"] for p in m["primitives"])
assert tris == sum(r["triangles"] for r in records) and tris <= 15000
texture_bytes = sum(t["estimatedMipBytesRGBA8"] for t in textures)
assert texture_bytes <= 16_000_000, texture_bytes
assert OUT.stat().st_size <= 2_000_000
for record in records:
    bb = record["bounds"]
    assert abs(bb["min"][1]) < 1e-6
    assert abs(bb["min"][0] + bb["max"][0]) < 1e-6
    assert abs(bb["min"][2] + bb["max"][2]) < 1e-6
manifest = {
    "builder": str(Path(__file__).relative_to(ROOT)), "builderSHA256": sha(Path(__file__).read_bytes()),
    "blender": bpy.app.version_string, "provenance": "Existing individually licensed CC0 Poly Haven derivatives; adapted without changing originals.",
    "sourceProvenanceFile": "public/models/donors/provenance.json",
    "sourceProvenanceSHA256": sha((SOURCE / "provenance.json").read_bytes()),
    "coordinates": "Metres; glTF Y-up, root X/Z centred and base minY=0; front +Z.",
    "collision": "No collider or navigation changes. Explicit runtime matrices must stay within existing support/clearance envelopes.",
    "assets": records, "triangles": tris, "materialBatches": sum(len(m["primitives"]) for m in doc["meshes"]),
    "materials": [m["name"] for m in doc["materials"]], "textures": textures,
    "packedEditableTextures": image_manifest, "estimatedTextureMipBytesRGBA8": texture_bytes,
    "texturePolicy": "512 colour for close props; 512 bin normal; 256 secondary/data maps and tyre. Colour WebP quality90; all normal/data maps lossless. Editable source packs resized PNGs.",
    "alphaCorrection": "The AC rusted_02 source declares BLEND but its source WebP has RGB channels only. Alpha is normalised to opaque; no invented mask.",
    "newLights": 0, "compressedGLBBytes": OUT.stat().st_size, "compressedGLBSHA256": sha(OUT.read_bytes()),
    "blendBytes": BLEND.stat().st_size, "blendSHA256": sha(BLEND.read_bytes()),
    "compression": {"tool": "npm gltfpack", "version": json.loads((ROOT / "node_modules/gltfpack/package.json").read_text())["version"],
                    "flags": flags, "lockfileSHA256": sha((ROOT / "package-lock.json").read_bytes())},
}
MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
print("WORLD_PROPS", tris, "triangles;", OUT.stat().st_size, "bytes;", texture_bytes, "texture mip bytes;", manifest["compressedGLBSHA256"])
