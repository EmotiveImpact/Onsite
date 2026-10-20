"""Prepare individually cleared Poly Haven plants for Heron Reach.

    blender -b -t 1 --python-exit-code 1 \
      --python scripts/maps/art/build_heron_world_plants.py

Uses only the pinned source download manifest; no downloads, physical geometry,
navigation, scene placement or edits to the original Blender collections.
Requires the repository's gltfpack and system Python 3 with Pillow and numpy.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil
import struct
import subprocess
import tempfile

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/reference/world-dressing"
BLEND = ROOT / "assets/blender/heron-reach/world-plants.blend"
MANIFEST = BLEND.with_name("world-plants-manifest.json")
OUTPUT = ROOT / "public/models/heron-reach/heron-reach-world-plants.glb"
FLAGS = ["-cc", "-kn", "-km", "-ke", "-kv", "-vpf", "-vtf"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def points(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def bounds(obj):
    verts = points(obj)
    return [[min(v[i] for v in verts) for i in range(3)],
            [max(v[i] for v in verts) for i in range(3)]]


def yup_bounds(obj):
    lo, hi = bounds(obj)
    return {"x0": lo[0], "x1": hi[0], "y0": lo[2], "y1": hi[2],
            "z0": -hi[1], "z1": -lo[1]}


def make_images(tmp):
    # Use explicit 16-bit → 8-bit conversion: Pillow.convert("L") clips the
    # upstream 16-bit mask. RGB JPEG has no alpha despite the source MASK flag.
    program = r'''
from PIL import Image
from pathlib import Path
import numpy as np
import json, sys
src, dst = map(Path, sys.argv[1:])
images = []
for asset, prefix, colour_size, normal_size in [
    ("fern_02", "hr_world_fern", 1024, 512),
    ("planter_pot_clay", "hr_world_clay", 256, 256),
]:
    base = src/asset/"textures"
    for channel, source, size in [
        ("colour", "diff", colour_size),
        ("normal", "nor_gl", normal_size),
        ("orm", "arm", 128),
    ]:
        im = Image.open(base/f"{asset}_{source}_1k.jpg").convert("RGB")
        im = im.resize((size, size), Image.Resampling.LANCZOS)
        if channel == "normal":
            v = np.asarray(im).astype(np.float32)/127.5-1
            v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
            im = Image.fromarray(np.round((v+1)*127.5).clip(0,255).astype(np.uint8))
        if asset == "fern_02" and channel == "colour":
            original = np.asarray(Image.open(base/"fern_02_alpha_1k.png")).astype(np.float64)
            assert original.max() > 255, "Expected the pinned 16-bit opacity source"
            alpha = np.round(original*255/65535).clip(0,255).astype(np.uint8)
            assert alpha.min() == 0 and alpha.max() == 255
            im = im.convert("RGBA")
            im.putalpha(Image.fromarray(alpha))
        path = dst/f"{prefix}_{channel}.png"
        im.save(path, optimize=True)
        images.append({"name": f"{prefix}_{channel}", "path": str(path),
                       "dimensions": [size,size], "channels": im.mode,
                       "estimatedRGBAWithMipBytes": sum(max(1,size>>n)**2*4 for n in range(size.bit_length())),
                       "colourSpace": "sRGB" if channel == "colour" else "Non-Color"})
(dst/"images.json").write_text(json.dumps(images))
'''
    subprocess.run(["python3", "-c", program, str(SOURCE), str(tmp)], check=True)
    result = json.loads((tmp / "images.json").read_text())
    loaded = {}
    for spec in result:
        image = bpy.data.images.load(spec["path"], check_existing=False)
        image.name = spec["name"]
        image.colorspace_settings.name = spec["colourSpace"]
        image.pack()
        loaded[spec["name"]] = image
    return result, loaded


def import_asset(source):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / source["localSource"]))
    objects = sorted(set(bpy.data.objects) - before, key=lambda obj: obj.name)
    assert all(obj.type == "MESH" for obj in objects), "Unexpected source hierarchy"
    return objects


def prepare_material(material, prefix, images):
    material.name = prefix
    replacements = {"_diff": "colour", "_nor_gl": "normal", "_arm": "orm", "_rough": "orm"}
    orm_node = None
    for node in material.node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        channel = next((value for suffix, value in replacements.items()
                        if suffix in node.image.name), None)
        assert channel, f"Unknown texture channel {node.image.name}"
        node.image = images[f"{prefix}_{channel}"]
        if channel == "orm":
            orm_node = node
    assert orm_node
    # Preserve the original imported MASK threshold graph and metallic factor.
    # Connect the source ARM red channel to the glTF-exporter AO socket too.
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        group.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    output = material.node_tree.nodes.new("ShaderNodeGroup")
    output.node_tree = group
    separate = material.node_tree.nodes.new("ShaderNodeSeparateColor")
    material.node_tree.links.new(orm_node.outputs["Color"], separate.inputs["Color"])
    material.node_tree.links.new(separate.outputs["Red"], output.inputs["Occlusion"])
    material["source"] = ("https://polyhaven.com/a/fern_02" if prefix.endswith("fern")
                          else "https://polyhaven.com/a/planter_pot_clay")
    material["licence"] = "CC0-1.0"


def normalise(obj, name, source, collection):
    original_pivot = obj.matrix_world.translation.copy()
    original_bounds = bounds(obj)
    low, high = original_bounds
    all_points = points(obj)
    stem = None
    if name.startswith("WORLD_FERN"):
        # A low dangling frond on B also reaches the ground: select the low
        # central stem cluster, excluding peripheral leaf-card vertices.
        basal = [p for p in all_points if p.z < low[2] + .008
                 and math.hypot(p.x-original_pivot.x, p.y-original_pivot.y) < .10]
        assert basal, f"No basal stem cluster for {name}"
        stem = sum(basal, Vector()) / len(basal)
    shift = Vector((-(low[0]+high[0])/2, -(low[1]+high[1])/2, -low[2]))
    obj.data.transform(Matrix.Translation(shift) @ obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.data.update()
    obj.name = name + "_mesh"
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    root = bpy.data.objects.new(name, None)
    collection.objects.link(root)
    obj.parent = root
    root["source"] = source["source"]
    root["licence"] = source["licence"]
    root["units"] = "metres"
    root["collision"] = "none"
    # `pivot` is interpreted as a numerical array by Three's GLTFLoader.
    root["originContract"] = "footprint centre, geometry minimum Y=0 in glTF"
    record = {
        "name": name, "sourceAsset": source["id"], "sourceObject": name.replace("WORLD_FERN_", "fern_02_").lower(),
        "sourceBoundsBlenderXYZ": original_bounds,
        "translationBlenderXYZ": list(shift), "scale": 1,
        "boundsYUp": yup_bounds(obj), "triangles": triangles(obj),
        "collision": "none", "renderOnly": True,
    }
    if stem is not None:
        stem += shift
        root["stemXZ"] = [stem.x, -stem.y]
        root["stemBasalY"] = stem.z
        record["stemXZ"] = list(root["stemXZ"])
        record["stemBasalY"] = stem.z
        record["stemMeasurement"] = "Centroid of source vertices within 8 mm of min height and 100 mm of source stem pivot; excludes low peripheral fronds."
    return root, obj, record


def soil_insert(pot, root, collection):
    height = .185
    segments = []
    pot.data.calc_loop_triangles()
    for tri in pot.data.loop_triangles:
        verts = [pot.data.vertices[i].co for i in tri.vertices]
        intersections = []
        for a, b in zip(verts, verts[1:] + verts[:1]):
            if (a.z < height <= b.z) or (b.z < height <= a.z):
                intersections.append(a + (b-a)*((height-a.z)/(b.z-a.z)))
        if len(intersections) == 2:
            segments.append(intersections)
    # A section of the scanned inner wall, sampled radially, produces a soil
    # cap that meets this irregular hand-made pot instead of floating in a
    # generic circle. Embed the edge 1 mm into the wall.
    edge, inner_radii = [], []
    for step in range(64):
        angle = step*math.tau/64
        dx, dy = math.cos(angle), math.sin(angle)
        radii = []
        for a, b in segments:
            ex, ey = b.x-a.x, b.y-a.y
            determinant = dx*ey-dy*ex
            if abs(determinant) < 1e-10:
                continue
            ray = (a.x*ey-a.y*ex)/determinant
            along = (a.x*dy-a.y*dx)/determinant
            if ray > 0 and -.00001 <= along <= 1.00001:
                radii.append(ray)
        assert radii, f"Pot section has a gap at angle {angle}"
        radius = min(radii)
        assert .09 < radius < .13, f"Unexpected inner wall: {radius}"
        inner_radii.append(radius)
        edge.append((dx*(radius+.001), dy*(radius+.001), height))
    mesh = bpy.data.meshes.new("hr_world_pot_soil_insert")
    mesh.from_pydata([(0, 0, height), *edge], [],
                     [(0, i+1, (i+1) % 64+1) for i in range(64)])
    mesh.update()
    material = bpy.data.materials.new("hr_world_soil")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (.027, .018, .012, 1)
    bsdf.inputs["Roughness"].default_value = .98
    material["source"] = "Original ONSITE soil cap; no external texture."
    mesh.materials.append(material)
    obj = bpy.data.objects.new("WORLD_CLAY_POT_soil", mesh)
    collection.objects.link(obj)
    obj.parent = root
    root["soilSurfaceY"] = height
    root["soilRadius"] = min(inner_radii)-.002
    root["soilCentreXZ"] = [0., 0.]
    return obj, {
        "soilSurfaceY": height, "soilRadius": root["soilRadius"],
        "soilCentreXZ": [0, 0], "innerWallRadii": [min(inner_radii), max(inner_radii)],
        "edgeEmbedMetres": .001, "triangles": 64,
        "source": "Original ONSITE geometry/material; horizontal section of the scanned pot's inner wall.",
    }


def parse_glb(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 12)[0]
    return data, json.loads(data[20:20+count])


def main():
    source_manifest = json.loads((SOURCE / "source-manifest.json").read_text())
    sources = {item["id"]: item for item in source_manifest["assets"]}
    for source in sources.values():
        for item in source["files"]:
            path = SOURCE / source["id"] / item["path"]
            assert path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], f"Source changed: {path}"
    checkpoint = None
    if BLEND.exists():
        checkpoint = Path(tempfile.mkdtemp(prefix="onsite-world-plants-checkpoint-")) / BLEND.name
        shutil.copy2(BLEND, checkpoint)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1
    collection = bpy.data.collections.new("HR_WORLD_PLANTS / cleared CC0 templates")
    bpy.context.scene.collection.children.link(collection)
    with tempfile.TemporaryDirectory(prefix="onsite-world-plants-") as folder:
        tmp = Path(folder)
        image_records, images = make_images(tmp)
        ferns = import_asset(sources["fern_02"])
        assert len(ferns) == 4
        prepare_material(ferns[0].data.materials[0], "hr_world_fern", images)
        roots, objects, records = [], [], []
        for fern in ferns:
            variant = fern.name.rsplit("_", 1)[1].upper()
            root, obj, record = normalise(fern, "WORLD_FERN_"+variant, sources["fern_02"], collection)
            roots.append(root)
            objects.append(obj)
            records.append(record)
        pots = import_asset(sources["planter_pot_clay"])
        assert len(pots) == 1
        prepare_material(pots[0].data.materials[0], "hr_world_clay", images)
        root, obj, record = normalise(pots[0], "WORLD_CLAY_POT", sources["planter_pot_clay"], collection)
        record["sourceObject"] = "planter_pot_clay"
        roots.append(root)
        objects.append(obj)
        soil, soil_record = soil_insert(obj, root, collection)
        objects.append(soil)
        record.update({key: soil_record[key] for key in ("soilSurfaceY", "soilRadius", "soilCentreXZ")})
        record["soilInsert"] = soil_record
        record["triangles"] += triangles(soil)
        records.append(record)
        # Remove unused imported original images; each derivative packs its
        # exact processed PNG bytes so this .blend has no temporary-file dependency.
        for image in list(bpy.data.images):
            if image not in images.values() and image.users == 0:
                bpy.data.images.remove(image)
        for image in images.values():
            assert image.packed_file and image.size[0] > 0
            image.filepath = "//world-plants-textures/" + image.name + ".png"
        for path in (BLEND.parent, OUTPUT.parent):
            path.mkdir(parents=True, exist_ok=True)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in roots+objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        raw = tmp / "world-plants.raw.glb"
        bpy.ops.export_scene.gltf(filepath=str(raw), export_format="GLB", use_selection=True,
                                  export_image_format="WEBP", export_image_quality=88,
                                  export_apply=True, export_yup=True, export_extras=True,
                                  export_lights=False, export_cameras=False)
        subprocess.run([str(ROOT / "node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(OUTPUT), *FLAGS], check=True)
    data, gltf = parse_glb(OUTPUT)
    total_triangles = sum(triangles(obj) for obj in objects)
    memory = sum(item["estimatedRGBAWithMipBytes"] for item in image_records)
    assert total_triangles <= 10000 and len(data) <= 1_500_000 and memory <= 8*1024*1024
    assert len(gltf.get("images", [])) == 6, "Unexpected texture duplication/loss"
    assert not [item for kind in ("images", "buffers") for item in gltf.get(kind, []) if item.get("uri")]
    assert not gltf.get("cameras") and "KHR_lights_punctual" not in gltf.get("extensionsUsed", [])
    materials = {item["name"]: item for item in gltf["materials"]}
    fern_material = materials["hr_world_fern"]
    assert fern_material["alphaMode"] == "MASK" and fern_material["doubleSided"] is True
    assert abs(fern_material.get("alphaCutoff", .5)-.5) < 1e-6
    for name in ("hr_world_fern", "hr_world_clay"):
        material = materials[name]
        assert "baseColorTexture" in material["pbrMetallicRoughness"] and "normalTexture" in material
        assert "metallicRoughnessTexture" in material["pbrMetallicRoughness"] and "occlusionTexture" in material
    named = {node.get("name"): node for node in gltf["nodes"]}
    assert all(root.name in named for root in roots)
    for root in roots:
        if root.name == "WORLD_CLAY_POT":
            assert named[root.name]["extras"]["soilSurfaceY"] == .185
        else:
            assert len(named[root.name]["extras"]["stemXZ"]) == 2
    manifest = {
        "builder": str(Path(__file__).relative_to(ROOT)), "blender": bpy.app.version_string,
        "units": "metres; Blender Z up; exported glTF Y up; native source scale preserved",
        "rootContract": "Each named root is identity transform, footprint centred X/Z, minY=0. Use uniform scale only. Fern stemXZ is in root-local glTF X/Z.",
        "sources": list(sources.values()), "licenceEvidence": source_manifest["licenceEvidence"],
        "assets": records, "objects": len(objects), "triangles": total_triangles,
        "modifications": [
            "Extracted the four separate fern catalogue meshes as individual roots.",
            "Preserved source topology, leaf normals, UVs and native metre scale; baked only catalogue placement and centre/base origin offsets.",
            "Combined the exact upstream 16-bit alpha PNG with source RGB diffuse; converted alpha linearly 0..65535 to 0..255. Source RGB JPEG alone has no alpha.",
            "Kept source MASK cutoff 0.5 and double-sided leaf rendering; no invisible backing/support planes.",
            "Reduced normal/ARM and small pot colour maps; renormalised resized OpenGL normals. Preserved metallic factor zero and source roughness, added ARM red-channel AO.",
            "Added an original 64-triangle soil insert following the pot's real inner wall at y0.185, edge embedded 1 mm; original plain dark rough soil material.",
            "Packed editable PNG derivatives into the new Blender source; embedded WebP runtime textures and meshopt compression.",
        ],
        "textures": [{key: value for key, value in item.items() if key != "path"} for item in image_records],
        "estimatedRGBAWithMipBytes": memory,
        "blend": {"path": str(BLEND.relative_to(ROOT)), "bytes": BLEND.stat().st_size, "sha256": digest(BLEND)},
        "runtime": {"path": str(OUTPUT.relative_to(ROOT)), "bytes": len(data), "sha256": digest(OUTPUT),
                    "extensionsRequired": gltf.get("extensionsRequired", []), "materials": list(materials)},
        "compression": {"tool": "npm gltfpack", "version": json.loads((ROOT/"node_modules/gltfpack/package.json").read_text())["version"], "flags": FLAGS},
        "collision": "None. Template kit contains render geometry only; placement is handled separately.",
        "rebuildCheckpoint": str(checkpoint) if checkpoint else None,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"bytes": len(data), "triangles": total_triangles, "mipBytes": memory, "assets": records}, indent=2))


if __name__ == "__main__":
    main()
