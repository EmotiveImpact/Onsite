"""Install packed PBR preview materials in the editable Blender source."""
import bpy

def prepare_materials(root):
    for name in ['brick','stock','concrete','asphalt','paving','steel']:
        mat=bpy.data.materials.get(name)
        if not mat:continue
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes.get('Principled BSDF')
        for node in list(nodes):
            if node.type not in ['BSDF_PRINCIPLED','OUTPUT_MATERIAL']:nodes.remove(node)
        for kind in ['color','normal','arm']:
            if name=='stock' and kind!='color':continue
            path=root/'public/materials/detail/generated-asphalt-color.webp' if name=='asphalt'and kind=='color'and(root/'public/materials/detail/generated-asphalt-color.webp').exists()else root/'public/materials/pbr'/f"{'brick' if name=='stock' else name}-{kind}.webp"
            if name=='stock':path=root/'public/materials/homes/stock-color.webp'
            image=bpy.data.images.load(str(path),check_existing=True)
            image.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color';image.pack()
            node=nodes.new('ShaderNodeTexImage');node.image=image
            if kind=='color':links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
            elif kind=='normal':
                normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.45
                links.new(node.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
            else:
                separate=nodes.new('ShaderNodeSeparateColor');links.new(node.outputs['Color'],separate.inputs['Color']);links.new(separate.outputs['Green'],bsdf.inputs['Roughness'])
                if name=='steel':links.new(separate.outputs['Blue'],bsdf.inputs['Metallic'])
