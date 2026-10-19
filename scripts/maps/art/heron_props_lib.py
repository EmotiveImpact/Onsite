"""Geometry helpers for the Heron Reach props kit.

Pure bmesh construction, no operators, so the build is deterministic and runs
headless under `python3` with Blender as a module. One `Asset` collects parts
into a single bmesh with per-face materials, metre UVs (or atlas UVs) and
per-part sharp-edge flags, then becomes one object in one collection.

Coordinates: metres, Z up, front of every asset faces -Y.
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

TAU = math.tau

# ---------------------------------------------------------------------------
# Deterministic value noise (no numpy needed inside Blender scripts).
# ---------------------------------------------------------------------------


def _hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 974711) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise(x, y, z=0.0, seed=0):
    """Value noise in [-1, 1]."""
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = _smooth(x - ix), _smooth(y - iy), _smooth(z - iz)
    acc = 0.0
    for dz in (0, 1):
        wz = fz if dz else 1 - fz
        for dy in (0, 1):
            wy = fy if dy else 1 - fy
            for dx in (0, 1):
                wx = fx if dx else 1 - fx
                acc += wx * wy * wz * _hash3(ix + dx, iy + dy, iz + dz, seed)
    return acc * 2.0 - 1.0


def fbm(x, y, z=0.0, seed=0, octaves=3):
    a, f, s, n = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        s += a * vnoise(x * f, y * f, z * f, seed + o * 17)
        n += a
        a *= 0.5
        f *= 2.03
    return s / n


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = x, y, z
    return m


def look_matrix(direction, up=Vector((0, 0, 1))):
    """Rotation taking local +Z to `direction`."""
    d = Vector(direction).normalized()
    if abs(d.dot(up)) > 0.999:
        up = Vector((1, 0, 0))
    x = up.cross(d).normalized()
    y = d.cross(x).normalized()
    m = Matrix((x, y, d)).transposed().to_4x4()
    return m


# ---------------------------------------------------------------------------
# Primitive part builders: each returns a fresh bmesh in local coordinates.
# Parts may carry their own UVs (layer 'UVMap') and face material indices.
# ---------------------------------------------------------------------------


def _new():
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    return bm


def _bevel_all(bm, offset, segments, edges=None):
    if offset <= 0:
        return
    geom = list(edges) if edges is not None else list(bm.edges)
    if not geom:
        return
    bmesh.ops.bevel(
        bm,
        geom=geom,
        offset=offset,
        offset_type="OFFSET",
        segments=max(1, segments),
        profile=0.5,
        affect="EDGES",
        clamp_overlap=True,
    )


def box(sx, sy, sz, bevel=0.0, seg=1, center=(0.0, 0.0, 0.0)):
    bm = _new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx + center[0], v.co.y * sy + center[1], v.co.z * sz + center[2]))
    _bevel_all(bm, min(bevel, 0.49 * min(sx, sy, sz)), seg)
    return bm


def box_mm(x0, x1, y0, y1, z0, z1, bevel=0.0, seg=1):
    return box(
        abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), bevel, seg,
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
    )


def quad(p0, p1, p2, p3, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
    """Single quad, counter-clockwise when seen from its front side."""
    bm = _new()
    uvl = bm.loops.layers.uv.active
    vs = [bm.verts.new(Vector(p)) for p in (p0, p1, p2, p3)]
    f = bm.faces.new(vs)
    for loop, uv in zip(f.loops, uvs):
        loop[uvl].uv = uv
    return bm


def grid_plane(sx, sz, nx, nz, uv_scale=1.0):
    """Vertical plane in XZ facing -Y, centred on x, bottom at z=0, UVs in metres."""
    bm = _new()
    uvl = bm.loops.layers.uv.active
    verts = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            x = -sx / 2 + sx * i / nx
            z = sz * j / nz
            row.append(bm.verts.new((x, 0.0, z)))
        verts.append(row)
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for loop in f.loops:
                co = loop.vert.co
                loop[uvl].uv = ((co.x + sx / 2) * uv_scale, co.z * uv_scale)
    return bm


def round_profile(points, radius, steps=2):
    """Fillet the interior corners of an open 2D polyline."""
    if radius <= 0 or steps <= 0 or len(points) < 3:
        return list(points)
    out = [points[0]]
    for i in range(1, len(points) - 1):
        p0, p1, p2 = Vector(points[i - 1]), Vector(points[i]), Vector(points[i + 1])
        a, b = (p0 - p1), (p2 - p1)
        la, lb = a.length, b.length
        if la < 1e-6 or lb < 1e-6:
            out.append(tuple(p1))
            continue
        r = min(radius, la * 0.45, lb * 0.45)
        a.normalize()
        b.normalize()
        s = p1 + a * r
        e = p1 + b * r
        for k in range(steps + 1):
            t = k / steps
            q = (1 - t) ** 2 * s + 2 * (1 - t) * t * p1 + t * t * e
            out.append((q.x, q.y))
    out.append(points[-1])
    return out


def lathe(profile, n=16, cap_bottom=True, cap_top=True, uv="metres", phase=0.0,
          uv_rect=None):
    """Revolve a (r, z) profile around Z. Profile runs bottom to top.

    uv='metres': u = arc length at the max radius, v = profile length.
    uv='unit'  : u in 0..1 around, v in 0..1 along profile (for label wraps).
    """
    bm = _new()
    uvl = bm.loops.layers.uv.active
    rmax = max(p[0] for p in profile) or 1.0
    lengths = [0.0]
    for i in range(1, len(profile)):
        dr = profile[i][0] - profile[i - 1][0]
        dz = profile[i][1] - profile[i - 1][1]
        lengths.append(lengths[-1] + math.hypot(dr, dz))
    total = lengths[-1] or 1.0
    rings = []
    for (r, z) in profile:
        ring = []
        for k in range(n):
            a = TAU * k / n + phase
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)

    def uvof(i, k):
        if uv == "unit":
            u, v = k / n, lengths[i] / total
            if uv_rect:
                u0, v0, u1, v1 = uv_rect
                return (u0 + (u1 - u0) * u, v0 + (v1 - v0) * v)
            return (u, v)
        return (TAU * rmax * k / n, lengths[i])

    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        if profile[i][0] < 1e-7 and profile[i + 1][0] < 1e-7:
            continue
        for k in range(n):
            k1 = (k + 1) % n
            if profile[i][0] < 1e-7:
                vs = (r0[k], r1[k], r1[k1])
                ks = ((i, k), (i + 1, k), (i + 1, k + 1))
            elif profile[i + 1][0] < 1e-7:
                vs = (r0[k], r0[k1], r1[k])
                ks = ((i, k), (i, k + 1), (i + 1, k))
            else:
                vs = (r0[k], r0[k1], r1[k1], r1[k])
                ks = ((i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k))
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            for loop, (ii, kk) in zip(f.loops, ks):
                loop[uvl].uv = uvof(ii, kk)
    # merge degenerate pole verts
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    if cap_bottom and profile[0][0] > 1e-7:
        ring = rings[0]
        f = bm.faces.new(list(reversed(ring)))
        for loop in f.loops:
            co = loop.vert.co
            loop[uvl].uv = (co.x, co.y)
    if cap_top and profile[-1][0] > 1e-7:
        ring = rings[-1]
        f = bm.faces.new(ring)
        for loop in f.loops:
            co = loop.vert.co
            loop[uvl].uv = (co.x, co.y)
    return bm


def cyl(r, h, n=16, z0=0.0, bevel=0.0, caps=True):
    if bevel > 0:
        b = min(bevel, r * 0.4, h * 0.4)
        prof = [(r - b, z0), (r - b * 0.3, z0 + b * 0.3), (r, z0 + b), (r, z0 + h - b),
                (r - b * 0.3, z0 + h - b * 0.3), (r - b, z0 + h)]
    else:
        prof = [(r, z0), (r, z0 + h)]
    return lathe(prof, n, caps, caps)


def cyl_between(p0, p1, r, n=8, caps=True, bevel=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = cyl(r, d.length, n, 0.0, bevel, caps)
    bmesh.ops.transform(bm, matrix=T(*p0) @ look_matrix(d), verts=bm.verts)
    return bm


def sphere(r, seg=12, rings=8):
    prof = []
    for i in range(rings + 1):
        a = -math.pi / 2 + math.pi * i / rings
        prof.append((r * math.cos(a) if 0 < i < rings else 0.0, r * math.sin(a)))
    return lathe(prof, seg, False, False)


def torus(R_, r, n=24, m=8):
    bm = _new()
    uvl = bm.loops.layers.uv.active
    grid = []
    for i in range(n):
        a = TAU * i / n
        row = []
        for j in range(m):
            b = TAU * j / m
            rr = R_ + r * math.cos(b)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), r * math.sin(b))))
        grid.append(row)
    for i in range(n):
        for j in range(m):
            i1, j1 = (i + 1) % n, (j + 1) % m
            f = bm.faces.new((grid[i][j], grid[i1][j], grid[i1][j1], grid[i][j1]))
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uvl].uv = (TAU * R_ * ii / n, TAU * r * jj / m)
    return bm


def prism(poly, depth, bevel=0.0, seg=1, y0=None):
    """Extrude a CCW polygon drawn in the XZ plane along +Y (depth), centred on y."""
    bm = _new()
    yb = -depth / 2 if y0 is None else y0
    vs = [bm.verts.new((x, yb, z)) for (x, z) in poly]
    f = bm.faces.new(vs)
    # face normal should be -Y for the front; poly CCW in XZ seen from -Y gives -Y
    bm.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, depth, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        _bevel_all(bm, bevel, seg)
    return bm


def sweep(path, profile, up=(0, 0, 1), closed=False, caps=True, uv_scale=1.0):
    """Sweep a 2D profile [(a, b)] along a 3D polyline with mitred joints.

    a runs along the side vector (tangent x up), b along `up` projected.
    """
    bm = _new()
    uvl = bm.loops.layers.uv.active
    pts = [Vector(p) for p in path]
    upv = Vector(up).normalized()
    npnt = len(pts)
    rings = []
    along = [0.0]
    for i in range(1, npnt):
        along.append(along[-1] + (pts[i] - pts[i - 1]).length)
    prev_n = None
    for i in range(npnt):
        if closed:
            d0 = (pts[i] - pts[i - 1]).normalized()
            d1 = (pts[(i + 1) % npnt] - pts[i]).normalized()
        else:
            d0 = (pts[i] - pts[i - 1]).normalized() if i > 0 else (pts[1] - pts[0]).normalized()
            d1 = (pts[i + 1] - pts[i]).normalized() if i < npnt - 1 else d0
        t = (d0 + d1)
        if t.length < 1e-6:
            t = d1
        t.normalize()
        # frame: n is "up" component perpendicular to t
        n = upv - t * upv.dot(t)
        if n.length < 1e-5:
            n = prev_n if prev_n is not None else Vector((1, 0, 0))
        n.normalize()
        if prev_n is not None and n.dot(prev_n) < 0:
            n = -n
        prev_n = n
        s = t.cross(n).normalized()
        cosh = max(0.2, d0.dot(t))
        # mitre scale along the bend direction only
        bend = (d1 - d0)
        ring = []
        for (a, b) in profile:
            off = s * a + n * b
            if bend.length > 1e-6:
                bd = bend.normalized()
                comp = off.dot(bd)
                off = off + bd * comp * (1.0 / cosh - 1.0)
            ring.append(bm.verts.new(pts[i] + off))
        rings.append(ring)
    m = len(profile)
    perim = [0.0]
    for j in range(1, m + 1):
        a0, b0 = profile[j - 1]
        a1, b1 = profile[j % m]
        perim.append(perim[-1] + math.hypot(a1 - a0, b1 - b0))
    segs = npnt if closed else npnt - 1
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % npnt]
        l0 = along[i]
        l1 = along[i + 1] if i + 1 < npnt else along[-1] + (pts[0] - pts[-1]).length
        for j in range(m):
            j1 = (j + 1) % m
            f = bm.faces.new((r0[j], r1[j], r1[j1], r0[j1]))
            for loop, (pu, pv) in zip(f.loops, ((j, l0), (j, l1), (j + 1, l1), (j + 1, l0))):
                loop[uvl].uv = (perim[pu] * uv_scale, pv * uv_scale)
    if caps and not closed:
        for ring, rev in ((rings[0], True), (rings[-1], False)):
            try:
                f = bm.faces.new(list(reversed(ring)) if rev else ring)
                for loop in f.loops:
                    co = loop.vert.co
                    loop[uvl].uv = (co.x * uv_scale, co.y * uv_scale + co.z * uv_scale)
            except ValueError:
                pass
    bm.normal_update()
    # make sure faces point outward
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def circle_profile(r, n=8):
    return [(r * math.cos(TAU * k / n + math.pi / n), r * math.sin(TAU * k / n + math.pi / n)) for k in range(n)]


def rect_profile(w, h, chamfer=0.0):
    a, b = w / 2, h / 2
    if chamfer <= 0:
        return [(-a, -b), (a, -b), (a, b), (-a, b)]
    c = min(chamfer, a * 0.45, b * 0.45)
    return [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]


def tube(path, r, n=8, closed=False, caps=True, up=(0, 0, 1)):
    return sweep(path, circle_profile(r, n), up=up, closed=closed, caps=caps)


def fillet_path(points, radius, steps=3):
    """Round the corners of a 3D polyline."""
    if len(points) < 3:
        return [Vector(p) for p in points]
    pts = [Vector(p) for p in points]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        a, b = (p0 - p1), (p2 - p1)
        r = min(radius, a.length * 0.45, b.length * 0.45)
        a.normalize()
        b.normalize()
        s, e = p1 + a * r, p1 + b * r
        for k in range(steps + 1):
            t = k / steps
            out.append((1 - t) ** 2 * s + 2 * (1 - t) * t * p1 + t * t * e)
    out.append(pts[-1])
    return out


def bolt_head(r=0.008, h=0.006, n=6):
    """Hex bolt head sitting on z=0, with a small chamfer."""
    return lathe([(r, 0.0), (r, h * 0.7), (r * 0.82, h), (0.0, h)], n, True, False, phase=math.pi / 6)


def dome_head(r=0.007, h=0.004, n=8):
    return lathe([(r, 0.0), (r * 0.9, h * 0.6), (r * 0.5, h * 0.95), (0.0, h)], n, True, False)


def text_mesh(text, font_path, size, extrude=0.0, bevel=0.0, align="CENTER", condense=1.0,
              resolution=2, spacing=1.0):
    """Blender text converted to a bmesh lying in the XZ plane facing -Y."""
    cu = bpy.data.curves.new("tmp_text", type="FONT")
    cu.body = text
    cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1 if bevel > 0 else 0
    cu.resolution_u = resolution
    cu.align_x = align
    cu.align_y = "BOTTOM"
    cu.space_character = spacing
    ob = bpy.data.objects.new("tmp_text", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = _new()
    bm.from_mesh(me)
    if not bm.loops.layers.uv:
        bm.loops.layers.uv.new("UVMap")
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    # text lies in XY facing +Z; stand it up to face -Y
    bmesh.ops.transform(bm, matrix=R("X", 90) @ S(condense, 1, 1), verts=bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------
# Asset accumulation
# ---------------------------------------------------------------------------


class Asset:
    def __init__(self, name, category, seed=1):
        self.name = name
        self.category = category
        self.bm = _new()
        self.uv = self.bm.loops.layers.uv.active
        self.mats = []
        self.rng = random.Random(seed)
        self.meta = {}

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def add(self, part, mat, matrix=None, uv="box", uv_scale=1.0, uv_rect=None, sharp=40.0,
            fit_axis=None, flip=False, smooth=True):
        """Merge `part` into the asset.

        mat: a material name, or a list mapping the part's material_index to names.
        uv : 'box' world box projection in metres (x uv_scale), 'keep' part UVs
             (x uv_scale), 'rect' part 0..1 UVs remapped into uv_rect,
             'fit' planar projection along fit_axis fitted to uv_rect.
        """
        if matrix is not None:
            bmesh.ops.transform(part, matrix=matrix, verts=part.verts)
            if matrix.to_3x3().determinant() < 0:
                bmesh.ops.reverse_faces(part, faces=part.faces)
        if flip:
            bmesh.ops.reverse_faces(part, faces=part.faces)
        part.normal_update()
        puv = part.loops.layers.uv.active
        if isinstance(mat, (list, tuple)):
            idx = [self.mi(m) for m in mat]
        else:
            idx = [self.mi(mat)]
        # sharp flags from the part's own dihedral angles
        cos_lim = math.cos(math.radians(sharp))
        part.verts.index_update()
        sharp_pairs = set()
        for e in part.edges:
            if len(e.link_faces) == 2:
                n0, n1 = e.link_faces[0].normal, e.link_faces[1].normal
                if n0.dot(n1) < cos_lim or e.link_faces[0].material_index != e.link_faces[1].material_index:
                    sharp_pairs.add(tuple(sorted((e.verts[0].index, e.verts[1].index))))
            else:
                sharp_pairs.add(tuple(sorted((e.verts[0].index, e.verts[1].index))))
        fit_bounds = None
        if uv == "fit":
            ax = {"X": 0, "Y": 1, "Z": 2}[fit_axis or "Y"]
            others = [a for a in (0, 1, 2) if a != ax]
            cs = [v.co for v in part.verts]
            mins = [min(c[a] for c in cs) for a in others]
            maxs = [max(c[a] for c in cs) for a in others]
            fit_bounds = (others, mins, maxs)
        vmap = [self.bm.verts.new(v.co) for v in part.verts]
        for f in part.faces:
            try:
                nf = self.bm.faces.new([vmap[v.index] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = idx[min(f.material_index, len(idx) - 1)]
            nf.smooth = smooth
            n = f.normal
            for nl, ol in zip(nf.loops, f.loops):
                co = ol.vert.co
                if uv == "box":
                    ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                    if ax >= ay and ax >= az:
                        u = co.y if n.x > 0 else -co.y
                        v = co.z
                    elif ay >= ax and ay >= az:
                        u = -co.x if n.y > 0 else co.x
                        v = co.z
                    else:
                        u = co.x
                        v = co.y if n.z > 0 else -co.y
                    nl[self.uv].uv = (u * uv_scale, v * uv_scale)
                elif uv == "keep":
                    p = ol[puv].uv
                    nl[self.uv].uv = (p.x * uv_scale, p.y * uv_scale)
                elif uv == "rect":
                    p = ol[puv].uv
                    u0, v0, u1, v1 = uv_rect
                    nl[self.uv].uv = (u0 + (u1 - u0) * p.x, v0 + (v1 - v0) * p.y)
                elif uv == "fit":
                    others, mins, maxs = fit_bounds
                    u0, v0, u1, v1 = uv_rect
                    a0, a1 = others
                    fu = (co[a0] - mins[0]) / max(1e-9, maxs[0] - mins[0])
                    fv = (co[a1] - mins[1]) / max(1e-9, maxs[1] - mins[1])
                    if fit_axis == "Y" and n.y > 0:
                        fu = 1 - fu
                    if fit_axis == "X" and n.x < 0:
                        fu = 1 - fu
                    nl[self.uv].uv = (u0 + (u1 - u0) * fu, v0 + (v1 - v0) * fv)
        self.bm.verts.ensure_lookup_table()
        for (a, b) in sharp_pairs:
            e = self.bm.edges.get((vmap[a], vmap[b]))
            if e is not None:
                e.smooth = False
        part.free()

    # -- finishing -----------------------------------------------------------
    def build(self, materials, parent_collection):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if not v.link_faces], dist=0.0)
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(materials[m])
        me.validate(clean_customdata=False)
        ob = bpy.data.objects.new(self.name, me)
        col = bpy.data.collections.new(self.name)
        parent_collection.children.link(col)
        col.objects.link(ob)
        self.object = ob
        self.collection = col
        return ob


def stats(ob):
    me = ob.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    return {
        "triangles": tris,
        "bounds_min": [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
        "bounds_max": [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)],
        "size": [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), round(max(zs) - min(zs), 3)],
    }


def rrect(w, d, r, nc=3, z=0.0, cx=0.0, cy=0.0):
    """Rounded rectangle loop (CCW seen from +Z) as 3D points at height z."""
    r = min(r, w * 0.49, d * 0.49)
    pts = []
    corners = [(w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)]
    for (x, y, a0) in corners:
        for k in range(nc + 1):
            a = math.radians(a0 + 90 * k / nc)
            pts.append(Vector((cx + x + r * math.cos(a), cy + y + r * math.sin(a), z)))
    return pts


def loft(rings, cap_bottom=True, cap_top=True, closed=True):
    """Bridge a list of equal-length point loops (bottom to top)."""
    bm = _new()
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for i in range(len(vr) - 1):
        a, b = vr[i], vr[i + 1]
        for k in range(n if closed else n - 1):
            k1 = (k + 1) % n
            try:
                bm.faces.new((a[k], a[k1], b[k1], b[k]))
            except ValueError:
                pass
    if closed and cap_bottom:
        bm.faces.new(list(reversed(vr[0])))
    if closed and cap_top:
        bm.faces.new(vr[-1])
    bm.normal_update()
    return bm


def soft_box(sx, sy, sz, r, cuts=4, center=(0.0, 0.0, 0.0)):
    """Box with evenly rounded edges and a regular grid (good for deforming)."""
    bm = _new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    r = min(r, hx * 0.98, hy * 0.98, hz * 0.98)
    for v in bm.verts:
        p = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
        inner = Vector((max(-hx + r, min(hx - r, p.x)), max(-hy + r, min(hy - r, p.y)), max(-hz + r, min(hz - r, p.z))))
        dv = p - inner
        if dv.length > 1e-9:
            p = inner + dv.normalized() * r
        v.co = p + Vector(center)
    bm.normal_update()
    return bm


def deform(bm, fn):
    """Apply fn(Vector) -> Vector to every vertex."""
    for v in bm.verts:
        v.co = fn(v.co.copy())
    bm.normal_update()
    return bm


def subdivide(bm, cuts=1):
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    return bm
