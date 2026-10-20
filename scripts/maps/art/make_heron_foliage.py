"""Build the Heron Reach foliage kit as an editable Blender file.

Run:  python3 scripts/maps/art/make_heron_foliage.py
      (run make_heron_foliage_textures.py first; it writes the WebP textures this packs)

Writes assets/blender/heron-reach/foliage-kit.blend and foliage-manifest.json.
Everything is deterministic: each asset has a fixed seed and the noise fields are
mathutils Perlin noise sampled at fixed offsets.

Trees use space colonisation (Runions, Lane and Prusinkiewicz 2007): attraction points
fill a species crown envelope, branch nodes grow towards the points they are closest to,
with a phototropism bias, then radii follow the pipe model and thin twigs sag under a
gravity pass. Branch chains become tapered tubes with parallel-transport frames and
continuous cylindrical bark UVs. Leaf cards sit on twig nodes, thinned by a 3D noise
field so the autumn canopy is partly bare and clustered.
"""
import json
import math
import os
import random
import sys

import bpy
import bmesh  # noqa: F401  (kept for interactive edits)
from mathutils import Vector, noise
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heron_foliage_atlas import (CLUSTER_LAYOUT, GRASS_COLUMNS, GRASS_TUFTS, HEDGE_LAYOUT,  # noqa: E402
                                 LITTER_CELLS, SIZE, WEED_LAYOUT, rect_uv)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TEX = os.path.join(REPO, "public", "materials", "heron", "foliage")
OUT_DIR = os.path.join(REPO, "assets", "blender", "heron-reach")
BLEND = os.environ.get("HR_FOLIAGE_BLEND") or os.path.join(OUT_DIR, "foliage-kit.blend")
MANIFEST = os.environ.get('HR_FOLIAGE_MANIFEST') or os.path.join(OUT_DIR, "foliage-manifest.json")

Z = Vector((0, 0, 1))


# ======================================================================================
# Mesh builder
# ======================================================================================

