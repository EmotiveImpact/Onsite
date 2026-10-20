"""Export the four existing winter-tree LOD1 assets as a separate original ONSITE kit.

    blender -b -t 1 --python-exit-code 1 --python scripts/maps/art/export_heron_ground_trees.py

Use -- --root /path/to/Onsite --output-root /tmp/staging for an isolated export.
Only existing LOD1 collections are appended. The additive Blend keeps its original packed
materials. The GLB carries texture-free material names for reuse of the loaded winter kit.
The repository's locked gltfpack compresses geometry while retaining names and attributes;
the intermediate *.raw.glb remains available under the repository's existing ignore rule.
Source Blend files, textures, collision and navigation remain untouched. Named roots match
the runtime kit loader's getObjectByName().
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import bpy
from mathutils import Vector


EXPECTED = {
    "TREE_PLANE_A_LOD1": 1533,
    "TREE_PLANE_B_LOD1": 1393,
    "TREE_BIRCH_A_LOD1": 827,
    "TREE_BIRCH_B_LOD1": 610,
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67 and version == 2 and length == len(data)
    chunk_length, chunk_type = struct.unpack_from("<II", data, 12)
    assert chunk_type == 0x4E4F534A
    return json.loads(data[20:20 + chunk_length])


def asset_report(root):
    objects = [o for o in root.children_recursive if o.type == "MESH"]
    points = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    return {
        "name": root.name,
        "collection": root.name,
        "objects": [o.name for o in objects],
        "triangles": sum(len(p.vertices) - 2 for o in objects for p in o.data.polygons),
        "boundsBlender": {"min": low, "max": high},
        "boundsYUp": {"min": [low[0], low[2], -high[1]], "max": [high[0], high[2], -low[1]]},
        "materials": sorted({s.material.name for o in objects for s in o.material_slots if s.material}),
        "collision": {"type": "none", "note": "Render-only kit; existing runtime owns trunk collision."},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    root = args.root.resolve()
    output = (args.output_root or root).resolve()
    source = root / "assets/blender/heron-reach/winter-trees.blend"
    source_manifest = root / "assets/blender/heron-reach/winter-manifest.json"
    blend = output / "assets/blender/heron-reach/ground-trees.blend"
    manifest_path = blend.with_name("ground-trees-manifest.json")
    glb = output / "public/models/heron-reach/heron-reach-ground-trees.glb"
    raw = glb.with_name("heron-reach-ground-trees.raw.glb")
    gltfpack = root / "node_modules/.bin/gltfpack"
    package_dir = root / "node_modules/gltfpack"
    package = json.loads((package_dir / "package.json").read_text())
    lockfile = root / "package-lock.json"
    locked = json.loads(lockfile.read_text())["packages"]["node_modules/gltfpack"]
    assert package["version"] == locked["version"], "Installed gltfpack differs from lockfile"
    flags = ["-cc", "-kn", "-km", "-kv", "-vpf", "-vtf"]
    blend.parent.mkdir(parents=True, exist_ok=True)
    glb.parent.mkdir(parents=True, exist_ok=True)
    original_hash = digest(source)
    recorded = json.loads(source_manifest.read_text())
    recorded_lods = {lod["name"]: lod["triangles"] for a in recorded["assets"] for lod in a.get("lods", [])}
    assert all(recorded_lods.get(name) == count for name, count in EXPECTED.items()), "Source LOD manifest changed"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    with bpy.data.libraries.load(str(source), link=False) as (available, imported):
        assert set(EXPECTED).issubset(available.collections), "Missing winter LOD1 collection"
        imported.collections = list(EXPECTED)
    container = bpy.data.collections.new("HR_GROUND_TREES")
    scene.collection.children.link(container)
    roots = []
    for collection in imported.collections:
        assert collection is not None
        container.children.link(collection)
        collection.hide_viewport = False
        collection.hide_render = False
        objects = [o for o in collection.all_objects if o.type == "MESH"]
        assert len(objects) == 2, f"Expected bark and leaves for {collection.name}"
        tops = [o for o in objects if o.parent not in objects]
        origin = tops[0].matrix_world.translation.copy()
        assert all((o.matrix_world.translation - origin).length < 1e-6 for o in tops), "Mixed kit origins"
        parent = bpy.data.objects.new(collection.name, None)
        collection.objects.link(parent)
        parent.location = origin
        bpy.context.view_layer.update()
        for obj in tops:
            transform = obj.matrix_world.copy()
            obj.parent = parent
            obj.matrix_world = transform
        parent.location = (0, 0, 0)
        for obj in objects:
            obj.hide_viewport = False
            obj.hide_render = False
            obj.hide_set(False)
        roots.append(parent)

    # Appending only these collections retains exactly their four materials and ten images.
    # Repair the original relative image paths before export, retaining existing packed bytes.
    textures = []
    for image in bpy.data.images:
        if image.source != "FILE":
            continue
        relative = Path("public/materials/heron/foliage") / Path(image.filepath).name
        image_path = root / relative
        assert image_path.is_file(), f"Missing existing texture: {relative}"
        image.filepath = str(image_path)
        if not image.packed_file:
            image.pack()
        source_hash = digest(image_path)
        packed_hash = hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
        assert packed_hash == source_hash, f"Packed texture differs from source: {relative}"
        textures.append({"file": relative.as_posix(), "sha256": source_hash, "packed": True})

    bpy.context.view_layer.update()
    assets = [asset_report(parent) for parent in roots]
    assert {a["name"]: a["triangles"] for a in assets} == EXPECTED, "Source triangle counts changed"
    source_attributes = {slot.material.name: {"NORMAL", "TEXCOORD_0"} | ({"COLOR_0"} if obj.data.color_attributes else set())
                         for parent in roots for obj in parent.children_recursive if obj.type == "MESH"
                         for slot in obj.material_slots if slot.material}
    # Preserve editable source materials and exact packed texture bytes in the additive Blend.
    # Relative links are portable after copying the staged artefacts into the repository.
    for image in bpy.data.images:
        if image.source == "FILE":
            image.filepath = "//../../../public/materials/heron/foliage/" + Path(image.filepath).name
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=False)

    # The runtime has already loaded the original winter kit. Export geometry with its exact
    # material names only, then resolve those names to the original materials in the loader.
    # These in-memory copies are never saved back into the additive or original Blend files.
    placeholders = {}
    source_materials = {slot.material for parent in roots for obj in parent.children_recursive
                        if obj.type == "MESH" for slot in obj.material_slots if slot.material}
    for material in sorted(source_materials, key=lambda m: m.name):
        name = material.name
        material.name = name + "__packed_source"
        placeholder = material.copy()
        placeholder.name = name
        placeholder.use_nodes = True
        placeholder.node_tree.nodes.clear()
        output_node = placeholder.node_tree.nodes.new("ShaderNodeOutputMaterial")
        shader = placeholder.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Base Color"].default_value = material.diffuse_color
        shader.inputs["Roughness"].default_value = material.roughness
        shader.inputs["Metallic"].default_value = material.metallic
        placeholder.node_tree.links.new(shader.outputs["BSDF"], output_node.inputs["Surface"])
        placeholders[material] = placeholder
    for parent in roots:
        for obj in parent.children_recursive:
            if obj.type == "MESH":
                for slot in obj.material_slots:
                    if slot.material:
                        slot.material = placeholders[slot.material]

    bpy.ops.object.select_all(action="DESELECT")
    for parent in roots:
        parent.select_set(True)
        for obj in parent.children_recursive:
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(raw), export_format="GLB", use_selection=True,
        export_image_format="WEBP", export_materials="EXPORT",
        export_vertex_color="ACTIVE", export_apply=True, export_yup=True,
    )
    subprocess.run([str(gltfpack), "-i", str(raw), "-o", str(glb), *flags], cwd=root, check=True)
    document = read_glb(glb)
    nodes = document["nodes"]
    root_indices = document["scenes"][document.get("scene", 0)]["nodes"]
    assert {nodes[i]["name"] for i in root_indices} == set(EXPECTED), "Asset root names were not preserved"

    def triangles(node_index):
        node = nodes[node_index]
        count = 0
        if "mesh" in node:
            for primitive in document["meshes"][node["mesh"]]["primitives"]:
                assert primitive.get("mode", 4) == 4
                accessor = primitive.get("indices", primitive["attributes"]["POSITION"])
                count += document["accessors"][accessor]["count"] // 3
        return count + sum(triangles(child) for child in node.get("children", []))

    exported_counts = {nodes[i]["name"]: triangles(i) for i in root_indices}
    assert exported_counts == EXPECTED, f"Export triangle mismatch: {exported_counts}"
    assert not document.get("images") and not document.get("textures"), "Unexpected GLB texture resources"
    assert all("uri" not in buffer for buffer in document["buffers"]), "External GLB buffer"
    assert "EXT_meshopt_compression" in document.get("extensionsRequired", []), "Meshopt compression missing"
    expected_materials = {"hr_bark_plane", "hr_leaf_plane", "hr_bark_birch", "hr_leaf_birch"}
    assert {m["name"] for m in document["materials"]} == expected_materials, "Material names changed"
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            material_name = document["materials"][primitive["material"]]["name"]
            assert source_attributes[material_name].issubset(primitive["attributes"]), "Mesh attributes lost"
    assert digest(source) == original_hash, "Source Blend changed"
    summary = {
        "kit": "Heron Reach ground-pass winter trees (existing LOD1)",
        "blender": bpy.app.version_string,
        "builder": "scripts/maps/art/export_heron_ground_trees.py",
        "builderSHA256": digest(Path(__file__).resolve()),
        "units": "metres; ground-centred origins; glTF Y-up",
        "source": {"file": source.relative_to(root).as_posix(), "sha256": original_hash,
                   "manifest": source_manifest.relative_to(root).as_posix()},
        "blend": blend.relative_to(output).as_posix(),
        "glb": glb.relative_to(output).as_posix(),
        "provenance": "Existing original ONSITE winter-tree LOD1 meshes and unchanged project procedural textures. No new or external assets.",
        "runtimeMaterials": "The GLB has texture-free named placeholders. Resolve each exact material name from the already-loaded winter kit; this preserves bark and leaf maps without duplicate texture allocation. The additive Blend retains original packed materials.",
        "assets": assets,
        "textures": sorted(textures, key=lambda t: t["file"]),
        "compression": {
            "tool": "npm gltfpack", "version": package["version"], "flags": flags,
            "package": "node_modules/gltfpack/package.json", "packageSHA256": digest(package_dir / "package.json"),
            "lockfileSHA256": digest(lockfile), "lockedIntegrity": locked["integrity"],
            "files": [{"file": (package_dir / name).relative_to(root).as_posix(), "sha256": digest(package_dir / name)}
                      for name in ["cli.js", "library.js", "library.wasm"]],
        },
        "export": {"nodeNames": [n.get("name") for n in nodes], "roots": list(exported_counts),
                   "triangles": sum(exported_counts.values()), "meshes": len(document["meshes"]),
                   "primitives": sum(len(m["primitives"]) for m in document["meshes"]),
                   "materials": [m["name"] for m in document["materials"]],
                   "meshAttributes": {m.get("name", f"mesh_{i}"): sorted(m["primitives"][0]["attributes"]) for i, m in enumerate(document["meshes"])},
                   "images": len(document.get("images", [])), "textures": len(document.get("textures", [])),
                   "extensionsUsed": document.get("extensionsUsed", []), "extensionsRequired": document.get("extensionsRequired", []),
                   "rawGLBBytes": raw.stat().st_size, "rawGLBSha256": digest(raw),
                   "glbBytes": glb.stat().st_size, "blendBytes": blend.stat().st_size,
                   "glbSha256": digest(glb)},
    }
    manifest_path.write_text(json.dumps(summary, indent=2) + "\n")
    print("GROUND_TREES " + json.dumps(summary["export"]))


if __name__ == "__main__":
    main()
