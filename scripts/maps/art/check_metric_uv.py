"""Blender regression: colour-layer allocation must not discard metric/custom UVs.

blender -b --python-exit-code 1 --python scripts/maps/art/check_metric_uv.py
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from heron_art_mesh import Builder
bpy.ops.wm.read_factory_settings(use_empty=True)
collection=bpy.data.collections.new('UV_CHECK');bpy.context.scene.collection.children.link(collection)
builder=Builder(lambda _:collection)
builder.quad('probe','probe',(0,0,0),(8,0,0),(8,2,0),(0,2,0),uv=[(0,0),(8,0),(8,2),(0,2)])
objects=builder.build(lambda _:bpy.data.materials.new('probe'))
actual=[tuple(x.uv) for x in objects[0].data.uv_layers['UVMap'].data]
expected=[(0.,0.),(8.,0.),(8.,2.),(0.,2.)]
assert actual==expected,(actual,expected)
assert objects[0].data.color_attributes.get('Col') is not None
print('PASS: metric UVs survive vertex-colour allocation in Blender',bpy.app.version_string)