class MB:
    """Collects vertices, faces, per-loop UVs, per-vertex custom normals and colours."""

    def __init__(self):
        self.v = []
        self.n = []
        self.c = []
        self.f = []
        self.uv = []
        self.m = []

    def vert(self, co, n=None, col=(1, 1, 1, 1)):
        self.v.append(Vector(co))
        self.n.append(Vector(n).normalized() if n is not None else None)
        self.c.append(col)
        return len(self.v) - 1

    def face(self, idx, uvs, mat=0):
        self.f.append(tuple(idx))
        self.uv.append(tuple(uvs))
        self.m.append(mat)

    def extend(self, other, offset=Vector((0, 0, 0)), rot=None, scale=1.0, mat_map=None):
        base = len(self.v)
        for co, n, c in zip(other.v, other.n, other.c):
            p = co * scale
            nn = n
            if rot is not None:
                p = rot @ p
                nn = (rot @ n) if n is not None else None
            self.v.append(p + offset)
            self.n.append(nn)
            self.c.append(c)
        for f, uv, m in zip(other.f, other.uv, other.m):
            self.f.append(tuple(i + base for i in f))
            self.uv.append(uv)
            self.m.append(mat_map[m] if mat_map else m)

    def tris(self):
        return sum(len(f) - 2 for f in self.f)

    def build(self, name, materials, vcol=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        for m in materials:
            me.materials.append(m)
        uvl = me.uv_layers.new(name="UVMap")
        loop_uvs = []
        for uvs in self.uv:
            loop_uvs.extend(uvs)
        flat = [x for uv in loop_uvs for x in uv]
        uvl.data.foreach_set("uv", flat)
        me.polygons.foreach_set("material_index", self.m)
        me.polygons.foreach_set("use_smooth", [True] * len(self.f))
        if vcol:
            ca = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")
            ca.data.foreach_set("color", [x for c in self.c for x in c])
        me.validate(clean_customdata=False)
        me.update()
        if all(n is not None for n in self.n) and len(self.n) == len(me.vertices):
            me.normals_split_custom_set_from_vertices([tuple(n) for n in self.n])
        return me


def obj(name, me, coll):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


# ======================================================================================
# Materials
# ======================================================================================

def load_img(name, non_color=False):
    path = os.path.join(TEX, name)
    img = bpy.data.images.load(path, check_existing=True)
    img.name = name
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    img.pack()
    return img


def gltf_output_group():
    g = bpy.data.node_groups.get("glTF Material Output")
    if g:
        return g
    g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
    g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    g.nodes.new("NodeGroupInput")
    return g


def make_material(name, color, normal, orm=None, alpha=False, rough=0.7, nstrength=1.0, vcol=False,
                  spec=0.5, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = load_img(color)
    tc.location = (-500, 200)
    if vcol:
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        vc.location = (-500, 450)
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        mx.location = (-150, 300)
        nt.links.new(tc.outputs["Color"], mx.inputs[6])
        nt.links.new(vc.outputs["Color"], mx.inputs[7])
        nt.links.new(mx.outputs[2], bsdf.inputs["Base Color"])
    else:
        nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:
        rnd = nt.nodes.new("ShaderNodeMath")
        rnd.operation = "ROUND"
        rnd.location = (-150, 50)
        nt.links.new(tc.outputs["Alpha"], rnd.inputs[0])
        nt.links.new(rnd.outputs[0], bsdf.inputs["Alpha"])
        mat.use_backface_culling = False
        mat.alpha_threshold = 0.5
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "DITHERED"
    else:
        mat.use_backface_culling = True
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = load_img(normal, non_color=True)
    tn.location = (-500, -250)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = nstrength
    nm.location = (-150, -250)
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if orm:
        to = nt.nodes.new("ShaderNodeTexImage")
        to.image = load_img(orm, non_color=True)
        to.location = (-500, -550)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-200, -550)
        nt.links.new(to.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
        grp = nt.nodes.new("ShaderNodeGroup")
        grp.node_tree = gltf_output_group()
        grp.location = (300, -500)
        nt.links.new(sep.outputs["Red"], grp.inputs["Occlusion"])
    else:
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    if coat and "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.25
    return mat


def build_materials():
    M = {}
    M["hr_bark_plane"] = make_material("hr_bark_plane", "plane-bark-color.webp", "plane-bark-normal.webp",
                                       "plane-bark-orm.webp", nstrength=1.0, vcol=True)
    M["hr_bark_birch"] = make_material("hr_bark_birch", "birch-bark-color.webp", "birch-bark-normal.webp",
                                       "birch-bark-orm.webp", nstrength=0.8, vcol=True)
    M["hr_leaf_plane"] = make_material("hr_leaf_plane", "plane-leaf-atlas-color.webp", "plane-leaf-atlas-normal.webp",
                                       alpha=True, rough=0.55, nstrength=0.8, spec=0.4)
    M["hr_leaf_birch"] = make_material("hr_leaf_birch", "birch-leaf-atlas-color.webp", "birch-leaf-atlas-normal.webp",
                                       alpha=True, rough=0.5, nstrength=0.7, spec=0.4)
    M["hr_grass_blade"] = make_material("hr_grass_blade", "grass-blades-color.webp", "grass-blades-normal.webp",
                                        alpha=True, rough=0.55, nstrength=0.8, spec=0.45)
    M["hr_shrub_leaf"] = make_material("hr_shrub_leaf", "shrub-leaf-atlas-color.webp", "shrub-leaf-atlas-normal.webp",
                                       alpha=True, rough=0.38, nstrength=0.8, spec=0.5)
    M["hr_hedge_leaf"] = make_material("hr_hedge_leaf", "hedge-leaf-atlas-color.webp", "hedge-leaf-atlas-normal.webp",
                                       alpha=True, rough=0.48, nstrength=0.9, spec=0.4)
    M["hr_leaf_litter"] = make_material("hr_leaf_litter", "leaf-litter-color.webp", "leaf-litter-normal.webp",
                                        alpha=True, rough=0.3, nstrength=1.0, spec=0.5)
    M["hr_weed"] = make_material("hr_weed", "weeds-color.webp", "weeds-normal.webp", alpha=True, rough=0.5,
                                 nstrength=0.8, spec=0.45)
    return M


# ======================================================================================
# Shared geometry helpers
# ======================================================================================

def perp(v):
    a = Vector((1, 0, 0)) if abs(v.x) < 0.9 else Vector((0, 1, 0))
    return v.cross(a).normalized()


def lerp(a, b, t):
    return a + (b - a) * t


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def tube(mb, pts, radii, sides, mat=0, u_rep=1, v_scale=1.0, v0=0.0, radial_fn=None, col_fn=None, tip=True):
    """Tapered tube along pts with parallel-transport frames. Seam vertices are duplicated so
    U runs 0..u_rep continuously around the branch; V follows arc length."""
    n = len(pts)
    if n < 2:
        return
    T = []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = (b - a)
        T.append(t.normalized() if t.length > 1e-9 else Z.copy())
    N = [perp(T[0])]
    for i in range(1, n):
        prev = N[-1]
        q = prev - T[i] * prev.dot(T[i])
        N.append(q.normalized() if q.length > 1e-6 else perp(T[i]))
    s = v0
    rings = []
    last = n - 1 if tip else n
    for i in range(last):
        if i > 0:
            s += (pts[i] - pts[i - 1]).length
        B = T[i].cross(N[i])
        ring = []
        for j in range(sides + 1):
            ang = 2 * math.pi * (j % sides) / sides
            d = N[i] * math.cos(ang) + B * math.sin(ang)
            r = radii[i]
            if radial_fn:
                r = radial_fn(i, ang, d, r)
            co = pts[i] + d * r
            col = col_fn(co, radii[i]) if col_fn else (1, 1, 1, 1)
            ring.append((mb.vert(co, d, col), (u_rep * j / sides, s * v_scale)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for j in range(sides):
            a, b = r0[j], r0[j + 1]
            c, d = r1[j + 1], r1[j]
            mb.face([a[0], b[0], c[0], d[0]], [a[1], b[1], c[1], d[1]], mat)
    if tip:
        s += (pts[-1] - pts[-2]).length
        col = col_fn(pts[-1], radii[-1]) if col_fn else (1, 1, 1, 1)
        r0 = rings[-1]
        for j in range(sides):
            apex = mb.vert(pts[-1], T[-1], col)
            a, b = r0[j], r0[j + 1]
            mb.face([a[0], b[0], apex], [a[1], b[1], (u_rep * (j + 0.5) / sides, s * v_scale)], mat)


def card(mb, P, up, nrm, w, h, rect, pivot, mat=0, bend=0.0, rows=3, normal_fn=None, gravity=None):
    """Alpha card whose atlas pivot sits at P; `up` runs from pivot to the top of the cell."""
    up = up.normalized()
    side = up.cross(nrm)
    if side.length < 1e-6:
        side = perp(up)
    side.normalize()
    nrm = side.cross(up).normalized()
    px, py = pivot
    g = gravity if gravity is not None else -Z
    idx = []
    for r in range(rows):
        fy = 1.0 - r / (rows - 1)  # bottom row first
        along = (py - fy) * h
        t = max(0.0, along / max(h * py, 1e-6))
        row = []
        for fx in (0.0, 1.0):
            co = P + side * ((fx - px) * w) + up * along + g * (bend * h * t * t)
            nn = normal_fn(co, nrm) if normal_fn else nrm
            row.append((mb.vert(co, nn), rect_uv(rect, fx, fy)))
        idx.append(row)
    for r in range(rows - 1):
        a, b = idx[r][0], idx[r][1]
        c, d = idx[r + 1][1], idx[r + 1][0]
        mb.face([a[0], b[0], c[0], d[0]], [a[1], b[1], c[1], d[1]], mat)


def mesh_bounds(mb):
    xs = [v.x for v in mb.v]
    ys = [v.y for v in mb.v]
    zs = [v.z for v in mb.v]
    return [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)], [round(max(xs), 3), round(max(ys), 3),
                                                                       round(max(zs), 3)]


# ======================================================================================
# Trees: space colonisation
# ======================================================================================

TREES = {
    "TREE_PLANE_A": dict(species="plane", seed=7101, H=7.8, Rmax=2.05, zb=2.85, trunk_top=2.65, leader=4.6, lean=(0.03, -0.01),
                         n_attr=1500, di=1.05, dk=0.26, D=0.15, trop=0.10, blobs=8, blob_size=1.0, r_tip=0.006, r_base=0.22, sag=0.07,
                         shape=(1.1, 0.55), offset=(0.0, 0.0), leaf_r=0.016, leaf_noise=0.45, leaf_bias=0.0,
                         cards=950, flare=0.85),
    "TREE_PLANE_B": dict(species="plane", seed=7202, H=7.3, Rmax=2.0, zb=2.9, trunk_top=2.7, leader=4.0, lean=(-0.02, 0.03),
                         n_attr=1450, di=1.05, dk=0.26, D=0.15, trop=0.14, blobs=7, blob_size=1.05, r_tip=0.006, r_base=0.23, sag=0.06,
                         shape=(0.95, 0.6), offset=(0.2, -0.15), leaf_r=0.016, leaf_noise=0.5, leaf_bias=-0.1,
                         cards=880, flare=0.9),
    "TREE_BIRCH_A": dict(species="birch", seed=7303, H=7.5, Rmax=1.75, zb=2.95, trunk_top=2.6, leader=6.3, lean=(0.02, 0.02),
                         n_attr=1300, di=0.95, dk=0.22, D=0.14, trop=0.16, blobs=6, blob_size=0.7, r_tip=0.0045, r_base=0.175, sag=0.26,
                         shape=(0.6, 0.95), offset=(0.0, 0.0), leaf_r=0.012, leaf_noise=0.45, leaf_bias=0.05,
                         cards=1100, flare=0.55),
    "TREE_BIRCH_B": dict(species="birch", seed=7404, H=6.7, Rmax=1.6, zb=2.9, trunk_top=2.55, leader=5.6, lean=(-0.04, 0.0),
                         n_attr=1150, di=0.95, dk=0.22, D=0.14, trop=0.14, blobs=5, blob_size=0.7, r_tip=0.0045, r_base=0.165, sag=0.3,
                         shape=(0.55, 1.0), offset=(-0.15, 0.1), leaf_r=0.012, leaf_noise=0.5, leaf_bias=-0.05,
                         cards=1000, flare=0.5),
}


def crown_radius(p, h):
    a, b = p["shape"]
    return p["Rmax"] * max(0.0, math.sin(math.pi * min(1.0, max(0.0, h)) ** a)) ** b


def crown_blobs(p, rng):
    """Limb-scale sub-crowns: each major limb carries its own rounded mass of foliage."""
    blobs = []
    H, zb = p["H"], p["zb"]
    for k in range(p.get("blobs", 0)):
        h = rng.uniform(0.25, 0.85)
        z = zb + h * (H - zb)
        R = crown_radius(p, h)
        a = rng.uniform(0, 2 * math.pi)
        r = R * rng.uniform(0.45, 0.85)
        size = rng.uniform(0.75, 1.3) * p.get("blob_size", 1.0)
        blobs.append((Vector((math.cos(a) * r, math.sin(a) * r, z)), size))
    return blobs


def sample_attractors(p, rng):
    pts = []
    H, zb = p["H"], p["zb"]
    ox, oy = p["offset"]
    seed_off = Vector((p["seed"] * 0.013, 3.1, 7.7))
    blobs = crown_blobs(p, rng)
    tries = 0
    while blobs and len(pts) < p["n_attr"] * 0.6 and tries < 200000:
        tries += 1
        c, sz = blobs[rng.randrange(len(blobs))]
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        if d.length > 1:
            continue
        q = c + Vector((d.x * sz, d.y * sz, d.z * sz * 0.8))
        if q.z < zb or q.z > H - 0.1 or q.length < 0.3:
            continue
        # outer part of each blob carries the leaves
        if rng.random() > 0.35 + 0.65 * d.length ** 2:
            continue
        pts.append(q)
    tries = 0
    while len(pts) < p["n_attr"] and tries < 200000:
        tries += 1
        x = rng.uniform(-p["Rmax"], p["Rmax"])
        y = rng.uniform(-p["Rmax"], p["Rmax"])
        z = rng.uniform(zb, H - 0.15)
        h = (z - zb) / (H - zb)
        ang = math.atan2(y - oy * h, x - ox * h)
        lobe = 1.0 + 0.45 * noise.noise(Vector((math.cos(ang) * 1.1, math.sin(ang) * 1.1, h * 1.8)) + seed_off)
        R = crown_radius(p, h) * lobe
        r = math.hypot(x - ox * h, y - oy * h)
        if r > R:
            continue
        # bias towards the outer shell, where the foliage lives
        if rng.random() > 0.5 + 0.5 * (r / max(R, 1e-3)) ** 1.5:
            continue
        clump = noise.noise(Vector((x, y, z)) * 0.8 + seed_off * 2.0)
        if rng.random() > smooth01(0.55 + clump):
            continue
        pts.append(Vector((x, y, z)))
    return pts


def colonise(p, rng):
    D = p["D"]
    pos, parent, grow = [], [], []
    # trunk: straight leader with a slight lean and wobble up to the crown
    z = -0.06
    lx, ly = p["lean"]
    cur = Vector((0, 0, z))
    pos.append(cur.copy())
    parent.append(-1)
    grow.append(False)
    while cur.z < p["leader"]:
        w = noise.noise(Vector((cur.z * 0.7, p["seed"] * 0.01, 0.5)))
        wob = (0.04 if cur.z < p["trunk_top"] else 0.12) * (1.6 if p["species"] == "birch" else 1.0)
        step = Vector((lx + wob * w, ly + wob * noise.noise(Vector((0.3, cur.z * 0.7, p["seed"] * 0.01))), 1.0))
        cur = cur + step.normalized() * D
        pos.append(cur.copy())
        parent.append(len(pos) - 2)
        # the leader can sprout laterals once it is above the clearance height
        grow.append(cur.z >= p["trunk_top"] + 0.1)
    grow[-1] = True
    attrs = sample_attractors(p, rng)
    children = {}
    trop = Vector((0, 0, p["trop"]))
    for it in range(400):
        if not attrs:
            break
        kd = KDTree(len(pos))
        cnt = 0
        for i, q in enumerate(pos):
            if grow[i]:
                kd.insert(q, i)
                cnt += 1
        if cnt == 0:
            break
        kd.balance()
        infl = {}
        alive = []
        for a in attrs:
            co, idx, dist = kd.find(a)
            if idx is None:
                alive.append(a)
                continue
            if dist < p["dk"]:
                continue
            alive.append(a)
            if dist < p["di"]:
                v = (a - co).normalized()
                if idx in infl:
                    infl[idx][0] += v
                    infl[idx][1] += 1
                else:
                    infl[idx] = [v, 1]
        attrs = alive
        if not infl:
            break
        added = 0
        for idx in sorted(infl):
            v, c = infl[idx]
            d = v / c
            if d.length < 0.2:
                d = d + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.1))
            d = d.normalized() + trop
            d.normalize()
            npos = pos[idx] + d * D
            ok = True
            for ch in children.get(idx, []):
                if (pos[ch] - npos).length < 0.35 * D:
                    ok = False
                    break
            if not ok:
                continue
            pos.append(npos)
            parent.append(idx)
            grow.append(True)
            children.setdefault(idx, []).append(len(pos) - 1)
            added += 1
        if added == 0:
            break
        if len(pos) > 9000:
            break
    return pos, parent


def pipe_radii(parent, r_tip, r_target, root_idx):
    n = len(parent)
    kids = [[] for _ in range(n)]
    for i, pa in enumerate(parent):
        if pa >= 0:
            kids[pa].append(i)

    def solve(e):
        acc = [0.0] * n
        for i in range(n - 1, -1, -1):
            if not kids[i]:
                acc[i] = r_tip ** e
            else:
                acc[i] = sum(acc[k] for k in kids[i])
        return [a ** (1.0 / e) for a in acc]

    lo, hi = 1.4, 3.5
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        r = solve(mid)
        if r[root_idx] > r_target:
            lo = mid
        else:
            hi = mid
    r = solve(0.5 * (lo + hi))
    return r, kids


def build_tree_skeleton(name, p):
    rng = random.Random(p["seed"])
    pos, parent = colonise(p, rng)
    # radius at the first node above the flare zone is the trunk reference
    ref = next(i for i, q in enumerate(pos) if q.z > 0.3)
    radii, kids = pipe_radii(parent, p["r_tip"], p["r_base"], ref)
    # gentle extra taper up the trunk so it does not read as a pipe
    for i, q in enumerate(pos):
        if radii[i] > 0.05:
            radii[i] *= 1.0 + 0.12 * max(0.0, 1.0 - q.z / 3.0) - 0.1 * min(1.0, max(0.0, (q.z - 2.5) / 3.0))
    # gravity: thin wood sags; propagate parent-first
    new = list(pos)
    for i in range(1, len(pos)):
        pa = parent[i]
        seg = pos[i] - pos[pa]
        L = seg.length
        d = seg.normalized()
        w = min(1.0, (0.02 / max(radii[i], 1e-4)) ** 0.7)
        if radii[i] > 0.06:
            w = 0.0
        d = (d - Z * (p["sag"] * w * (1.0 - 0.5 * max(0.0, d.z)))).normalized()
        new[i] = new[pa] + d * L
    pos = new
    # clearance: prune any non-trunk wood that drops below the canopy base clearance
    trunk_set = set()
    i = 0
    while True:
        trunk_set.add(i)
        if not kids[i]:
            break
        i = max(kids[i], key=lambda k: radii[k])
        if pos[i].z > p["trunk_top"] + 0.2:
            break
    keep = [True] * len(pos)
    for i in range(1, len(pos)):
        if not keep[parent[i]]:
            keep[i] = False
        elif i not in trunk_set and pos[i].z < 2.78:
            keep[i] = False
    return pos, parent, radii, kids, keep


def chains_from(pos, parent, radii, kids, keep):
    """Split the node tree into branch chains: each chain follows its thickest child."""
    chains = []
    stack = [(0, None)]
    while stack:
        start, pa = stack.pop()
        chain = [pa] if pa is not None else []
        i = start
        while True:
            chain.append(i)
            ks = [k for k in kids[i] if keep[k]]
            if not ks:
                break
            ks.sort(key=lambda k: -radii[k])
            for k in ks[1:]:
                stack.append((k, i))
            i = ks[0]
        chains.append(chain)
    return chains


def smooth_chain_positions(pos, chains, iters=3):
    pos = list(pos)
    for ch in chains:
        for _ in range(iters):
            pts = [pos[i] for i in ch]
            for k in range(2, len(ch) - 1):
                pos[ch[k]] = pts[k] * 0.5 + (pts[k - 1] + pts[k + 1]) * 0.25
    return pos


def sides_for(r, lod):
    table = [(0.12, 14), (0.06, 9), (0.03, 7), (0.015, 5), (0.007, 4), (0.0, 3)] if lod == 0 else \
            [(0.12, 8), (0.05, 6), (0.02, 4), (0.0, 3)]
    for thr, s in table:
        if r >= thr:
            return s
    return 3


def tree_bark(p, pos, chains, radii, lod, mat_index=0):
    mb = MB()
    birch = p["species"] == "birch"
    seed_off = Vector((p["seed"] * 0.01, 1.7, 4.2))
    min_r = 0.0 if lod == 0 else 0.008
    min_r0 = 0.0035 if lod == 0 else 0.008

    def col_fn(co, r):
        if birch:
            # thin twigs are dark red-brown; base of the trunk carries black fissured bark
            t = smooth01((r - 0.008) / 0.03)
            twig = (0.36, 0.25, 0.21)
            c = [lerp(twig[k], 1.0, t) for k in range(3)]
            if co.z < 2.1:
                n = noise.noise(Vector((co.x * 7, co.y * 7, co.z * 3.0)) + seed_off)
                dark = smooth01((2.0 - co.z) / 1.5)
                d = smooth01((dark + 0.5 * n) * 2.2 - 0.55)
                c = [x * (1 - 0.88 * d) for x in c]
            return (c[0], c[1], c[2], 1.0)
        t = smooth01((r - 0.006) / 0.04)
        twig = (0.62, 0.55, 0.48)
        c = [lerp(twig[k], 1.0, t) for k in range(3)]
        if co.z < 0.6:
            g = 0.75 + 0.25 * smooth01(co.z / 0.6)  # damp soil splash at the root flare
            c = [x * g for x in c]
        return (c[0], c[1], c[2], 1.0)

    for ci, ch in enumerate(chains):
        r0 = radii[ch[1]] if len(ch) > 1 else radii[ch[0]]
        if r0 < min_r0:
            continue
        is_trunk = ci == 0
        # resample: keep nodes once the accumulated length reaches a radius-dependent step
        step = max(0.12, min(0.42, 3.5 * r0 + 0.12)) * (1.0 if lod == 0 else 1.7)
        keep = [ch[0]]
        acc = 0.0
        for k in range(1, len(ch)):
            acc += (pos[ch[k]] - pos[ch[k - 1]]).length
            force = is_trunk and lod == 0 and (pos[ch[k]].z < 0.7 or (birch and pos[ch[k]].z < 2.1 and k % 2 == 0))
            if acc >= step or k == len(ch) - 1 or force:
                if radii[ch[k]] < min_r and k != len(ch) - 1:
                    continue
                keep.append(ch[k])
                acc = 0.0
        if len(keep) < 2:
            continue
        pts = [pos[i] for i in keep]
        rr = [radii[i] for i in keep]
        if not is_trunk:
            rr[0] = min(rr[0], radii[keep[1]] * 1.05)
        sides = sides_for(r0, lod)
        if is_trunk:
            sides = 16 if lod == 0 else 9
        circ = 2 * math.pi * max(r0, 1e-3)
        u_rep = max(1, round(circ / 1.0))
        v_scale = u_rep / circ
        radial_fn = None
        if is_trunk:
            fl = p["flare"]
            ph = (p["seed"] % 100) * 0.07

            def radial_fn(i, ang, d, r, pts=pts, fl=fl, ph=ph):
                zz = pts[i].z
                lobe = max(0.0, math.cos(5 * (ang + ph) + 0.6 * math.sin(3 * ang))) ** 2
                f = 1.0 + fl * math.exp(-max(zz, 0.0) / 0.2) * (0.35 + 0.65 * lobe)
                bump = 1.0 + 0.05 * noise.noise(Vector((d.x * 2.0, d.y * 2.0, zz * 1.5)) + seed_off)
                return r * f * bump
        tip = radii[keep[-1]] < 0.02
        tube(mb, pts, rr, sides, mat_index, u_rep, v_scale, v0=(ci * 0.37) % 1.0, radial_fn=radial_fn,
             col_fn=col_fn, tip=tip)
    return mb


def tree_leaves(p, pos, parent, radii, kids, keep, lod, rng_seed):
    rng = random.Random(rng_seed)
    birch = p["species"] == "birch"
    mb = MB()
    seed_off = Vector((p["seed"] * 0.021, 9.3, 2.2))
    centre = Vector((p["offset"][0] * 0.5, p["offset"][1] * 0.5, p["zb"] + (p["H"] - p["zb"]) * 0.45))
    cand = []
    for i in range(1, len(pos)):
        if not keep[i] or radii[i] > p["leaf_r"] or pos[i].z < p["zb"] - 0.1:
            continue
        tipness = 1.0 if not [k for k in kids[i] if keep[k]] else 0.55
        f = noise.noise(pos[i] * 0.9 + seed_off) + 0.5 * noise.noise(pos[i] * 2.3 + seed_off * 1.7)
        dens = smooth01((f + p["leaf_bias"] + p["leaf_noise"]) / (2 * p["leaf_noise"]))
        cand.append((i, dens * tipness))
    target = p["cards"] if lod == 0 else int(p["cards"] * 0.6)
    tot = sum(w for _, w in cand) + 1e-6
    scale = target / tot
    cells_c = CLUSTER_LAYOUT["cluster"]
    cells_s = CLUSTER_LAYOUT["single"]

    def nfn(co, nrm):
        rad = (co - centre)
        rad.z *= 0.6
        rad = rad.normalized() + Z * 0.35
        nn = nrm if nrm.dot(rad) >= 0 else -nrm
        return (nn * 0.45 + rad.normalized() * 0.55).normalized()

    count = 0
    for i, w in cand:
        k = w * scale
        n = int(k) + (1 if rng.random() < (k - int(k)) else 0)
        for _ in range(n):
            P = pos[i]
            pa = parent[i]
            tw = (pos[i] - pos[pa]).normalized()
            out = (P - centre)
            out.z = 0
            out = out.normalized() if out.length > 1e-4 else Vector((1, 0, 0))
            if birch:
                up = (tw * 0.45 + out * 0.35 - Z * 0.9 + Vector((rng.gauss(0, 0.35), rng.gauss(0, 0.35), rng.gauss(0, 0.2))))
            else:
                up = (tw * 0.8 + out * 0.45 + Z * 0.15 + Vector((rng.gauss(0, 0.45), rng.gauss(0, 0.45), rng.gauss(0, 0.3))))
            up.normalize()
            nrm = (Z * 0.8 + out * 0.5 + Vector((rng.gauss(0, 0.5), rng.gauss(0, 0.5), rng.gauss(0, 0.3))))
            nrm = (nrm - up * nrm.dot(up))
            if nrm.length < 1e-3:
                nrm = perp(up)
            nrm.normalize()
            if rng.random() < ((0.72 if not birch else 0.6) if lod == 0 else 1.0):
                cell = cells_c[rng.randrange(len(cells_c))]
                size = rng.uniform(0.42, 0.55) if not birch else rng.uniform(0.24, 0.32)
            else:
                cell = cells_s[rng.randrange(len(cells_s))]
                size = rng.uniform(0.2, 0.26) if not birch else rng.uniform(0.13, 0.17)
            if lod == 1:
                size *= 1.45
            if P.z - size < 2.85:  # keep the walk-under clearance free of hanging cards
                continue
            P2 = P + Vector((rng.gauss(0, 0.03), rng.gauss(0, 0.03), rng.gauss(0, 0.03)))
            card(mb, P2, up, nrm, size, size, cell["rect"], cell["pivot"], 0,
                 bend=(rng.uniform(0.05, 0.18) if lod == 0 else 0.0), rows=(3 if lod == 0 else 2), normal_fn=nfn)
            count += 1
    return mb, count


def trunk_collision(pos, chains, radii, p):
    trunk = chains[0]
    best = 0.0
    for i in trunk:
        if 0.3 <= pos[i].z <= 2.0:
            best = max(best, radii[i])
    base = radii[trunk[1]] * (1 + p["flare"])
    return round(best * 1.05, 3), round(base, 3)


# ======================================================================================
# Grass, weeds, litter
# ======================================================================================

def blade(mb, base, h, w, phi, bend, col_idx, rng, mat=0, segs=4):
    """One curved tapered blade mapped to an atlas column."""
    rect = GRASS_COLUMNS[col_idx]["rect"]
    x, y, cw, ch = rect
    m = 3.5 / cw
    dirh = Vector((math.cos(phi), math.sin(phi), 0))
    side = Vector((-math.sin(phi), math.cos(phi), 0))
    twist = rng.uniform(-0.6, 0.6)
    pts = [base.copy()]
    ang0 = rng.uniform(0.1, 0.5)
    p = base.copy()
    for s in range(1, segs + 1):
        t = s / segs
        a = ang0 + bend * t * t * 1.6
        d = Z * math.cos(a) + dirh * math.sin(a)
        p = p + d * (h / segs)
        pts.append(p.copy())
    rows = []
    for s, q in enumerate(pts):
        t = s / segs
        if s == segs:
            nrm = (Z * 0.7 + dirh * 0.3)
            rows.append([(mb.vert(q, nrm.normalized()), rect_uv(rect, 0.5, 0.004))])
            break
        ww = w * (1 - 0.55 * t)
        sd = (side * math.cos(twist * t) + dirh * math.sin(twist * t)).normalized()
        nrm = (Z * 0.65 + dirh * 0.35).normalized()
        fy = 1 - t * 0.996 - 0.002
        rows.append([(mb.vert(q - sd * ww * 0.5, nrm), rect_uv(rect, m, fy)),
                     (mb.vert(q + sd * ww * 0.5, nrm), rect_uv(rect, 1 - m, fy))])
    for s in range(segs - 1):
        a, b = rows[s]
        d, c = rows[s + 1]
        # Upper blade surface is front-facing; retain each corner's existing UV.
        # Authored upward lighting normals remain independent of the blade bend.
        mb.face([d[0], c[0], b[0], a[0]], [d[1], c[1], b[1], a[1]], mat)
    a, b = rows[segs - 1]
    t = rows[segs][0]
    mb.face([t[0], b[0], a[0]], [t[1], b[1], a[1]], mat)


GRASS_CLUMPS = {
    "GRASS_CLUMP_A": dict(seed=8101, n=20, h=(0.12, 0.22), w=(0.008, 0.011), spread=0.08, bend=(0.5, 1.2)),
    "GRASS_CLUMP_B": dict(seed=8202, n=24, h=(0.18, 0.45), w=(0.007, 0.011), spread=0.08, bend=(0.5, 1.3)),
    "GRASS_CLUMP_C": dict(seed=8303, n=28, h=(0.12, 0.17), w=(0.008, 0.012), spread=0.09, bend=(0.5, 1.4)),
    "GRASS_CLUMP_D": dict(seed=8404, n=12, h=(0.25, 0.42), w=(0.006, 0.009), spread=0.05, bend=(0.5, 1.2)),
}


def grass_clump(spec):
    rng = random.Random(spec["seed"])
    mb = MB()
    for b in range(spec["n"]):
        r = spec["spread"] * math.sqrt(rng.random())
        a = rng.uniform(0, 2 * math.pi)
        base = Vector((math.cos(a) * r, math.sin(a) * r, -0.005))
        phi = a + rng.gauss(0, 0.6)
        h = rng.uniform(*spec["h"])
        col = rng.randrange(len(GRASS_COLUMNS))
        blade(mb, base, h, rng.uniform(*spec["w"]), phi, rng.uniform(*spec["bend"]), col, rng)
    return mb


def rotz(a):
    from mathutils import Matrix
    return Matrix.Rotation(a, 3, "Z")


def grass_patch(clumps, seed, grid=5, names=("GRASS_CLUMP_A", "GRASS_CLUMP_C", "GRASS_CLUMP_B"), fillers=60):
    rng = random.Random(seed)
    mb = MB()
    cellw = 1.0 / grid
    for gy in range(grid):
        for gx in range(grid):
            x = -0.5 + (gx + rng.uniform(0.15, 0.85)) * cellw
            y = -0.5 + (gy + rng.uniform(0.15, 0.85)) * cellw
            nm = names[0] if rng.random() < 0.45 else (names[1] if rng.random() < 0.7 else names[2])
            mb.extend(clumps[nm], Vector((x, y, 0)), rotz(rng.uniform(0, 6.283)), rng.uniform(0.85, 1.15))
    # filler: low crossed tuft cards between the modelled clumps so the lawn reads as turf
    for k in range(fillers):
        x, y = rng.uniform(-0.48, 0.48), rng.uniform(-0.48, 0.48)
        cell = GRASS_TUFTS[rng.randrange(2)]
        a = rng.uniform(0, math.pi)
        hgt = rng.uniform(0.1, 0.17)
        for j in range(2):
            nrm = Vector((math.cos(a + j * math.pi / 2), math.sin(a + j * math.pi / 2), 0))
            card(mb, Vector((x, y, -0.01)), Z, nrm, hgt * 0.75, hgt, cell["rect"], cell["pivot"], 0, rows=2,
                 normal_fn=lambda co, nn: (Z * 0.75 + nn * 0.25).normalized())
    return mb


def grass_edge(clumps, seed):
    rng = random.Random(seed)
    mb = MB()
    for k in range(8):
        x = -0.5 + (k + rng.uniform(0.1, 0.9)) / 8
        y = rng.uniform(-0.07, 0.07)
        nm = "GRASS_CLUMP_D" if rng.random() < 0.4 else "GRASS_CLUMP_A"
        mb.extend(clumps[nm], Vector((x, y, 0)), rotz(rng.uniform(0, 6.283)), rng.uniform(0.6, 1.0))
    return mb


def strip_leaf(mb, base, phi, L, Wd, rise, droop, rect, mat, segs=3):
    """Flat-ish leaf strip (rosette leaves) from base outwards, mapped bottom to top of rect."""
    dirh = Vector((math.cos(phi), math.sin(phi), 0))
    side = Vector((-math.sin(phi), math.cos(phi), 0))
    rows = []
    for s in range(segs + 1):
        t = s / segs
        co = base + dirh * (L * t) + Z * (rise * math.sin(math.pi * t * 0.8) - droop * t * t)
        nrm = (Z * 0.9 + dirh * 0.1).normalized()
        rows.append([(mb.vert(co - side * Wd * 0.5, nrm), rect_uv(rect, 0.0, 1 - t)),
                     (mb.vert(co + side * Wd * 0.5, nrm), rect_uv(rect, 1.0, 1 - t))])
    for s in range(segs):
        a, b = rows[s]
        d, c = rows[s + 1]
        # Rosette upper surface faces +Z, consistent with its authored upward normals.
        # Reverse corners and their UVs together; upright cross_cards stay unchanged.
        mb.face([d[0], c[0], b[0], a[0]], [d[1], c[1], b[1], a[1]], mat)


def cross_cards(mb, rect, pivot, w, h, n, rng, mat, yaw0=0.0):
    for k in range(n):
        a = yaw0 + k * math.pi / n + rng.uniform(-0.2, 0.2)
        nrm = Vector((math.cos(a), math.sin(a), 0))
        up = (Z + Vector((rng.gauss(0, 0.1), rng.gauss(0, 0.1), 0))).normalized()
        card(mb, Vector((0, 0, -0.01)), up, nrm, w, h, rect, pivot, mat, bend=0.0, rows=2,
             normal_fn=lambda co, nn: (nn * 0.3 + Z * 0.7).normalized())


def weed_tuft(kind, seed):
    rng = random.Random(seed)
    mb = MB()  # material 0 = hr_weed, 1 = hr_grass_blade
    W = WEED_LAYOUT
    if kind == "A":  # dandelion rosette with two plantain leaves
        n = 9
        for k in range(n):
            phi = k * 2 * math.pi / n + rng.uniform(-0.2, 0.2)
            cell = W["dandelion"][rng.randrange(4)]
            L = rng.uniform(0.11, 0.17)
            strip_leaf(mb, Vector((0, 0, 0.004)), phi, L, L * 0.25, rng.uniform(0.01, 0.025), 0.012,
                       cell["rect"], 0)
        for k in range(2):
            cell = W["plantain"][rng.randrange(4)]
            L = rng.uniform(0.1, 0.13)
            strip_leaf(mb, Vector((0, 0, 0.006)), rng.uniform(0, 6.28), L, L * 0.23, 0.03, 0.01, cell["rect"], 0)
    elif kind == "B":  # paving-crack grass weed: crossed tuft cards plus real blades
        cross_cards(mb, W["crack"]["rect"], W["crack"]["pivot"], 0.24, 0.24, 3, rng, 0)
        for b in range(6):
            a = rng.uniform(0, 6.283)
            blade(mb, Vector((math.cos(a) * 0.015, math.sin(a) * 0.015, -0.004)), rng.uniform(0.08, 0.16), 0.006,
                  a, rng.uniform(0.4, 1.0), rng.randrange(12), rng, mat=1, segs=3)
    else:  # wall-base weed: herb sprig cards plus a small rosette
        cross_cards(mb, W["herb"]["rect"], W["herb"]["pivot"], 0.32, 0.32, 3, rng, 0)
        for k in range(5):
            phi = k * 2 * math.pi / 5 + rng.uniform(-0.3, 0.3)
            cell = W["plantain"][rng.randrange(4)]
            L = rng.uniform(0.08, 0.12)
            strip_leaf(mb, Vector((0, 0, 0.004)), phi, L, L * 0.23, 0.02, 0.01, cell["rect"], 0)
    return mb


def leaf_litter(kind, seed):
    rng = random.Random(seed)
    mb = MB()
    n = {"A": 230, "B": 150, "C": 60}[kind]
    zc = 0.005
    blobs = [(rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4)) for _ in range(4)]
    k = 0
    tries = 0
    while k < n and tries < 20000:
        tries += 1
        x, y = rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)
        if kind == "A":  # gutter drift: dense along -Y edge, thinning out
            if rng.random() > math.exp(-(y + 0.5) / 0.28):
                continue
        elif kind == "B":  # clumps blown into small heaps
            d = min(math.hypot(x - bx, y - by) for bx, by in blobs)
            if rng.random() > 0.25 + 0.75 * math.exp(-(d / 0.18) ** 2):
                continue
        cell = LITTER_CELLS[rng.randrange(len(LITTER_CELLS))]
        sz = rng.uniform(0.17, 0.26) if cell["kind"] == "plane" else rng.uniform(0.11, 0.15)
        a = rng.uniform(0, 2 * math.pi)
        u = Vector((math.cos(a), math.sin(a), 0))
        v = Vector((-math.sin(a), math.cos(a), 0))
        c = Vector((x, y, zc + 0.00012 * k))
        curl = rng.uniform(0.0, 0.012)
        fold = rng.uniform(-0.004, 0.008)
        grid = []
        for iy, fy in enumerate((1.0, 0.5, 0.0)):
            row = []
            for ix, fx in enumerate((0.0, 0.5, 1.0)):
                lift = curl * ((fx - 0.5) * 2) ** 2 + (fold if ix == 1 else 0.0) * 0.0
                lift += (curl * 0.6) * ((0.5 - fy) * 2) ** 2
                if ix == 1:
                    lift = max(0.0, lift - fold)
                co = c + u * ((fx - 0.5) * sz) + v * ((0.5 - fy) * sz) + Z * lift
                row.append((mb.vert(co, Z), rect_uv(cell["rect"], fx, fy)))
            grid.append(row)
        for iy in range(2):
            for ix in range(2):
                a0, b0 = grid[iy][ix], grid[iy][ix + 1]
                c0, d0 = grid[iy + 1][ix + 1], grid[iy + 1][ix]
                mb.face([a0[0], b0[0], c0[0], d0[0]], [a0[1], b0[1], c0[1], d0[1]], 0)
        k += 1
    return mb


