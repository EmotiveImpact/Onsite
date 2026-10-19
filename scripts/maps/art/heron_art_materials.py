"""Material library for the Heron Reach art build.

Tiling materials read the texture kit's WebP sets from public/materials/heron/ (colour, OpenGL normal,
glTF ORM) and scale metric UVs by 1 / coverage. Plain materials are defined here. Every material
multiplies its base colour by the 'Col' vertex colour, which carries grime and baked occlusion.
A material whose textures have not been made yet falls back to a flat colour of the same name,
so the build always runs and picks up new textures on the next rebuild.
"""
import json
import os
import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TEX = os.path.join(ROOT, 'public', 'materials', 'heron')

# Flat fallbacks and plain materials: base colour (linear), roughness, metalness, emission (rgb, strength).
PLAIN = {
    'hr_brick_stock': ((.36, .27, .17), .85, 0),
    'hr_brick_red': ((.28, .09, .06), .85, 0),
    'hr_brick_painted': ((.55, .53, .48), .8, 0),
    'hr_concrete_cast': ((.42, .41, .38), .8, 0),
    'hr_concrete_board': ((.36, .35, .33), .85, 0),
    'hr_concrete_rough': ((.25, .24, .22), .9, 0),
    'hr_render': ((.5, .47, .42), .8, 0),
    'hr_asphalt': ((.05, .05, .055), .55, 0),
    'hr_court': ((.07, .12, .1), .6, 0),
    'hr_paving': ((.3, .29, .27), .6, 0),
    'hr_pavers_red': ((.22, .09, .07), .65, 0),
    'hr_roof_felt': ((.06, .06, .06), .8, 0),
    'hr_steel_black': ((.02, .02, .02), .45, .6),
    'hr_steel_galv': ((.45, .46, .47), .45, .9),
    'hr_steel_aged': ((.2, .12, .08), .7, .5),
    'hr_shutter': ((.4, .41, .42), .5, .8),
    'hr_rubber': ((.03, .03, .03), .7, 0),
    'hr_timber': ((.2, .12, .07), .7, 0),
    'hr_soil': ((.05, .035, .025), .95, 0),
    'hr_grass_ground': ((.06, .1, .03), .9, 0),
    'hr_gravel': ((.25, .24, .22), .9, 0),
    'hr_plaster': ((.62, .6, .55), .9, 0),
    'hr_glass': ((.02, .025, .03), .05, 0),
    'hr_upvc_white': ((.7, .7, .68), .45, 0),
    'hr_paint_yellow': ((.7, .5, .02), .55, 0),
    'hr_paint_white': ((.62, .62, .6), .55, 0),
    'hr_plastic_black': ((.02, .02, .02), .5, 0),
    'hr_plastic_green': ((.02, .12, .05), .5, 0),
    'hr_door_paint': ((.35, .35, .35), .45, 0),
    'hr_signage': ((.6, .6, .6), .5, 0),
    'hr_floor_laminate': ((.25, .15, .08), .45, 0),
    'hr_ceiling': ((.7, .69, .66), .9, 0),
    'hr_fabric': ((.12, .12, .14), .95, 0),
    'hr_wood_furniture': ((.22, .13, .07), .6, 0),
    'hr_kitchen': ((.6, .6, .58), .35, 0),
    'hr_ceramic': ((.75, .75, .74), .2, 0),
    'hr_window_dark': ((.01, .012, .015), .3, 0),
}
EMIT = {
    'hr_glass_lit': ((1.0, .62, .32), 4.0),
    'hr_lamp_emit': ((1.0, .7, .42), 30.0),
    'hr_window_interior': ((1.0, .66, .38), 3.0),
}


def coverage_table():
    path = os.path.join(ROOT, 'assets', 'blender', 'heron-reach', 'materials-manifest.json')
    out = {}
    if os.path.exists(path):
        for t in json.load(open(path)).get('tilingTextures', []):
            out[t['name']] = t.get('coverageMetres', 2.0)
    return out


