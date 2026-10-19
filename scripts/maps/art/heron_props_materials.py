"""Placeholder shared materials and the kit's own hr_prop_* materials.

Shared names follow docs/maps/heron-reach-32/art/CONVENTIONS.md. These are plain
Principled placeholders with plausible colour and roughness; the lead swaps in the
texture kit's versions by name. hr_prop_* materials belong to this kit and use the
procedural images in public/materials/heron/props/.
"""

import os

import bpy

# name: (base colour (linear), roughness, metallic, options)
SHARED = {
    "hr_steel_black": ((0.030, 0.030, 0.032), 0.55, 0.25, {}),
    "hr_steel_galv": ((0.42, 0.43, 0.43), 0.42, 0.90, {}),
    "hr_steel_aged": ((0.11, 0.085, 0.065), 0.78, 0.45, {}),
    "hr_concrete_cast": ((0.36, 0.35, 0.33), 0.85, 0.0, {}),
    "hr_concrete_rough": ((0.30, 0.29, 0.27), 0.92, 0.0, {}),
    "hr_timber": ((0.075, 0.050, 0.034), 0.72, 0.0, {}),
    "hr_plastic_black": ((0.022, 0.022, 0.023), 0.55, 0.0, {}),
    "hr_plastic_green": ((0.032, 0.058, 0.040), 0.55, 0.0, {}),
    "hr_paint_yellow": ((0.62, 0.42, 0.04), 0.45, 0.0, {}),
    "hr_lamp_emit": ((1.0, 0.78, 0.52), 0.35, 0.0, {"emit": (1.0, 0.62, 0.30), "strength": 30.0}),
    "hr_glass": ((0.015, 0.018, 0.022), 0.06, 0.0, {"specular": 0.6}),
    "hr_glass_lit": ((1.0, 0.75, 0.48), 0.2, 0.0, {"emit": (1.0, 0.66, 0.38), "strength": 3.0}),
    "hr_signage": ((0.040, 0.042, 0.046), 0.50, 0.15, {}),
    "hr_rubber": ((0.018, 0.018, 0.018), 0.88, 0.0, {}),
    "hr_upvc_white": ((0.62, 0.62, 0.59), 0.45, 0.0, {}),
    "hr_soil": ((0.07, 0.05, 0.035), 0.95, 0.0, {}),
}

# name: (base colour, roughness, metallic, options)  options: image, normal, alpha, emit...
PROP = {
    "hr_prop_cage_mesh": ((1, 1, 1), 0.55, 0.3, {"image": "cage_mesh", "alpha": True}),
    "hr_prop_wire_grid": ((1, 1, 1), 0.40, 0.8, {"image": "wire_grid", "alpha": True}),
    "hr_prop_goal_net": ((1, 1, 1), 0.90, 0.0, {"image": "goal_net", "alpha": True}),
    "hr_prop_goal_paint": ((0.62, 0.62, 0.58), 0.50, 0.0, {}),
    "hr_prop_products": ((1, 1, 1), 0.45, 0.0, {"image": "products"}),
    "hr_prop_shop": ((1, 1, 1), 0.50, 0.0, {"image": "shop"}),
    "hr_prop_shop_lit": ((1, 1, 1), 0.40, 0.0, {"image": "shop", "emit_image": True, "strength": 2.5}),
    "hr_prop_sign_letters": ((0.95, 0.90, 0.80), 0.40, 0.0, {"emit": (1.0, 0.86, 0.66), "strength": 8.0}),
    "hr_prop_glass_clear": ((0.80, 0.85, 0.88), 0.04, 0.0, {"alpha_const": 0.16}),
    "hr_prop_fridge_light": ((0.95, 0.94, 0.90), 0.40, 0.0, {"emit": (1.0, 0.95, 0.86), "strength": 10.0}),
    "hr_prop_fridge_liner": ((1, 1, 1), 0.40, 0.0, {"image": "shop", "emit_image": True, "strength": 0.6}),
    "hr_prop_laundry": ((1, 1, 1), 0.38, 0.5, {"image": "laundry"}),
    "hr_prop_stainless": ((0.50, 0.50, 0.51), 0.30, 1.0, {}),
    "hr_prop_notices": ((1, 1, 1), 0.80, 0.0, {"image": "notices"}),
    "hr_prop_vehicle": ((1, 1, 1), 0.30, 0.0, {"image": "vehicle"}),
    "hr_prop_car_paint": ((0.020, 0.021, 0.024), 0.32, 0.35, {"coat": 0.8}),
    "hr_prop_van_paint": ((0.075, 0.078, 0.082), 0.42, 0.25, {"coat": 0.5}),
    "hr_prop_litter": ((1, 1, 1), 0.55, 0.0, {"image": "litter"}),
    "hr_prop_mattress": ((1, 1, 1), 0.95, 0.0, {"image": "mattress"}),
    "hr_prop_bin_bag": ((0.010, 0.010, 0.012), 0.28, 0.0, {}),
    "hr_prop_cone": ((0.48, 0.12, 0.03), 0.60, 0.0, {}),
    "hr_prop_reflective": ((0.70, 0.70, 0.68), 0.30, 0.0, {}),
    "hr_prop_ball_white": ((0.66, 0.64, 0.58), 0.50, 0.0, {}),
    "hr_prop_ball_black": ((0.022, 0.022, 0.022), 0.50, 0.0, {}),
    "hr_prop_intercom": ((1, 1, 1), 0.45, 0.8, {"image": "intercom", "normal": True}),
    "hr_prop_cctv": ((1, 1, 1), 0.60, 0.0, {"image": "cctv"}),
    "hr_prop_manhole": ((1, 1, 1), 0.60, 0.6, {"image": "manhole", "normal": True}),
    "hr_prop_vents": ((1, 1, 1), 0.85, 0.0, {"image": "vents", "normal": True}),
    "hr_prop_pegboard": ((1, 1, 1), 0.80, 0.0, {"image": "pegboard"}),
    "hr_prop_fabric": ((1, 1, 1), 0.95, 0.0, {"image": "fabric"}),
    "hr_prop_felt": ((0.050, 0.120, 0.085), 0.95, 0.0, {}),
    "hr_prop_laminate": ((0.42, 0.34, 0.25), 0.45, 0.0, {}),
    "hr_prop_formica_grey": ((0.28, 0.285, 0.29), 0.50, 0.0, {}),
    "hr_prop_plastic_blue": ((0.05, 0.075, 0.13), 0.50, 0.0, {}),
    "hr_prop_plastic_white": ((0.55, 0.55, 0.53), 0.60, 0.0, {}),
    "hr_prop_shelf_paint": ((0.62, 0.62, 0.60), 0.50, 0.1, {}),
    "hr_prop_trolley_plastic": ((0.10, 0.11, 0.14), 0.45, 0.0, {}),
    "hr_prop_dark_void": ((0.004, 0.004, 0.004), 1.00, 0.0, {}),
    "hr_prop_bike_paint": ((0.16, 0.035, 0.03), 0.35, 0.2, {"coat": 0.4}),
    "hr_prop_dish_paint": ((0.52, 0.52, 0.50), 0.50, 0.0, {}),
    "hr_prop_ac_casing": ((0.50, 0.50, 0.48), 0.50, 0.1, {}),
    "hr_prop_pool_red": ((0.36, 0.04, 0.03), 0.20, 0.0, {}),
    "hr_prop_pool_yellow": ((0.62, 0.45, 0.04), 0.20, 0.0, {}),
    "hr_prop_tool_red": ((0.40, 0.05, 0.03), 0.40, 0.0, {}),
    "hr_prop_copper": ((0.55, 0.30, 0.18), 0.40, 1.0, {}),
    "hr_prop_lens_red": ((0.30, 0.012, 0.01), 0.15, 0.0, {}),
    "hr_prop_lens_amber": ((0.55, 0.22, 0.02), 0.15, 0.0, {}),
}