# ======================================================================================
# Shrubs and hedges
# ======================================================================================

SHRUBS = {
    "SHRUB_A": dict(seed=9101, H=0.56, R=0.45, stems=7, cards=240),
    "SHRUB_B": dict(seed=9202, H=0.40, R=0.55, stems=8, cards=240),
    "SHRUB_C": dict(seed=9303, H=0.68, R=0.36, stems=6, cards=220),
}


def shrub(spec):
    rng = random.Random(spec["seed"])
    mb = MB()  # mat 0 = bark (plane bark used as generic dark wood), 1 = shrub leaf
    H, R = spec["H"], spec["R"]
    tips = []

    def grow(p0, d, L, r, depth):
        pts = [p0]
        rr = [r]
        segs = 3
        q = p0
        dd = d.copy()
        for s in range(segs):
            dd = (dd + Vector((rng.gauss(0, 0.15), rng.gauss(0, 0.15), 0.05))).normalized()
            q = q + dd * (L / segs)
            pts.append(q)
            rr.append(r * (1 - 0.6 * (s + 1) / segs))
        tube(mb, pts, rr, 4 if r > 0.006 else 3, 0, 1, 1 / (2 * math.pi * r), tip=True,
             col_fn=lambda co, rad: (0.45, 0.4, 0.33, 1.0))
        for k, q in enumerate(pts[1:]):
            tips.append((q, (pts[k + 1] - pts[k]).normalized()))
        if depth < 2:
            for k in range(2):
                f = rng.uniform(0.45, 0.9)
                idx = int(f * segs)
                base = pts[idx]
                nd = (dd + Vector((rng.gauss(0, 0.6), rng.gauss(0, 0.6), 0.3))).normalized()
                grow(base, nd, L * 0.55, r * 0.55, depth + 1)

    for s in range(spec["stems"]):
        a = s * 2 * math.pi / spec["stems"] + rng.uniform(-0.3, 0.3)
        tilt = rng.uniform(0.35, 0.8) * (R / H) * 0.9
        d = Vector((math.cos(a) * tilt, math.sin(a) * tilt, 1.0)).normalized()
        grow(Vector((rng.gauss(0, 0.03), rng.gauss(0, 0.03), -0.02)), d, H * rng.uniform(0.55, 0.75), 0.011, 0)
    cells = CLUSTER_LAYOUT["cluster"] + CLUSTER_LAYOUT["single"]
    centre = Vector((0, 0, H * 0.35))

    def nfn(co, nrm):
        rad = (co - centre).normalized() + Z * 0.3
        nn = nrm if nrm.dot(rad) >= 0 else -nrm
        return (nn * 0.4 + rad.normalized() * 0.6).normalized()

    placed = 0
    tries = 0
    while placed < spec["cards"] and tries < 5000:
        tries += 1
        # sample a point on the mound envelope and attach to the nearest twig node
        u = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(0.05, 1.0) ** 0.6
        layer = rng.uniform(0.55, 1.0) ** 0.5
        P = Vector((math.cos(u) * R * math.sqrt(1 - v * v) * layer, math.sin(u) * R * math.sqrt(1 - v * v) * layer,
                    H * 0.15 + (H * 0.72) * v * layer))
        q, dtw = min(tips, key=lambda t: (t[0] - P).length)
        if (q - P).length > 0.25:
            continue
        out = (P - centre).normalized()
        up = (dtw * 0.5 + out * 0.6 + Z * 0.3 + Vector((rng.gauss(0, 0.3), rng.gauss(0, 0.3), 0))).normalized()
        nrm = (out + Vector((rng.gauss(0, 0.4), rng.gauss(0, 0.4), rng.gauss(0, 0.4)))).normalized()
        cell = cells[rng.randrange(3)] if rng.random() < 0.75 else cells[3 + rng.randrange(4)]
        size = rng.uniform(0.18, 0.26) if cell in cells[:3] else rng.uniform(0.1, 0.14)
        attach = P - up * size * 0.4
        attach.z = max(attach.z, 0.03)
        card(mb, attach, up, nrm, size, size, cell["rect"], cell["pivot"], 1, bend=0.08, rows=3, normal_fn=nfn)
        placed += 1
    # clamp to the 0.7 m planting limit
    top = max(v.z for v in mb.v)
    if top > 0.7:
        s = 0.7 / top
        mb.v = [Vector((v.x, v.y, v.z * s)) for v in mb.v]
    return mb


