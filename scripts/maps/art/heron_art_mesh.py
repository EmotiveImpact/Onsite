"""Geometry accumulation for the Heron Reach art build.

Everything is authored in map coordinates (x east, z south, y up, metres) and converted once to
Blender (X = x-72, Y = 60-z, Z = y). Geometry is accumulated per (group, material) and turned into
one Blender object each, so the authored file stays editable without thousands of tiny objects.
UVs are metric (1 UV unit = 1 m) for tiling materials; materials scale them by 1/coverage.
"""
import math
import bpy
from mathutils import Vector

OX, OZ = 72.0, 60.0


def bl(x, y, z):
    return (x - OX, OZ - z, y)


class Accumulator:
    """Collects quads/triangles with UVs and vertex colours for one group and material."""

    def __init__(self):
        self.verts = []
        self.faces = []
        self.uvs = []
        self.cols = []

    def poly(self, pts, uvs, col=(1, 1, 1, 1)):
        base = len(self.verts)
        self.verts.extend(bl(*p) for p in pts)
        self.faces.append(tuple(range(base, base + len(pts))))
        self.uvs.append(list(uvs))
        self.cols.append(col if isinstance(col, list) else [col] * len(pts))

    def __len__(self):
        return len(self.faces)


class Builder:
    def __init__(self, collection_for):
        self.groups = {}
        self.collection_for = collection_for

    def acc(self, group, mat):
        return self.groups.setdefault((group, mat), Accumulator())

    # --- primitives -------------------------------------------------------------------------
    def quad(self, group, mat, p0, p1, p2, p3, uv=None, col=(1, 1, 1, 1)):
        """Quad p0..p3 counter-clockwise seen from the front. Metric planar UVs by default."""
        if uv is None:
            uv = planar_uv([p0, p1, p2, p3])
        if callable(col):
            col = [col(p) for p in (p0, p1, p2, p3)]
        self.acc(group, mat).poly([p0, p1, p2, p3], uv, col)

    def box(self, group, mat, x0, x1, y0, y1, z0, z1, faces='all', col=None, mats=None, uv_offset=(0, 0)):
        """Axis-aligned box. faces: subset of '+x -x +y -y +z -z' (map axes) or 'all'.
        mats optionally maps a face key to another material. col: callable(point)->rgba or rgba."""
        keys = ['+x', '-x', '+y', '-y', '+z', '-z'] if faces == 'all' else faces.split()
        P = {
            '+x': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
            '-x': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            '+y': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
            '-y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            '-z': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        }
        for k in keys:
            pts = P[k]
            m = (mats or {}).get(k, mat)
            if m is None:
                continue
            c = [col(p) for p in pts] if callable(col) else (col or (1, 1, 1, 1))
            uv = planar_uv(pts, k, uv_offset)
            self.acc(group, m).poly(pts, uv, c)

    def cylinder(self, group, mat, a, b, r, seg=8, caps=True, col=(1, 1, 1, 1), r2=None):
        """Tube from a to b (map coordinates). UV u around (metres of circumference), v along."""
        a, b = Vector(a), Vector(b)
        axis = b - a
        length = axis.length
        if length < 1e-5:
            return
        d = axis.normalized()
        ref = Vector((0, 1, 0)) if abs(d.y) < .9 else Vector((1, 0, 0))
        u = d.cross(ref).normalized()
        v = d.cross(u).normalized()
        r2 = r if r2 is None else r2
        ring = lambda c, rr: [c + (u * math.cos(t) + v * math.sin(t)) * rr for t in [i * math.tau / seg for i in range(seg)]]
        ra, rb = ring(a, r), ring(b, r2)
        circ = math.tau * r
        acc = self.acc(group, mat)
        for i in range(seg):
            j = (i + 1) % seg
            pts = [tuple(ra[i]), tuple(ra[j]), tuple(rb[j]), tuple(rb[i])]
            u0, u1 = circ * i / seg, circ * (i + 1) / seg
            acc.poly(pts, [(u0, 0), (u1, 0), (u1, length), (u0, length)], col)
        if caps:
            acc.poly([tuple(p) for p in reversed(ra)], [(0, 0)] * seg, col)
            acc.poly([tuple(p) for p in rb], [(0, 0)] * seg, col)

    # --- output -----------------------------------------------------------------------------
    def build(self, materials, smooth_groups=()):
        made = []
        for (group, mat), acc in self.groups.items():
            if not len(acc):
                continue
            mesh = bpy.data.meshes.new(f'{group} / {mat}')
            mesh.from_pydata(acc.verts, [], acc.faces)
            uvl = mesh.uv_layers.new(name='UVMap')
            colour = mesh.color_attributes.new(name='Col', type='FLOAT_COLOR', domain='CORNER')
            # Adding CustomData invalidates the UV-layer RNA handle in Blender 4.3.
            # Reacquire it or foreach_set silently leaves default 0..1 UVs on every face.
            uvl = mesh.uv_layers['UVMap']
            # Loops follow face order and vertex order, so flattened per-face lists line up.
            uvl.data.foreach_set('uv', [c for f in acc.uvs for uv in f for c in uv])
            colour.data.foreach_set('color', [c for f in acc.cols for rgba in f for c in rgba])
            mesh.materials.append(materials(mat))
            mesh.validate(clean_customdata=False)
            mesh.update()
            if any(group.endswith(s) for s in smooth_groups):
                for p in mesh.polygons:
                    p.use_smooth = True
            obj = bpy.data.objects.new(f'{group} / {mat}', mesh)
            self.collection_for(group).objects.link(obj)
            made.append(obj)
        self.groups.clear()
        return made


def planar_uv(pts, key=None, offset=(0, 0)):
    """Metric planar projection chosen from the face normal (map axes)."""
    if key is None:
        a, b, c = Vector(pts[0]), Vector(pts[1]), Vector(pts[2])
        n = (b - a).cross(c - a)
        ax = max(range(3), key=lambda i: abs(n[i]))
        key = {0: '+x', 1: '+y', 2: '+z'}[ax]
        if n[ax] < 0:
            key = '-' + key[1]
    ox, oy = offset
    if key in ('+y', '-y'):
        return [(p[0] + ox, -p[2] + oy) for p in pts]
    if key in ('+x', '-x'):
        s = 1 if key == '-x' else -1
        return [(s * p[2] + ox, p[1] + oy) for p in pts]
    s = 1 if key == '+z' else -1
    return [(s * p[0] + ox, p[1] + oy) for p in pts]