def _principled(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return nt, bsdf


def _image(name, root, kind="color"):
    key = f"heron_props_{name}_{kind}"
    if key in bpy.data.images:
        return bpy.data.images[key]
    path = os.path.join(root, "public", "materials", "heron", "props", f"{name}-{kind}.webp")
    img = bpy.data.images.load(path, check_existing=False)
    img.name = key
    if kind != "color":
        img.colorspace_settings.name = "Non-Color"
    img.pack()
    return img


def make_material(name, spec, root):
    col, rough, metal, opt = spec
    mat = bpy.data.materials.new(name)
    nt, bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    mat.diffuse_color = (*col, 1.0)
    if "specular" in opt:
        bsdf.inputs["Specular IOR Level"].default_value = opt["specular"]
    if "coat" in opt:
        bsdf.inputs["Coat Weight"].default_value = opt["coat"]
        bsdf.inputs["Coat Roughness"].default_value = 0.08
    if "emit" in opt:
        bsdf.inputs["Emission Color"].default_value = (*opt["emit"], 1.0)
        bsdf.inputs["Emission Strength"].default_value = opt["strength"]
    if "image" in opt:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.location = (-400, 100)
        tex.image = _image(opt["image"], root)
        tex.interpolation = "Linear"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if opt.get("emit_image"):
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = opt["strength"]
        if opt.get("alpha"):
            rnd = nt.nodes.new("ShaderNodeMath")
            rnd.operation = "ROUND"
            rnd.location = (-120, -150)
            nt.links.new(tex.outputs["Alpha"], rnd.inputs[0])
            nt.links.new(rnd.outputs[0], bsdf.inputs["Alpha"])
            mat.use_backface_culling = False
            try:
                mat.surface_render_method = "DITHERED"
            except AttributeError:
                pass
        if opt.get("normal"):
            ntex = nt.nodes.new("ShaderNodeTexImage")
            ntex.location = (-400, -250)
            ntex.image = _image(opt["image"], root, "normal")
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nmap.location = (-120, -300)
            nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    if "alpha_const" in opt:
        bsdf.inputs["Alpha"].default_value = opt["alpha_const"]
        mat.use_backface_culling = False
        try:
            mat.surface_render_method = "BLENDED"
        except AttributeError:
            pass
    return mat


def build_all(root):
    mats = {}
    for name, spec in SHARED.items():
        mats[name] = make_material(name, spec, root)
    for name, spec in PROP.items():
        mats[name] = make_material(name, spec, root)
    return mats