def hedge(end, seed):
    """Clipped privet hedge, 1 m along X, 0.6 m deep, 1.0 m tall. Material 0 = hr_hedge_leaf
    (cards and core share it), 1 = bark for the stems visible at the base."""
    rng = random.Random(seed)
    mb = MB()
    L, Dp, H = 1.0, 0.6, 1.0
    hx, hy = L / 2, Dp / 2
    core = HEDGE_LAYOUT["core"]["rect"]
    ci, cd, ch = 0.1, 0.09, 0.1  # core inset from the clipped surface
    cx1 = hx - ci if end else hx
    # hidden core: front, back, top (and +X end face when this is an end piece)
    faces = [
        [(-hx, -hy + cd, 0), (cx1, -hy + cd, 0), (cx1, -hy + cd, H - ch), (-hx, -hy + cd, H - ch)],
        [(cx1, hy - cd, 0), (-hx, hy - cd, 0), (-hx, hy - cd, H - ch), (cx1, hy - cd, H - ch)],
        [(-hx, -hy + cd, H - ch), (cx1, -hy + cd, H - ch), (cx1, hy - cd, H - ch), (-hx, hy - cd, H - ch)],
    ]
    if end:
        faces.append([(cx1, -hy + cd, 0), (cx1, hy - cd, 0), (cx1, hy - cd, H - ch), (cx1, -hy + cd, H - ch)])
    for f in faces:
        a, b, c, d = [Vector(p) for p in f]
        nrm = (b - a).cross(d - a).normalized()
        ids = [mb.vert(p, nrm) for p in (a, b, c, d)]
        uvs = [rect_uv(core, 0, 1), rect_uv(core, 1, 1), rect_uv(core, 1, 0), rect_uv(core, 0, 0)]
        mb.face(ids, uvs, 0)
    # base stems
    for k in range(7):
        x = -hx + (k + rng.uniform(0.2, 0.8)) * L / 7
        if end and x > cx1:
            continue
        y = rng.uniform(-0.12, 0.12)
        top = Vector((x + rng.gauss(0, 0.05), y + rng.gauss(0, 0.05), 0.4))
        tube(mb, [Vector((x, y, -0.02)), (Vector((x, y, -0.02)) + top) * 0.5, top], [0.014, 0.011, 0.008], 4, 1,
             1, 1 / (2 * math.pi * 0.014), tip=False, col_fn=lambda co, r: (0.5, 0.42, 0.34, 1.0))
    sprigs = HEDGE_LAYOUT["cluster"]
    singles = HEDGE_LAYOUT["single"]

    def nfn(co, nrm):
        return nrm

    def place(P, nrm, up_hint):
        cell = sprigs[rng.randrange(2)] if rng.random() < 0.7 else singles[rng.randrange(4)]
        size = rng.uniform(0.2, 0.28) if cell in sprigs else rng.uniform(0.11, 0.15)
        up = (up_hint + Vector((rng.gauss(0, 0.5), rng.gauss(0, 0.5), rng.gauss(0, 0.5)))).normalized()
        up = (up - nrm * up.dot(nrm) + nrm * 0.15).normalized()  # sprigs lie along the clipped face
        n2 = (nrm + Vector((rng.gauss(0, 0.4), rng.gauss(0, 0.4), rng.gauss(0, 0.4)))).normalized()
        attach = P - up * size * 0.45 - nrm * rng.uniform(0.0, 0.04)
        smooth_n = (n2 * 0.6 + nrm * 0.3 + Z * 0.1).normalized()
        card(mb, attach, up, n2, size, size, cell["rect"], cell["pivot"], 0, bend=0.05, rows=2,
             normal_fn=lambda co, nn: smooth_n)

    xmax = hx - 0.04 if end else hx
    # front and back faces
    for side_y, ny in ((-hy, -1), (hy, 1)):
        for k in range(120):
            x = rng.uniform(-hx, xmax)
            z = rng.uniform(0.12, H - 0.03) ** 0.9
            rnd = 0.04 * smooth01((z - (H - 0.12)) / 0.12)  # rounded clipped shoulder
            if end:
                rnd += 0.05 * smooth01((x - (hx - 0.15)) / 0.15)
            P = Vector((x, side_y - ny * (rnd + 0.07), min(z, H - 0.08)))
            nrm = Vector((0, ny, 0.3 * smooth01((z - 0.85) / 0.15)))
            place(P, nrm.normalized(), Z * 0.8 + Vector((0, ny * 0.3, 0)))
    # top
    for k in range(170):
        x = rng.uniform(-hx, xmax)
        y = rng.uniform(-hy + 0.03, hy - 0.03)
        P = Vector((x * 1.0, y * 0.85, H - 0.07 - 0.02 * abs(y / hy) ** 3 - rng.uniform(0.0, 0.05)))
        place(P, (Z + Vector((0, y * 0.6, 0))).normalized(), Vector((rng.gauss(0, 1), rng.gauss(0, 1), 0.4)))
    if end:
        for k in range(75):
            y = rng.uniform(-hy + 0.03, hy - 0.03)
            z = rng.uniform(0.12, H - 0.05)
            round_ = 0.05 * (abs(y) / hy) ** 2
            P = Vector((hx - 0.07 - round_, y * 0.85, min(z, H - 0.08)))
            nrm = Vector((1, y * 0.8, 0)).normalized()
            place(P, nrm, Z * 0.8 + Vector((0.3, 0, 0)))
    return mb