COVERAGE = coverage_table()
DEFAULT_COVERAGE = {'hr_steel_black': 1.0, 'hr_steel_galv': 1.0, 'hr_steel_aged': 1.0, 'hr_rubber': 1.0}


def _image(path, non_color):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    return img


def texture_set(name):
    """Paths of colour/normal/orm for a material if its colour map exists."""
    for folder in (TEX, os.path.join(TEX, 'props')):
        c = os.path.join(folder, f'{name}-color.webp')
        if os.path.exists(c):
            n = os.path.join(folder, f'{name}-normal.webp')
            o = os.path.join(folder, f'{name}-orm.webp')
            return c, n if os.path.exists(n) else None, o if os.path.exists(o) else None
    return None


class Library:
    def __init__(self):
        self.cache = {}
        self.report = {}

    def __call__(self, name):
        if name not in self.cache:
            self.cache[name] = self.make(name)
        return self.cache[name]

    def make(self, name):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.use_backface_culling = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        out.location = (600, 0)
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (300, 0)
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        vcol = nt.nodes.new('ShaderNodeVertexColor')
        vcol.layer_name = 'Col'
        vcol.location = (-500, 300)
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type = 'RGBA'
        mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        mul.location = (50, 200)
        nt.links.new(vcol.outputs['Color'], mul.inputs['B'])
        nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])

        tex = texture_set(name)
        if tex:
            cov = COVERAGE.get(name, DEFAULT_COVERAGE.get(name, 2.0))
            uv = nt.nodes.new('ShaderNodeTexCoord')
            uv.location = (-1000, 0)
            mp = nt.nodes.new('ShaderNodeMapping')
            mp.location = (-800, 0)
            mp.inputs['Scale'].default_value = (1 / cov, 1 / cov, 1)
            nt.links.new(uv.outputs['UV'], mp.inputs['Vector'])
            c, n, o = tex
            ci = nt.nodes.new('ShaderNodeTexImage')
            ci.image = _image(c, False)
            ci.location = (-500, 100)
            nt.links.new(mp.outputs['Vector'], ci.inputs['Vector'])
            nt.links.new(ci.outputs['Color'], mul.inputs['A'])
            if n:
                ni = nt.nodes.new('ShaderNodeTexImage')
                ni.image = _image(n, True)
                ni.location = (-500, -400)
                nm = nt.nodes.new('ShaderNodeNormalMap')
                nm.location = (0, -400)
                nt.links.new(mp.outputs['Vector'], ni.inputs['Vector'])
                nt.links.new(ni.outputs['Color'], nm.inputs['Color'])
                nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
            if o:
                oi = nt.nodes.new('ShaderNodeTexImage')
                oi.image = _image(o, True)
                oi.location = (-500, -150)
                sep = nt.nodes.new('ShaderNodeSeparateColor')
                sep.location = (-150, -150)
                nt.links.new(mp.outputs['Vector'], oi.inputs['Vector'])
                nt.links.new(oi.outputs['Color'], sep.inputs['Color'])
                nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
                nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
            else:
                bsdf.inputs['Roughness'].default_value = PLAIN.get(name, ((0, 0, 0), .8, 0))[1]
            self.report[name] = {'textured': True, 'coverage': cov, 'normal': bool(n), 'orm': bool(o)}
            return mat

        if name in EMIT:
            col, strength = EMIT[name]
            mul.inputs['A'].default_value = (*col, 1)
            bsdf.inputs['Emission Color'].default_value = (*col, 1)
            bsdf.inputs['Emission Strength'].default_value = strength
            bsdf.inputs['Roughness'].default_value = .4
            self.report[name] = {'textured': False, 'emissive': strength}
            return mat
        col, rough, metal = PLAIN.get(name, ((.5, .1, .5), .5, 0))
        mul.inputs['A'].default_value = (*col, 1)
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        if name == 'hr_glass':
            # Thin glazing over the interior cards: mostly reflection, the room shows through.
            bsdf.inputs['Specular IOR Level'].default_value = .8
            bsdf.inputs['Alpha'].default_value = .28
            mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else None
        self.report[name] = {'textured': False, 'fallback': name not in PLAIN}
        return mat