# ======================================================================================
# Scene assembly
# ======================================================================================

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def tri_count(objs):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)


def obj_bounds(objs):
    mn = [1e9] * 3
    mx = [-1e9] * 3
    for o in objs:
        for v in o.data.vertices:
            for k in range(3):
                mn[k] = min(mn[k], v.co[k])
                mx[k] = max(mx[k], v.co[k])
    return [round(x, 3) for x in mn], [round(x, 3) for x in mx]


def main():
    only = os.environ.get("HR_FOLIAGE_ONLY")  # optional comma list for quick iteration
    reset_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    M = build_materials()
    manifest = {"kit": "heron-reach foliage", "blend": "assets/blender/heron-reach/foliage-kit.blend",
                "units": "metres, Z-up in Blender (glTF export converts to Y-up)", "assets": []}
    kitroot = new_collection("HR_FOLIAGE")
    lodroot = new_collection("HR_FOLIAGE_LOD1")

    def want(name):
        return not only or any(name.startswith(x) for x in only.split(","))

    # ---------------- trees
    for name, p in TREES.items():
        if not want(name):
            continue
        if os.environ.get('HR_FOLIAGE_WINTER') == '1':
            # The same deterministic trunk/branch skeleton, with only 4% lingering leaves.
            # Does not change the original collider manifest or any runtime placement.
            p={**p,'cards':max(12,round(p['cards']*.04))}
        pos, parent, radii, kids, keep = build_tree_skeleton(name, p)
        chains = chains_from(pos, parent, radii, kids, keep)
        pos = smooth_chain_positions(pos, chains)
        bark_mat = M["hr_bark_plane"] if p["species"] == "plane" else M["hr_bark_birch"]
        leaf_mat = M["hr_leaf_plane"] if p["species"] == "plane" else M["hr_leaf_birch"]
        entries = {}
        for lod in (0, 1):
            cname = name if lod == 0 else name + "_LOD1"
            coll = new_collection(cname, kitroot if lod == 0 else lodroot)
            bark = tree_bark(p, pos, chains, radii, lod)
            leaves, ncards = tree_leaves(p, pos, parent, radii, kids, keep, lod, p["seed"] + 17 * (lod + 1))
            ob = obj(cname + "_bark", bark.build(cname + "_bark", [bark_mat], vcol=True), coll)
            ol = obj(cname + "_leaves", leaves.build(cname + "_leaves", [leaf_mat]), coll)
            entries[lod] = (coll, [ob, ol], bark.tris(), leaves.tris(), ncards)
        col_r, flare_r = trunk_collision(pos, chains, radii, p)
        coll, objs, tb, tl, nc = entries[0]
        mn, mx = obj_bounds(objs)
        lowest_leaf = min(v.co.z for v in objs[1].data.vertices)
        lowest_branch = min((pos[i].z for i in range(len(pos)) if keep[i] and radii[i] < 0.08 and pos[i].z > 1.0),
                            default=0)
        c1, objs1, tb1, tl1, nc1 = entries[1]
        manifest["assets"].append({
            "name": name, "collection": name, "kind": "tree", "species": "London plane" if p["species"] == "plane" else "silver birch",
            "objects": [o.name for o in objs], "triangles": tb + tl, "triangles_bark": tb, "triangles_leaves": tl,
            "leaf_cards": nc, "bounds_min": mn, "bounds_max": mx, "height": round(mx[2], 2),
            "canopy_radius": round(max(abs(mn[0]), abs(mn[1]), mx[0], mx[1]), 2),
            "lowest_leaf_z": round(lowest_leaf, 2), "lowest_branch_z": round(lowest_branch, 2),
            "collision": {"type": "cylinder", "radius": col_r, "height": 2.0, "centre": [0, 0, 1.0],
                          "note": "trunk radius at 0.3-2.0 m plus 5 percent; root flare reaches %.2f m at ground "
                                  "level and is cosmetic; canopy has no collision" % flare_r},
            "lods": [{"name": name + "_LOD1", "collection": name + "_LOD1", "objects": [o.name for o in objs1],
                      "triangles": tb1 + tl1, "leaf_cards": nc1}],
            "materials": [objs[0].active_material.name, objs[1].active_material.name],
            "seed": p["seed"], "nodes": len(pos),
        })
        print(name, "bark", tb, "leaves", tl, "cards", nc, "LOD1", tb1 + tl1, "nodes", len(pos), "col", col_r,
              "low leaf", round(lowest_leaf, 2), "bounds", mn, mx)

    # ---------------- grass
    clumps = {n: grass_clump(s) for n, s in GRASS_CLUMPS.items()}
    gm = M["hr_grass_blade"]
    for name, mb in list(clumps.items()) + [("GRASS_PATCH_1M", grass_patch(clumps, 8501)),
                                             ("GRASS_EDGE_1M", grass_edge(clumps, 8602))]:
        if not want(name):
            continue
        coll = new_collection(name, kitroot)
        o = obj(name, mb.build(name, [gm]), coll)
        mn, mx = obj_bounds([o])
        manifest["assets"].append({"name": name, "collection": name, "kind": "grass", "objects": [o.name],
                                   "triangles": mb.tris(), "bounds_min": mn, "bounds_max": mx,
                                   "collision": {"type": "none"}, "lods": [], "materials": [gm.name],
                                   "tiling": "1 m tile, place on a 1 m grid with random 90 degree turns"
                                   if name == "GRASS_PATCH_1M" else None})
    # ---------------- weeds
    for k, kind in enumerate("ABC"):
        name = "WEED_TUFT_" + kind
        if not want(name):
            continue
        mb = weed_tuft(kind, 8701 + k)
        coll = new_collection(name, kitroot)
        mats = [M["hr_weed"], M["hr_grass_blade"]]
        o = obj(name, mb.build(name, mats), coll)
        mn, mx = obj_bounds([o])
        manifest["assets"].append({"name": name, "collection": name, "kind": "weed", "objects": [o.name],
                                   "triangles": mb.tris(), "bounds_min": mn, "bounds_max": mx,
                                   "collision": {"type": "none"}, "lods": [],
                                   "materials": sorted({mats[i].name for i in mb.m})})
    # ---------------- litter
    for k, kind in enumerate("ABC"):
        name = "LEAF_LITTER_" + kind
        if not want(name):
            continue
        mb = leaf_litter(kind, 8801 + k)
        coll = new_collection(name, kitroot)
        o = obj(name, mb.build(name, [M["hr_leaf_litter"]]), coll)
        mn, mx = obj_bounds([o])
        manifest["assets"].append({"name": name, "collection": name, "kind": "leaf litter", "objects": [o.name],
                                   "triangles": mb.tris(), "bounds_min": mn, "bounds_max": mx,
                                   "collision": {"type": "none"}, "lods": [], "materials": ["hr_leaf_litter"],
                                   "note": {"A": "gutter drift, dense along the -Y edge",
                                            "B": "small heaps", "C": "sparse scatter"}[kind]})
    # ---------------- shrubs
    for name, spec in SHRUBS.items():
        if not want(name):
            continue
        mb = shrub(spec)
        coll = new_collection(name, kitroot)
        o = obj(name, mb.build(name, [M["hr_bark_plane"], M["hr_shrub_leaf"]], vcol=True), coll)
        mn, mx = obj_bounds([o])
        manifest["assets"].append({"name": name, "collection": name, "kind": "shrub", "objects": [o.name],
                                   "triangles": mb.tris(), "bounds_min": mn, "bounds_max": mx,
                                   "collision": {"type": "none", "note": "below 0.7 m; walk-through cosmetic"},
                                   "lods": [], "materials": ["hr_bark_plane", "hr_shrub_leaf"]})
    # ---------------- hedges
    for name, end in (("HEDGE_1M", False), ("HEDGE_END", True)):
        if not want(name):
            continue
        mb = hedge(end, 9501 if not end else 9602)
        coll = new_collection(name, kitroot)
        o = obj(name, mb.build(name, [M["hr_hedge_leaf"], M["hr_bark_plane"]], vcol=True), coll)
        mn, mx = obj_bounds([o])
        manifest["assets"].append({"name": name, "collection": name, "kind": "hedge", "objects": [o.name],
                                   "triangles": mb.tris(), "bounds_min": mn, "bounds_max": mx,
                                   "footprint": [1.0, 0.6],
                                   "collision": {"type": "box", "size": [1.0, 0.6, 1.0], "centre": [0, 0, 0.5],
                                                 "note": "blocks players; use an explicit box collider"},
                                   "lods": [], "materials": ["hr_hedge_leaf", "hr_bark_plane"],
                                   "tiling": ("open at -X and +X, tiles end to end along X every 1.0 m" if not end
                                              else "open at -X, closed rounded end at +X; rotate 180 degrees for the "
                                                   "other end of a run")})

    # hide LOD collections in the viewport so the file opens tidy
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name == "HR_FOLIAGE_LOD1":
            lc.hide_viewport = True
    manifest["textures"] = TEXTURE_NOTES
    manifest["materials"] = MATERIAL_NOTES
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups beside the kit
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    if not only or os.environ.get('HR_FOLIAGE_MANIFEST'):
        manifest['blend']=os.path.relpath(BLEND,REPO)
        manifest['provenance']='Original ONSITE deterministic tree generators and existing project procedural bark/leaf textures. No external meshes.'
        manifest['winter']=os.environ.get('HR_FOLIAGE_WINTER')=='1'
        manifest['blender']=bpy.app.version_string
        with open(MANIFEST, "w") as fh:
            json.dump(manifest, fh, indent=2)
    print("saved", BLEND)


TEXTURE_NOTES = [
    {"files": ["plane-leaf-atlas-color.webp", "plane-leaf-atlas-normal.webp"], "material": "hr_leaf_plane",
     "method": "numpy: palmate 3-5 lobed outline from a soft-max of pointed polar lobes with coarse teeth; "
               "primary and secondary veins as distance fields; autumn palette yellow-green to tan and brown "
               "with blotch noise and browned margins; 2x supersampled; normal from a dome-plus-vein height map; "
               "colour bled under transparent pixels (pull-push) to stop mip fringes. Seed 4101."},
    {"files": ["birch-leaf-atlas-color.webp", "birch-leaf-atlas-normal.webp"], "material": "hr_leaf_birch",
     "method": "numpy: deltoid-ovate outline with acuminate tip and double serration, midrib and seven straight "
               "vein pairs; yellow-green to gold palette; clusters on thin dark twigs. Seed 4202."},
    {"files": ["plane-bark-color.webp", "plane-bark-normal.webp", "plane-bark-orm.webp"], "material": "hr_bark_plane",
     "method": "numpy: two scales of periodic, domain-warped Worley cells; each plate gets a bark age (cream, olive, "
               "grey-green, grey-brown); small flakes peel to younger layers; softened rims, rain streaks and "
               "algae tint; height from age steps; ORM = cavity AO, roughness by age, metal 0. Tiles both ways, "
               "1 tile = 1 m. Seed 4808."},
    {"files": ["birch-bark-color.webp", "birch-bark-normal.webp", "birch-bark-orm.webp"], "material": "hr_bark_birch",
     "method": "numpy: cream-white base with grey mottling and pinkish peeled bands; 300 wrapped horizontal "
               "lenticel dashes; ragged dark fissured patches from thresholded periodic noise. Black trunk base and "
               "dark twigs come from vertex colour (COLOR_0) multiplied in the material. Seed 4909."},
    {"files": ["grass-blades-color.webp", "grass-blades-normal.webp"], "material": "hr_grass_blade",
     "method": "numpy: twelve 64 px blade columns (damp dark greens, two yellowed) with keeled midrib, striations, "
               "darker base and ragged dried straw tips of random length; two side-view tuft cards drawn as "
               "tapered Bezier blades. Seed 4606."},
    {"files": ["weeds-color.webp", "weeds-normal.webp"], "material": "hr_weed",
     "method": "numpy: runcinate dandelion leaves, plantain leaves with parallel veins, a grassy crack weed with "
               "seed panicles and a groundsel-type sprig with muted yellow heads. Seed 4707."},
    {"files": ["leaf-litter-color.webp", "leaf-litter-normal.webp"], "material": "hr_leaf_litter",
     "method": "numpy: 4 x 4 grid of fallen plane and birch leaves in wet browns, with dark wet spotting, "
               "holes, curl in the height map. Seed 4505."},
    {"files": ["hedge-leaf-atlas-color.webp", "hedge-leaf-atlas-normal.webp"], "material": "hr_hedge_leaf",
     "method": "numpy: privet sprigs with opposite small glossy elliptic leaves, an opaque inner-foliage tile "
               "(900 overlapping leaves darkened by depth) for the hidden core, small sprig singles. Seed 4404."},
    {"files": ["shrub-leaf-atlas-color.webp", "shrub-leaf-atlas-normal.webp"], "material": "hr_shrub_leaf",
     "method": "numpy: evergreen laurel-type oval leaves with fine serration, a few bronze older leaves, on green "
               "twigs. Seed 4303."},
]

MATERIAL_NOTES = {
    "all": "Principled BSDF; colour images sRGB, normal and ORM Non-Color; OpenGL normals.",
    "alpha": "Leaf, grass, weed, hedge and litter materials feed image alpha through a Math Round node "
             "(alpha clip at 0.5) and have backface culling off, so glTF exports alphaMode MASK, doubleSided.",
    "bark": "hr_bark_plane and hr_bark_birch multiply the base colour by the Col vertex colour attribute "
            "(glTF COLOR_0). Occlusion via the glTF Material Output group from the ORM red channel.",
    "normals": "Leaf cards carry custom normals blended towards the canopy radial direction so crowns light "
               "softly; grass normals lean towards +Z so lawns light like the ground.",
}


if __name__ == "__main__":
    main()
