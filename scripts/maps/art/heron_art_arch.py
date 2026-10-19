"""Heron Reach architecture, built around the generator's collision boxes.

Reads assets/blender/heron-reach/layout.json (written by scripts/maps/export-heron-layout.ts) and
adds render geometry only: brick and plaster faces chosen per side, window frames, sills, lintels
and lit interior cards, door frames and open leaves, slab edges and soffits, concrete gallery
upstands with handrails, stair nosings and balustrades, board-marked columns, roofs and parapets,
shop fronts, the undercroft's services, and home interiors. Nothing here is collision.
"""
import math
import random
from heron_art_mesh import Builder

STOREY = 3.0
CEIL = 2.8
SLAB = 0.2


def chunk(x, z):
    """4 x 4 grid of 36 x 30 m export chunks so the runtime can frustum-cull the site."""
    if x < -2 or x > 146 or z < -2 or z > 122:
        return 'OUT'
    return f'C{min(3, max(0, int(x // 36)))}{min(3, max(0, int(z // 30)))}'


class Arch:
    def __init__(self, L, builder: Builder, seed=1938):
        self.L = L
        self.B = builder
        self.rng = random.Random(seed)
        self.homes = [dict(h, w=9, d=8) for h in L['homes']]
        self.cores = L['cores']
        self.shops = L['shops']
        self.blocks = L['blocks']
        self.windows = []  # (x, y, z, axis, normal, width, height) for dressing / lights

    # --- helpers -----------------------------------------------------------------------------
    def g(self, kind, x, z):
        return f'{chunk(x, z)}/{kind}'

    def owner_rect(self, x, z, y):
        """Rectangle and type of the home/core/shop that contains a point, if any."""
        for h in self.homes:
            if h['x'] - .01 <= x <= h['x'] + 9.01 and h['z'] - .01 <= z <= h['z'] + 8.01 and h['y'] - .1 <= y < h['y'] + 2.9:
                return 'home', (h['x'], h['z'], 9, 8)
        for c in self.cores:
            r = c['rect']
            if r[0] - .01 <= x <= r[0] + r[2] + .01 and r[1] - .01 <= z <= r[1] + r[3] + .01:
                return 'core', r
        for s in self.shops:
            r = s['rect']
            if r[0] - .01 <= x <= r[0] + r[2] + .01 and r[1] - .01 <= z <= r[1] + r[3] + .01 and y < 3:
                return 'shop', r
        return None, None

    def grime(self, base_y, top=2.8, strength=.35):
        """Vertex colour: darker, damp band near the floor; slight lift towards the top."""
        def f(p):
            h = max(0.0, p[1] - base_y)
            k = 1 - strength * math.exp(-h / .45) - .08 * math.exp(-max(0, top - h) / .3)
            n = .94 + .06 * math.sin(p[0] * 1.7 + p[2] * 2.3)
            v = max(.35, k * n)
            return (v, v, v * .98, 1)
        return f

    # --- walls -------------------------------------------------------------------------------
    def walls(self):
        mats = {'home': ('hr_brick_stock', 'hr_plaster'), 'core': ('hr_brick_red', 'hr_brick_painted'), 'shop': ('hr_brick_red', 'hr_render')}
        for b in self.L['boxes']:
            bid = b['id']
            if not (bid.startswith('wall-') or bid.startswith('sill-') or bid.startswith('lintel-')):
                continue
            x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
            cx, cz, cy = (x0 + x1) / 2, (z0 + z1) / 2, (y0 + y1) / 2
            if bid == 'wall-B1':
                self.B.box(self.g('undercroft', cx, cz), 'hr_concrete_rough', x0, x1, y0, y1, z0, z1, faces='+x -x +z -z', col=self.waterline(y0))
                self.underpass_tiles(b)
                continue
            kind, rect = self.owner_rect(cx, cz, cy)
            if b['mat'] == 'plaster' or kind is None:
                self.B.box(self.g('interior', cx, cz), 'hr_plaster', x0, x1, y0, y1, z0, z1, faces='+x -x +z -z +y -y', col=self.grime(y0, strength=.12))
                continue
            outer, inner = mats[kind]
            rx, rz, rw, rd = rect
            mx, mz = rx + rw / 2, rz + rd / 2
            # The face pointing away from the owner's centre is the exterior.
            thin_x = (x1 - x0) < (z1 - z0)
            fm = {}
            if thin_x:
                fm['+x'], fm['-x'] = (outer, inner) if cx > mx else (inner, outer)
                fm['+z'] = fm['-z'] = outer
            else:
                fm['+z'], fm['-z'] = (outer, inner) if cz > mz else (inner, outer)
                fm['+x'] = fm['-x'] = outer
            fm['+y'] = 'hr_concrete_cast'
            fm['-y'] = None
            grp = self.g('facade' if kind != 'core' else 'cores', cx, cz)
            col = self.grime(y0 if y0 % 3 < .01 or y0 < 0 else math.floor(y0 / 3) * 3)
            ext = ('+x' if cx > mx else '-x') if thin_x else ('+z' if cz > mz else '-z')
            holes = self.blank_windows(b, kind, ext) if bid.startswith('wall-') and kind != 'shop' else []
            if holes:
                fm[ext] = None
                self.face_with_holes(grp, outer, b, ext, holes, col)
            self.B.box(grp, outer, x0, x1, y0, y1, z0, z1, mats=fm, col=col)
        for b in self.L['boxes']:
            if b['id'] in ('reserve',) or b['id'].startswith('cover-'):
                self.solid_feature(b)

    def underpass_tiles(self, b):
        """Cream glazed tiles to 2.4 m on the undercroft's room faces, 8 mm proud of the concrete."""
        x0, x1, y0, z0, z1 = b['x0'], b['x1'], b['y0'], b['z0'], b['z1']
        top = min(b['y1'], y0 + 2.4)
        inside = lambda x, z: any(r[0] <= x <= r[0] + r[2] and r[1] <= z <= r[1] + r[3] for r in self.L['floors']['B1'])
        grp = self.g('undercroft', (x0 + x1) / 2, (z0 + z1) / 2)
        col = self.waterline(y0)
        for k, (px, pz) in {'+x': (x1 + .3, (z0 + z1) / 2), '-x': (x0 - .3, (z0 + z1) / 2), '+z': ((x0 + x1) / 2, z1 + .3), '-z': ((x0 + x1) / 2, z0 - .3)}.items():
            if (k[1] == 'x') == ((x1 - x0) > (z1 - z0)) or not inside(px, pz):
                continue  # only the long faces that look into the room
            if k == '+x':
                self.B.box(grp, 'hr_tile_underpass', x1, x1 + .008, y0, top, z0, z1, faces='+x +y', col=col)
            elif k == '-x':
                self.B.box(grp, 'hr_tile_underpass', x0 - .008, x0, y0, top, z0, z1, faces='-x +y', col=col)
            elif k == '+z':
                self.B.box(grp, 'hr_tile_underpass', x0, x1, y0, top, z1, z1 + .008, faces='+z +y', col=col)
            else:
                self.B.box(grp, 'hr_tile_underpass', x0, x1, y0, top, z0 - .008, z0, faces='-z +y', col=col)

    # --- render-only windows in blank facade runs ----------------------------------------------
    def blank_windows(self, b, kind, ext):
        """Window rectangles (a0, a1, v0, v1) for a blank exterior wall run. The generator only
        opens the windows its plans call for; the rest of each brick run gets render-only windows,
        cut into the outer face with a reveal, so elevations read as lived-in flats. The wall's
        collision is unchanged and the glass stays opaque, so sight lines match the game."""
        x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
        along_x = ext in ('+z', '-z')
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        run = a1 - a0
        ww, wh, sill = (1.2, 1.35, .9) if kind == 'home' else (1.65, 2.35, .3)
        pitch = 2.6 if kind == 'home' else 3.0
        margin=.8 if kind=='home' else .45
        n = int((run + pitch - ww - margin) // pitch) if run >= ww + margin else 0
        if n <= 0:
            return []
        out = []
        sgn = 1 if ext[0] == '+' else -1
        face = (x1 if sgn > 0 else x0) if not along_x else (z1 if sgn > 0 else z0)
        for base in [y0 + k * STOREY for k in range(int((y1 - y0 + .05) // STOREY) + 1)]:
            if base + sill + wh > y1 - .2 or base < y0 - .01:
                continue
            for i in range(n):
                c = a0 + run * (i + .5) / n
                # Skip if something sits right in front of the face (another wall, a core, a slab edge).
                probe = (c, base + sill + wh / 2, face + sgn * .25) if along_x else (face + sgn * .25, base + sill + wh / 2, c)
                if self.occupied(probe):
                    continue
                out.append((c - ww / 2, c + ww / 2, base + sill, base + sill + wh, base))
        return out

    def occupied(self, p):
        x, y, z = p
        if not hasattr(self, '_occ'):
            self._occ = [(o['x0'], o['x1'], o['y0'], o['y1'], o['z0'], o['z1']) for o in self.L['boxes']
                         if o['id'] not in ('ground', 'boundary', 'tree') and not o['id'].startswith('cover-')]
        return any(a <= x <= b_ and c <= y <= d and e <= z <= f for a, b_, c, d, e, f in self._occ)

    def face_with_holes(self, grp, mat, b, ext, holes, col, depth=.16):
        """One wall face drawn as strips around rectangular holes, with reveals and a window in each."""
        x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
        along_x = ext in ('+z', '-z')
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        sgn = 1 if ext[0] == '+' else -1
        plane = (z1 if sgn > 0 else z0) if along_x else (x1 if sgn > 0 else x0)
        back = plane - sgn * depth

        def rect(u0, u1, v0, v1, key, at, m=mat):
            if u1 - u0 < 1e-4 or v1 - v0 < 1e-4:
                return
            if along_x:
                self.B.box(grp, m, u0, u1, v0, v1, at, at, faces=key, col=col)
            else:
                self.B.box(grp, m, at, at, v0, v1, u0, u1, faces=key, col=col)

        cuts = sorted({a0, a1, *[h[0] for h in holes], *[h[1] for h in holes]})
        for u0, u1 in zip(cuts, cuts[1:]):
            mid = (u0 + u1) / 2
            spans = sorted((h[2], h[3]) for h in holes if h[0] < mid < h[1])
            v = y0
            for s0, s1 in spans + [(y1, y1)]:
                rect(u0, u1, v, s0, ext, plane)
                v = s1
        flip = {'+x': '-x', '-x': '+x', '+z': '-z', '-z': '+z'}
        side_lo, side_hi = ('+x', '-x') if along_x else ('+z', '-z')
        lo, hi = min(plane, back), max(plane, back)
        for (h0, h1, v0, v1, base) in holes:
            # reveals face into the opening
            if along_x:
                self.B.box(grp, 'hr_render', h0, h0, v0, v1, lo, hi, faces='+x', col=col)
                self.B.box(grp, 'hr_render', h1, h1, v0, v1, lo, hi, faces='-x', col=col)
                self.B.box(grp, 'hr_render', h0, h1, v0, v0, lo, hi, faces='+y', col=col)
                self.B.box(grp, 'hr_render', h0, h1, v1, v1, lo, hi, faces='-y', col=col)
            else:
                self.B.box(grp, 'hr_render', lo, hi, v0, v1, h0, h0, faces='+z', col=col)
                self.B.box(grp, 'hr_render', lo, hi, v0, v1, h1, h1, faces='-z', col=col)
                self.B.box(grp, 'hr_render', lo, hi, v0, v0, h0, h1, faces='+y', col=col)
                self.B.box(grp, 'hr_render', lo, hi, v1, v1, h0, h1, faces='-y', col=col)
            c = (h0 + h1) / 2
            t = abs(plane - (b['z0'] + b['z1']) / 2 if along_x else plane - (b['x0'] + b['x1']) / 2) * 2
            mid_plane = plane - sgn * t / 2
            o = dict(kind='window', x=c if along_x else mid_plane, z=mid_plane if along_x else c, y=base,
                     axis='x' if along_x else 'z', normal=sgn, width=h1 - h0, sill=v0 - base, height=v1 - v0,
                     wall=t, owner=self.owner_rect(c if along_x else mid_plane, mid_plane if along_x else c, base + 1)[0] or 'home', lit=False)
            self.window(o, self.rng, cosmetic=True, back=back)

    def waterline(self, y0):
        def f(p):
            h = p[1] - y0
            v = .55 + .45 * min(1, h / 1.1) if h < 1.1 else (.92 - .25 * (abs(h - 1.12) < .06))
            return (v, v, v * .97, 1)
        return f

    def solid_feature(self, b):
        x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        kind = next((c['kind'] for c in self.L['cover'] if 'cover-' + c['id'] == b['id']), 'reserve')
        grp = self.g('landscape', cx, cz)
        if 'planter' in kind:
            # Precast planter: 120 mm walls, soil 150 mm below the rim, shrubs from the foliage kit.
            t = .12
            for (a0, a1, c0, c1) in [(x0, x1, z0, z0 + t), (x0, x1, z1 - t, z1), (x0, x0 + t, z0 + t, z1 - t), (x1 - t, x1, z0 + t, z1 - t)]:
                self.B.box(grp, 'hr_concrete_cast', a0, a1, y0, y1, c0, c1, faces='+x -x +z -z +y', col=self.grime(y0, top=y1 - y0, strength=.45))
            self.B.box(grp, 'hr_soil', x0 + t, x1 - t, y0, y1 - .15, z0 + t, z1 - t, faces='+y')
        elif 'privacy' in kind:
            # Gallery privacy screen: black steel frame with vertical timber slats.
            grp = self.g('galleries', cx, cz)
            self.B.box(grp, 'hr_steel_black', x0, x1, y1 - .06, y1, z0, z1)
            along_x = (x1 - x0) > (z1 - z0)
            n = int(((x1 - x0) if along_x else (z1 - z0)) / .14)
            for i in range(n):
                if along_x:
                    a = x0 + (i + .5) * (x1 - x0) / n
                    self.B.box(grp, 'hr_timber', a - .04, a + .04, y0, y1 - .06, z0 + .1, z1 - .1)
                else:
                    a = z0 + (i + .5) * (z1 - z0) / n
                    self.B.box(grp, 'hr_timber', x0 + .1, x1 - .1, y0, y1 - .06, a - .04, a + .04)
        else:
            mat = 'hr_brick_red' if 'screen' in kind else 'hr_brick_stock'
            self.B.box(grp, mat, x0, x1, y0, y1 - .08, z0, z1, faces='+x -x +z -z', col=self.grime(y0, top=y1 - y0, strength=.5))
            self.B.box(grp, 'hr_concrete_cast', x0 - .04, x1 + .04, y1 - .08, y1, z0 - .04, z1 + .04)

    # --- openings ----------------------------------------------------------------------------
    def openings(self):
        rng = self.rng
        for o in self.L['openings']:
            kind = o['kind']
            if kind.startswith('inner-'):
                if kind == 'inner-door':
                    self.door(o, inner=True)
                continue
            if kind == 'window':
                self.window(o, rng)
            elif kind == 'door':
                self.door(o)
            elif kind == 'arch':
                pass

    def frame_axes(self, o):
        """Unit vectors: along the wall (a), outward normal (n); centre at the wall mid-plane."""
        if o['axis'] == 'x':
            return (1, 0), (0, o['normal'])
        return (0, 1), (o['normal'], 0)

    def window(self, o, rng, cosmetic=False, back=None):
        (ax, az), (nx, nz) = self.frame_axes(o)
        w, h, sill, y = o['width'], o['height'], o['sill'], o['y']
        cx, cz, t = o['x'], o['z'], o['wall']
        shop = o['owner'] in [s['id'] for s in self.shops]
        core = o['owner'] == 'core' or (o['owner'].startswith('S') and len(o['owner']) == 2)
        grp = self.g('windows', cx, cz)
        inset = -t / 2 + .07  # glass plane, measured from the outer face inward (n points out)
        def P(u, v, d):  # u along wall from centre, v height above storey, d along outward normal
            return (cx + ax * u + nx * d, y + v, cz + az * u + nz * d)
        y0, y1 = sill, sill + h
        fw = .065 if not shop else .08
        frame = 'hr_steel_black' if shop or core else 'hr_upvc_white'
        def bar(u0, u1, v0, v1, d0, d1, mat=frame):
            pts = [P(u0, v0, d0), P(u1, v1, d1)]
            xs = sorted([pts[0][0], pts[1][0]]); zs = sorted([pts[0][2], pts[1][2]])
            self.B.box(grp, mat, xs[0], xs[1], min(pts[0][1], pts[1][1]), max(pts[0][1], pts[1][1]), zs[0], zs[1])
        d0, d1 = t / 2 - .14, t / 2 - .06
        # outer frame
        bar(-w / 2, w / 2, y0, y0 + fw, d0, d1); bar(-w / 2, w / 2, y1 - fw, y1, d0, d1)
        bar(-w / 2, -w / 2 + fw, y0, y1, d0, d1); bar(w / 2 - fw, w / 2, y0, y1, d0, d1)
        panes = max(1, round(w / (1.4 if not shop else 2.2)))
        for i in range(1, panes):
            u = -w / 2 + i * w / panes
            bar(u - fw / 2, u + fw / 2, y0, y1, d0, d1)
        if not shop and h > 1.2:
            v = y1 - .42
            bar(-w / 2, w / 2, v - fw / 2, v + fw / 2, d0, d1)
        # glass pane (thin) at the frame plane
        g0 = P(-w / 2 + fw, y0 + fw, (d0 + d1) / 2)
        g1 = P(w / 2 - fw, y1 - fw, (d0 + d1) / 2)
        self.pane(grp, 'hr_glass', g0, g1, (nx, nz))
        # Lit interior card just behind the glass, facing out (single-sided: invisible from inside).
        if cosmetic and core:
            # Stair-core strip window: glass blocks with the lit stair glowing through.
            self.pane(grp, 'hr_glass_blocks', P(-w / 2, y0, -t / 2 + .04), P(w / 2, y1, -t / 2 + .04), (nx, nz))
            # Thin dark glazing bars give tall vertical bays a readable industrial scale.
            bar(-.025,.025,y0,y1,d0-.01,d1+.01,'hr_steel_black')
        if not shop:
            lit = o.get('lit') or rng.random() < (.55 if not core else .0)
            if not core:
                cell = rng.randrange(32) if lit else rng.choice([4, 12, 20, 28])
                c0 = P(-w / 2 + fw, y0 + fw, (d0 + d1) / 2 - .05)
                c1 = P(w / 2 - fw, y1 - fw, (d0 + d1) / 2 - .05)
                self.card(grp, 'hr_window_interior' if lit else 'hr_window_dark', c0, c1, (nx, nz), cell)
                self.windows.append(dict(x=cx + nx * t / 2, y=y + (y0 + y1) / 2, z=cz + nz * t / 2, nx=nx, nz=nz, lit=lit, w=w, h=h))
        # precast sill outside and a lintel band above
        out = t / 2
        self.B.box(grp, 'hr_concrete_cast', *self.span(P(-w / 2 - .06, y0 - .07, out - .02), P(w / 2 + .06, y0, out + .06)))
        if not shop:
            self.B.box(grp, 'hr_concrete_cast', *self.span(P(-w / 2 - .12, y1, out - .01), P(w / 2 + .12, y1 + .16, out + .012)))

    @staticmethod
    def span(p, q):
        return (min(p[0], q[0]), max(p[0], q[0]), min(p[1], q[1]), max(p[1], q[1]), min(p[2], q[2]), max(p[2], q[2]))

    def pane(self, grp, mat, p0, p1, n):
        nx, nz = n
        (x0, y0, z0), (x1, y1, z1) = p0, p1
        if nz:  # plane z = const, facing +-z
            z = z0
            pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] if nz > 0 else [(x1, y0, z), (x0, y0, z), (x0, y1, z), (x1, y1, z)]
        else:
            x = x0
            pts = [(x, y0, z1), (x, y0, z0), (x, y1, z0), (x, y1, z1)] if nx > 0 else [(x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0)]
        # orient so the quad faces outward
        a, b, c = pts[0], pts[1], pts[2]
        nrm = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]), 0, (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if nrm[0] * nx + nrm[2] * nz < 0:
            pts = pts[::-1]
        self.B.quad(grp, mat, *pts)
        return pts

    def card(self, grp, mat, p0, p1, n, cell):
        """Quad with UVs selecting one 8 x 4 atlas cell (cell 0 top-left)."""
        pts = self.pane(grp, mat, p0, p1, n)
        acc = self.B.acc(grp, mat)
        cx, cy = cell % 8, cell // 8
        u0, u1 = cx / 8, (cx + 1) / 8
        v1, v0 = 1 - cy / 4, 1 - (cy + 1) / 4
        # pts are ordered bottom-left, bottom-right, top-right, top-left as seen from outside
        acc.uvs[-1] = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

    def door(self, o, inner=False):
        (ax, az), (nx, nz) = self.frame_axes(o)
        w, h, y, t = o['width'], o['height'], o['y'], o['wall']
        cx, cz = o['x'], o['z']
        public = o['owner'].startswith('S') and len(o['owner']) == 2
        shop = o['owner'] in [s['id'] for s in self.shops]
        grp = self.g('doors' if not inner else 'interior', cx, cz)
        def P(u, v, d):
            return (cx + ax * u + nx * d, y + v, cz + az * u + nz * d)
        fw = .06
        frame = 'hr_steel_black' if public or shop else ('hr_upvc_white' if not inner else 'hr_timber')
        for u0, u1 in [(-w / 2, -w / 2 + fw), (w / 2 - fw, w / 2)]:
            self.B.box(grp, frame, *self.span(P(u0, 0, -t / 2), P(u1, h, t / 2)))
        self.B.box(grp, frame, *self.span(P(-w / 2, h - fw, -t / 2), P(w / 2, h, t / 2)))
        # Threshold strip
        self.B.box(grp, 'hr_steel_galv' if not inner else 'hr_timber', *self.span(P(-w / 2, 0, -t / 2), P(w / 2, .012, t / 2)))
        if public:
            # Public core doors: pair of steel-framed wired-glass leaves held open against the wall inside.
            for s in (-1, 1):
                hinge = s * (w / 2 - fw)
                lw = w / 2 - fw
                self.leaf(grp, P, hinge, -s, lw, h - fw, -t / 2 - .02, 'hr_steel_black', glass='hr_wired_glass')
            # wall-mounted intercom handled by dressing
        else:
            lw = w - 2 * fw
            # Hinge on the side nearer the module edge so the open leaf hugs the hall wall.
            side = -1 if (ax * (cx - self.module_centre(o)[0]) + az * (cz - self.module_centre(o)[1])) <= 0 else 1
            hinge = side * (w / 2 - fw)
            self.leaf(grp, P, hinge, -side, lw, h - fw, -t / 2 - .02, 'hr_door_paint' if not inner else 'hr_plaster', glass=not inner and o['height'] > 2.1)
        if not inner and not public:
            # Number plate and letterbox on home and shop doors.
            pass

    def module_centre(self, o):
        for h in self.homes:
            if h['x'] - .01 <= o['x'] <= h['x'] + 9.01 and h['z'] - .01 <= o['z'] <= h['z'] + 8.01:
                return h['x'] + 4.5, h['z'] + 4
        for s in self.shops:
            r = s['rect']
            if r[0] - .01 <= o['x'] <= r[0] + r[2] + .01 and r[1] - .01 <= o['z'] <= r[1] + r[3] + .01:
                return r[0] + r[2] / 2, r[1] + r[3] / 2
        return o['x'], o['z']

    def leaf(self, grp, P, hinge, toward, lw, lh, d, mat, glass=False):
        """Door leaf swung 92 degrees inward from the hinge (d is the inner face offset)."""
        th = .045
        a = math.radians(92)
        # Leaf spans from the hinge along (cos a * toward along wall, sin a inward)
        u_end = hinge + toward * lw * math.cos(a)
        d_end = d - lw * math.sin(a)
        # Approximate the rotated leaf as an axis-aligned slab (92 degrees is near perpendicular).
        u0, u1 = sorted([hinge, hinge + toward * th])
        self.B.box(grp, mat, *self.span(P(u0, .01, d), P(u1, lh, d_end)))
        if glass:
            g0, g1 = P(u0 - .002, lh * .45, d - .12), P(u1 + .002, lh - .15, d_end + .12)
            self.B.box(grp, glass if isinstance(glass, str) else 'hr_glass', *self.span(g0, g1))

    # --- slabs, roofs, edges -------------------------------------------------------------------
    def slabs(self):
        homes_by_level = {}
        for b in self.L['boxes']:
            bid = b['id']
            if bid not in ('slab', 'roof', 'landing') and not bid.endswith('-cap'):
                continue
            x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            if bid == 'landing':
                self.B.box(self.g('cores', cx, cz), 'hr_concrete_cast', x0, x1, y0, y1, z0, z1, faces='+y -y +x -x +z -z', mats={'-y': 'hr_concrete_board'})
                continue
            top = 'hr_concrete_cast'
            if bid == 'roof' or bid.endswith('-cap'):
                top = 'hr_roof_felt'
            elif y1 > 8.9 and bid == 'slab':
                top = 'hr_paving'
            elif y1 < -2.9:
                top = 'hr_concrete_rough'
            grp = self.g('slabs' if y1 > -1 else 'undercroft', cx, cz)
            col = (lambda p: (.9 + .1 * math.sin(p[0] * .7 + p[2] * .9), .9 + .1 * math.sin(p[0] * .7 + p[2] * .9), .9, 1))
            self.B.box(grp, top, x0, x1, y0, y1, z0, z1, mats={'-y': 'hr_concrete_board', '+x': 'hr_concrete_cast', '-x': 'hr_concrete_cast', '+z': 'hr_concrete_cast', '-z': 'hr_concrete_cast'}, col=col)

    def guards(self):
        """Concrete upstands with a steel handrail on +3/+6 edges; brick parapets with copings on roofs."""
        for gd in self.L['guards']:
            y = gd['y']
            x0, z0, x1, z1, nx, nz = gd['x0'], gd['z0'], gd['x1'], gd['z1'], gd['nx'], gd['nz']
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            grp = self.g('galleries', cx, cz)
            t = .16
            ext = .08
            def rect(off0, off1, ya, yb, mat, faces='all', mats=None, extend=0.0):
                if nz:
                    zz = sorted([z0 + nz * off0, z0 + nz * off1])
                    self.B.box(grp, mat, min(x0, x1) - extend, max(x0, x1) + extend, ya, yb, zz[0], zz[1], faces=faces, mats=mats)
                else:
                    xx = sorted([x0 + nx * off0, x0 + nx * off1])
                    self.B.box(grp, mat, xx[0], xx[1], ya, yb, min(z0, z1) - extend, max(z0, z1) + extend, faces=faces, mats=mats)
            roof = y > 8.9
            # slab edge beam / fascia below the walking surface
            rect(0, t + ext, y - .55, y, 'hr_concrete_cast', faces='+x -x +z -z -y', extend=0)
            if roof:
                rect(0, t + ext, y, y + 1.12, 'hr_brick_stock', faces='+x -x +z -z')
                rect(-.03, t + ext + .03, y + 1.12, y + 1.2, 'hr_concrete_cast')
            else:
                rect(0, t + ext, y, y + 1.0, 'hr_concrete_aggregate', faces='+x -x +z -z')
                rect(-.02, t + ext + .02, y + 1.0, y + 1.05, 'hr_concrete_cast', faces='+y +x -x +z -z')
                # steel handrail on short posts
                L = math.hypot(x1 - x0, z1 - z0)
                ux, uz = (x1 - x0) / max(L, 1e-6), (z1 - z0) / max(L, 1e-6)
                ox, oz = nx * (t + ext) / 2, nz * (t + ext) / 2
                self.B.cylinder(grp, 'hr_steel_black', (x0 + ox, y + 1.2, z0 + oz), (x1 + ox, y + 1.2, z1 + oz), .024, seg=8)
                n = max(1, int(L / 1.5))
                for i in range(n + 1):
                    px, pz = x0 + ux * L * i / n + ox, z0 + uz * L * i / n + oz
                    self.B.cylinder(grp, 'hr_steel_black', (px, y + 1.05, pz), (px, y + 1.2, pz), .016, seg=6, caps=False)
            # drip stain under the fascia
        # Core and private-stair guards: steel balusters with handrail.
        for b in self.L['boxes']:
            bid = b['id']
            if not (bid.endswith('-guard') or bid.endswith('-balustrade')) or bid == 'guard':
                continue
            self.balustrade(b)

    def balustrade(self, b):
        x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        grp = self.g('cores', cx, cz)
        along_x = (x1 - x0) > (z1 - z0)
        mid = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
        L = (x1 - x0) if along_x else (z1 - z0)
        if b['id'].endswith('-balustrade'):
            # Full-height well balustrade (collision); render rails per storey along the flights.
            for k in range(int((y1 - y0 - 1.2) / 1.5 + .01) + 1):
                base = y0 + k * 1.5
                self.rail_run(grp, along_x, mid, (x0, x1) if along_x else (z0, z1), base, base + 1.5)
            return
        # Horizontal guard at a landing edge
        self.rail_run(grp, along_x, mid, (x0, x1) if along_x else (z0, z1), y0, y0)

    def rail_run(self, grp, along_x, mid, ends, ya, yb):
        a0, a1 = ends
        L = a1 - a0
        P = (lambda a, y: (a, y, mid)) if along_x else (lambda a, y: (mid, y, a))
        # sloped handrail from (a0, ya) to (a1, yb) at 1.0 m, balusters every 0.12 m
        self.B.cylinder(grp, 'hr_steel_black', P(a0, ya + 1.0), P(a1, yb + 1.0), .022, seg=8)
        self.B.cylinder(grp, 'hr_steel_black', P(a0, ya + .1), P(a1, yb + .1), .012, seg=6)
        n = max(1, int(L / .12))
        for i in range(n + 1):
            a = a0 + L * i / n
            yy = ya + (yb - ya) * i / n
            self.B.cylinder(grp, 'hr_steel_black', P(a, yy + .1), P(a, yy + 1.0), .008, seg=4, caps=False)

    # --- stairs ---------------------------------------------------------------------------------
    def stairs(self):
        for b in self.L['boxes']:
            if b['id'] != 'stair':
                continue
            x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            grp = self.g('cores', cx, cz)
            # Core treads get the painted tread map on top (added with the nosing below).
            core = self.owner_rect(cx, cz, y1 - .05)[0] == 'core'
            self.B.box(grp, 'hr_concrete_cast', x0, x1, y0, y1, z0, z1, mats={'-y': 'hr_concrete_board', '+y': None if core else 'hr_concrete_cast'})
            # anti-slip nosing on the rising edge: the edge facing down-flight is the lower neighbour side.
        self.nosings()

    def nosings(self):
        steps = [b for b in self.L['boxes'] if b['id'] == 'stair']
        tops = {}
        for b in steps:
            tops.setdefault((round(b['x0'], 2), round(b['x1'], 2)), []).append(b)
        for b in steps:
            x0, x1, y1, z0, z1 = b['x0'], b['x1'], b['y1'], b['z0'], b['z1']
            # Find the tread one rise lower in the same flight to know which edge is the nosing.
            lower = [q for q in tops[(round(x0, 2), round(x1, 2))] if abs(q['y1'] - (y1 - .15)) < .01 and (abs(q['z0'] - z1) < .01 or abs(q['z1'] - z0) < .01)]
            core = self.owner_rect((x0 + x1) / 2, (z0 + z1) / 2, y1 - .05)[0] == 'core'
            if not lower:
                if core:  # first step of a flight: plain top, as the tread box no longer draws one
                    self.B.box(self.g('cores', (x0 + x1) / 2, z0), 'hr_concrete_cast', x0, x1, y1, y1, z0, z1, faces='+y')
                continue
            q = lower[0]
            edge = z1 if abs(q['z0'] - z1) < .01 else z0
            s = 1 if edge == z1 else -1
            grp = self.g('cores', (x0 + x1) / 2, edge)
            if core:
                # Painted tread, one 0-1 map per step with the yellow nosing (V = 0) on the front edge.
                back = z0 if edge == z1 else z1
                pts = [(x0, y1, edge), (x1, y1, edge), (x1, y1, back), (x0, y1, back)]
                uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
                if s < 0:  # keep the quad facing up
                    pts, uv = [pts[1], pts[0], pts[3], pts[2]], [uv[1], uv[0], uv[3], uv[2]]
                self.B.quad(grp, 'hr_stair_tread', *pts, uv=uv)
                continue
            za, zb = sorted([edge, edge - s * .055])
            self.B.box(grp, 'hr_rubber', x0 + .05, x1 - .05, y1, y1 + .006, za, zb, faces='+y +z -z')

    # --- columns, roofs, cores, shops -------------------------------------------------------------
    def columns(self):
        for c in self.L['columns']:
            s = c['size'] / 2
            grp = self.g('columns', c['x'], c['z'])
            self.B.box(grp, 'hr_concrete_board', c['x'] - s, c['x'] + s, 0, CEIL, c['z'] - s, c['z'] + s, faces='+x -x +z -z', col=self.grime(0, strength=.4))
            # chamfered base plinth
            self.B.box(grp, 'hr_concrete_cast', c['x'] - s - .03, c['x'] + s + .03, 0, .12, c['z'] - s - .03, c['z'] + s + .03, faces='+x -x +z -z +y')

    def roofs(self):
        """Parapets on non-playable roofs and core caps, plus copings."""
        for b in self.L['boxes']:
            if b['id'] != 'roof' and not b['id'].endswith('-cap'):
                continue
            x0, x1, y1, z0, z1 = b['x0'], b['x1'], b['y1'], b['z0'], b['z1']
            if y1 < 3.1 and b['id'] == 'roof':
                ph = .35  # shop roof upstand
            else:
                ph = .6
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            grp = self.g('roofs', cx, cz)
            t = .2
            mat = 'hr_brick_red' if b['id'].endswith('-cap') or y1 < 3.1 else 'hr_brick_stock'
            for (a0, a1, c0, c1) in [(x0, x1, z0, z0 + t), (x0, x1, z1 - t, z1), (x0, x0 + t, z0 + t, z1 - t), (x1 - t, x1, z0 + t, z1 - t)]:
                self.B.box(grp, mat, a0, a1, y1, y1 + ph, c0, c1, faces='+x -x +z -z')
                self.B.box(grp, 'hr_concrete_cast', a0 - .03, a1 + .03, y1 + ph, y1 + ph + .06, c0 - .03, c1 + .03)

    def ground(self):
        """Ground zoning: asphalt base, paved concourses, red pavers in Washhouse Square, the court,
        grass and soil beds with kerbs. Split into 2 m quads so vertex dirt can vary."""
        L = self.L
        site = L['site']
        zones = []  # (rect, material) later entries win
        zones.append(((site[0], site[1], site[2], site[3]), 'hr_asphalt'))
        for b in L['blocks']:
            x, z, w, d = b['rect']
            zones.append(((x - 4, z - 4, w + 8, d + 8), 'hr_paving'))
        for s in L['surfaces']:
            if s['level'] == 'L1' and s['id'].startswith('gallery-'):
                x, z, w, d = s['rect']
                zones.append(((x - 2, z - 2, w + 4, d + 4), 'hr_paving'))
        for s in L['shops']:
            x, z, w, d = s['rect']
            zones.append(((x - 3, z - 3, w + 6, d + 6), 'hr_paving'))
        zones.append(((66, 84, 12, 24), 'hr_pavers_red'))  # Washhouse Square between the two service blocks
        zones.append(((60, 36, 24, 12), 'hr_pavers_red'))  # threshold south of Garden Court
        zones.append(((L['cage']['rect'][0] - 1.5, L['cage']['rect'][1] - 1.5, L['cage']['rect'][2] + 3, L['cage']['rect'][3] + 3), 'hr_paving'))
        zones.append((tuple(L['cage']['rect']), 'hr_court'))
        garden = next(s['rect'] for s in L['surfaces'] if s['id'] == 'garden')
        zones.append((tuple(garden), 'hr_grass_ground'))
        # paths across the garden to the objective
        gx, gz, gw, gd = garden
        zones.append(((gx + gw / 2 - 1.5, gz, 3, gd), 'hr_paving'))
        zones.append(((gx, gz + gd / 2 - 1.5, gw, 3), 'hr_paving'))
        zones.append(((gx + gw / 2 - 4, gz + gd / 2 - 4, 8, 8), 'hr_paving'))
        for p in L['planting']:
            zones.append((tuple(p['rect']), 'hr_grass_ground'))
        self.zones = zones
        cells = {}
        step = 2.0
        nx, nz = int(site[2] / step), int(site[3] / step)
        for i in range(nx):
            for j in range(nz):
                x, z = site[0] + (i + .5) * step, site[1] + (j + .5) * step
                mat = 'hr_asphalt'
                for (r, m) in zones:
                    if r[0] <= x <= r[0] + r[2] and r[1] <= z <= r[1] + r[3]:
                        mat = m
                cells[(i, j)] = mat
        # Grass cells (2 m) for the runtime grass field, in map coordinates.
        self.grass_cells = [(site[0] + i * step, site[1] + j * step) for (i, j), m in sorted(cells.items()) if m == 'hr_grass_ground']
        # Ground quads, skipped where a B1 core opens below G.
        holes = [c['rect'] for c in self.cores if c['levels'][0] < 0]
        def dirt(p):
            x, z = p[0], p[2]
            v = .82 + .1 * math.sin(x * .23 + z * .17) * math.sin(x * .11 - z * .29) + .06 * math.sin(x * 1.3) * math.sin(z * 1.1)
            return (v, v, v * .98, 1)
        for (i, j), mat in cells.items():
            x0, z0 = site[0] + i * step, site[1] + j * step
            x1, z1 = x0 + step, z0 + step
            if any(r[0] <= x0 + 1 <= r[0] + r[2] and r[1] <= z0 + 1 <= r[1] + r[3] for r in holes):
                continue
            y = .0 if mat not in ('hr_grass_ground',) else .01
            self.B.quad(self.g('ground', x0 + 1, z0 + 1), mat, (x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0), col=dirt)
        # kerbs where paving meets asphalt or grass
        for (i, j), mat in cells.items():
            for di, dj in ((1, 0), (0, 1)):
                other = cells.get((i + di, j + dj))
                if other is None or other == mat:
                    continue
                pair = {mat, other}
                if pair & {'hr_grass_ground'} or pair == {'hr_paving', 'hr_asphalt'}:
                    x0, z0 = site[0] + (i + di) * step, site[1] + (j + dj) * step
                    if di:
                        self.B.box(self.g('ground', x0, z0 + 1), 'hr_concrete_cast', x0 - .07, x0 + .07, 0, .08, z0, z0 + step, faces='+x -x +y')
                    else:
                        self.B.box(self.g('ground', x0 + 1, z0), 'hr_concrete_cast', x0, x0 + step, 0, .08, z0 - .07, z0 + .07, faces='+z -z +y')

    def undercroft(self):
        """Ceiling soffit, downstand beams, cable trays, pipes and strip lights in B1."""
        for r in self.L['floors']['B1']:
            x, z, w, d = r
            grp = self.g('undercroft', x + w / 2, z + d / 2)
            # soffit = underside of the ground slab
            self.B.quad(grp, 'hr_concrete_board', (x, -.2, z), (x + w, -.2, z), (x + w, -.2, z + d), (x, -.2, z + d))
            long_x = w >= d
            L = w if long_x else d
            n = int(L / 6)
            for k in range(1, n + 1):
                a = (x if long_x else z) + k * L / (n + 1)
                if long_x:
                    self.B.box(grp, 'hr_concrete_board', a - .2, a + .2, -.5, -.2, z, z + d, faces='+x -x -y')
                else:
                    self.B.box(grp, 'hr_concrete_board', x, x + w, -.5, -.2, a - .2, a + .2, faces='+z -z -y')
            # services along one side: two pipes and a cable tray
            if long_x:
                zz = z + .45
                self.B.cylinder(grp, 'hr_steel_galv', (x + .2, -.65, zz), (x + w - .2, -.65, zz), .08, seg=10)
                self.B.cylinder(grp, 'hr_plastic_black', (x + .2, -.6, zz + .25), (x + w - .2, -.6, zz + .25), .05, seg=8)
                self.B.box(grp, 'hr_steel_galv', x + .2, x + w - .2, -.42, -.38, z + .9, z + 1.25)
                for k in range(int(w / 5)):
                    lx = x + 2.5 + k * 5
                    self.B.box(grp, 'hr_lamp_emit', lx - .6, lx + .6, -.24, -.2, z + d / 2 - .06, z + d / 2 + .06, faces='-y')
                    self.B.box(grp, 'hr_steel_galv', lx - .62, lx + .62, -.2, -.17, z + d / 2 - .08, z + d / 2 + .08, faces='+x -x +z -z')
            else:
                xx = x + .45
                self.B.cylinder(grp, 'hr_steel_galv', (xx, -.65, z + .2), (xx, -.65, z + d - .2), .08, seg=10)
                self.B.cylinder(grp, 'hr_plastic_black', (xx + .25, -.6, z + .2), (xx + .25, -.6, z + d - .2), .05, seg=8)
                self.B.box(grp, 'hr_steel_galv', x + .9, x + 1.25, -.42, -.38, z + .2, z + d - .2)
                for k in range(int(d / 5)):
                    lz = z + 2.5 + k * 5
                    self.B.box(grp, 'hr_lamp_emit', x + w / 2 - .06, x + w / 2 + .06, -.24, -.2, lz - .6, lz + .6, faces='-y')

    def interiors(self):
        """Home floors, ceilings and furniture modelled over the generator's furniture boxes."""
        for h in self.homes:
            x, z, y = h['x'], h['z'], h['y']
            grp = self.g('interior', x + 4.5, z + 4)
            self.B.quad(grp, 'hr_floor_laminate', (x + .2, y + .004, z + 7.8), (x + 8.8, y + .004, z + 7.8), (x + 8.8, y + .004, z + .2), (x + .2, y + .004, z + .2))
            self.B.quad(grp, 'hr_ceiling', (x + .2, y + 2.795, z + .2), (x + 8.8, y + 2.795, z + .2), (x + 8.8, y + 2.795, z + 7.8), (x + .2, y + 2.795, z + 7.8))
            # pendant lamp shade
            self.B.cylinder(grp, 'hr_lamp_emit', (x + 6.5, y + 2.45, z + 6), (x + 6.5, y + 2.6, z + 6), .16, seg=10, r2=.08)
        for b in self.L['boxes']:
            if not b['id'].startswith('home-'):
                continue
            kind = b['id'][5:]
            x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
            grp = self.g('interior', (x0 + x1) / 2, (z0 + z1) / 2)
            if kind == 'bed':
                self.B.box(grp, 'hr_wood_furniture', x0, x1, y0, y0 + .3, z0, z1)
                self.B.box(grp, 'hr_fabric', x0 + .03, x1 - .03, y0 + .3, y1, z0 + .03, z1 - .03)
            elif kind == 'sofa':
                self.B.box(grp, 'hr_fabric', x0, x1, y0 + .1, y0 + .45, z0, z1)
                along_x = (x1 - x0) > (z1 - z0)
                if along_x:
                    self.B.box(grp, 'hr_fabric', x0, x1, y0 + .45, y1, z1 - .2, z1)
                else:
                    self.B.box(grp, 'hr_fabric', x0, x0 + .2, y0 + .45, y1, z0, z1)
            elif kind == 'counter':
                self.B.box(grp, 'hr_kitchen', x0, x1, y0, y1 - .04, z0, z1)
                self.B.box(grp, 'hr_concrete_cast', x0 - .02, x1 + .02, y1 - .04, y1, z0 - .02, z1 + .02)
            elif kind == 'bath':
                self.B.box(grp, 'hr_ceramic', x0, x1, y0, y1, z0, z1, faces='+x -x +z -z')
                self.B.box(grp, 'hr_ceramic', x0 + .06, x1 - .06, y0 + .2, y0 + .21, z0 + .06, z1 - .06, faces='+y')
            elif kind == 'table':
                self.B.box(grp, 'hr_wood_furniture', x0, x1, y1 - .04, y1, z0, z1)
                for (a, c) in [(x0 + .05, z0 + .05), (x1 - .09, z0 + .05), (x0 + .05, z1 - .09), (x1 - .09, z1 - .09)]:
                    self.B.box(grp, 'hr_wood_furniture', a, a + .04, y0, y1 - .04, c, c + .04, faces='+x -x +z -z')

    def cores_extra(self):
        """Big painted level numbers on each core's back wall, above the half landing, as in the
        stairwell concept frame; and ceiling strip fittings under the decks where the dressing
        plan put a ceiling light."""
        labels = {-3: 'B1', 0: 'G', 3: '1', 6: '2', 9: 'R'}
        for c in self.cores:
            cx, cz = c['rect'][0], c['rect'][1]
            mirror = c['mirror']
            wz = cz + 5.8 if mirror else cz + .2
            n = -1 if mirror else 1
            for y in c['levels']:
                grp = self.g('cores', cx + 3, cz + 3)
                label = labels.get(int(round(y)), str(y))
                self.painted_text(grp, 'hr_paint_yellow', label, cx + 3, y + 2.05, wz + n * .009, n, size=1.2 if len(label) == 1 else .9)
                # Existing entry/landing zone: fittings above the 2.4 m clearance envelope.
                lz=cz+1 if mirror else cz+5
                self.B.box(grp,'hr_steel_galv',cx+1.05,cx+2.45,y+2.68,y+2.78,lz-.11,lz+.11)
                self.B.box(grp,'hr_core_strip',cx+1.1,cx+2.4,y+2.665,y+2.68,lz-.08,lz+.08,faces='-y')
                # Riser and clips tuck into the back corner, outside the walking lane.
                px=cx+.31; pz=wz+n*.09
                self.B.cylinder(grp,'hr_steel_galv',(px,y+.12,pz),(px,y+2.75,pz),.035,8)
                for h in [.4,1.5,2.5]:
                    self.B.box(grp,'hr_steel_black',px-.055,px+.055,y+h-.025,y+h+.025,pz-.05,pz+.05)
        for a in self.L.get('anchors', []):
            if a['kind'] != 'ceiling':
                continue
            x, y, z = a['x'], a['y'], a['z']
            grp = self.g('galleries', x, z)
            top = y + .26
            self.B.box(grp, 'hr_steel_galv', x - .65, x + .65, top - .09, top, z - .09, z + .09, faces='+x -x +z -z -y', mats={'-y': None})
            self.B.box(grp, 'hr_lamp_emit', x - .6, x + .6, top - .1, top - .09, z - .06, z + .06, faces='-y')

    def painted_text(self, grp, mat, text, x, y, z, n, size=.9):
        """Text as flat mesh on a wall facing +z (n=1) or -z (n=-1), centred on (x, y)."""
        import bpy
        cu = bpy.data.curves.new('label', 'FONT')
        cu.body = text
        cu.size = size
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        ob = bpy.data.objects.new('label', cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        acc = self.B.acc(grp, mat)
        for t in me.loop_triangles:
            pts = [me.vertices[i].co for i in t.vertices]
            # font X -> along the wall (mirrored for -z so it reads correctly), font Y -> up
            P = [(x + n * p.x, y + p.y, z) for p in pts]
            if n < 0:
                P = P[::-1]
            acc.poly(P, [(0, 0)] * 3, (1, 1, 1, 1))
        ob.evaluated_get(dg).to_mesh_clear()
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)

    def facade_dressing(self):
        """Render-only kit fittings on the brick: downpipes at wall ends, satellite dishes, airbricks
        and kitchen vents. Placements use the kits' wall mount (origin on the face, front outward)."""
        rng = random.Random(77)
        items = []
        face = lambda nx, nz: math.atan2(nx, nz)
        for b in self.L['boxes']:
            bid = b['id']
            if not bid.startswith('wall-') or b['mat'] == 'plaster' or bid == 'wall-B1':
                continue
            x0, x1, y0, y1, z0, z1 = b['x0'], b['x1'], b['y0'], b['y1'], b['z0'], b['z1']
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            kind, rect = self.owner_rect(cx, cz, (y0 + y1) / 2)
            if kind != 'home':
                continue
            mx, mz = rect[0] + rect[2] / 2, rect[1] + rect[3] / 2
            along_x = (x1 - x0) > (z1 - z0)
            run = (x1 - x0) if along_x else (z1 - z0)
            if run < 2.5:
                continue
            if along_x:
                nz = 1 if cz > mz else -1
                fz = z1 if nz > 0 else z0
                pos = lambda u: (x0 + u, fz)
                ry = face(0, nz)
                probe = lambda u, y: (x0 + u, y, fz + nz * .25)
            else:
                nx = 1 if cx > mx else -1
                fx = x1 if nx > 0 else x0
                pos = lambda u: (fx, z0 + u)
                ry = face(nx, 0)
                probe = lambda u, y: (fx + nx * .25, y, z0 + u)
            if self.occupied(probe(run / 2, y0 + 1.5)):
                continue
            if rng.random() < .45:
                u = .35 if rng.random() < .5 else run - .35
                for k in range(int((y1 - y0) // 3) + 1):
                    if y0 + k * 3 + 2.7 <= y1 + .05 and not self.occupied(probe(u, y0 + k * 3 + 1.4)):
                        px, pz = pos(u)
                        items.append(dict(asset='DOWNPIPE_3M', x=px, y=y0 + k * 3, z=pz, ry=ry))
            if y0 >= 2.9 and rng.random() < .22:
                px, pz = pos(rng.uniform(.6, run - .6))
                items.append(dict(asset='SATELLITE_DISH', x=px, y=y0 + rng.uniform(1.9, 2.3), z=pz, ry=ry))
            if y0 < .1 and rng.random() < .6:
                for k in range(2):
                    px, pz = pos(rng.uniform(.5, run - .5))
                    items.append(dict(asset='AIRBRICK', x=px, y=.22, z=pz, ry=ry))
            if rng.random() < .25:
                px, pz = pos(rng.uniform(.5, run - .5))
                items.append(dict(asset='VENT_GRILLE', x=px, y=y0 + 2.3, z=pz, ry=ry))
        # Ground-floor flats: security grilles on some windows and a boarded void now and then
        # (South London kit, origin at the bottom of the back face).
        voids = set()
        for w in self.windows:
            if w['y'] > 3 or w['w'] < 1:
                continue
            sill = w['y'] - w['h'] / 2
            block = ('N' if w['z'] < 60 else 'S') + ('W' if w['x'] < 72 else 'E')
            r = rng.random()
            if block not in voids and not w['lit'] and r < .12:
                voids.add(block)
                items.append(dict(asset='hr_prop_void_sheet_window_1200', x=w['x'], y=sill - .02, z=w['z'], ry=face(w['nx'], w['nz'])))
            elif r < .3:
                asset = 'hr_prop_window_grille_1200' if rng.random() < .65 else 'hr_prop_window_grille_1200_black'
                items.append(dict(asset=asset, x=w['x'], y=sill + .08, z=w['z'], ry=face(w['nx'], w['nz'])))
        self.facade_items = items

    def boundary(self):
        """Dwarf brick wall with piers and railings along the site edge (collision is the 3 m box)."""
        for b in self.L['boxes']:
            if b['id'] != 'boundary':
                continue
            x0, x1, z0, z1 = b['x0'], b['x1'], b['z0'], b['z1']
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            grp = self.g('boundary', cx, cz)
            self.B.box(grp, 'hr_brick_stock', x0, x1, 0, .9, z0, z1, faces='+x -x +z -z', col=self.grime(0, top=.9, strength=.55))
            self.B.box(grp, 'hr_concrete_cast', x0 - .04, x1 + .04, .9, .98, z0 - .04, z1 + .04)
            along_x = (x1 - x0) > (z1 - z0)
            L = (x1 - x0) if along_x else (z1 - z0)
            mid = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
            n = int(L / .13)
            P = (lambda a, y: (a, y, mid)) if along_x else (lambda a, y: (mid, y, a))
            a0 = x0 if along_x else z0
            for k in range(n):
                a = a0 + (k + .5) * L / n
                self.B.cylinder(grp, 'hr_steel_black', P(a, .98), P(a, 2.3), .011, seg=4, caps=False)
            for yy in (1.1, 2.2):
                self.B.cylinder(grp, 'hr_steel_black', P(a0, yy), P(a0 + L, yy), .02, seg=6)
            for k in range(int(L / 6) + 1):
                a = a0 + k * L / max(1, int(L / 6))
                if along_x:
                    self.B.box(grp, 'hr_brick_stock', a - .25, a + .25, 0, 1.3, z0 - .05, z1 + .05)
                    self.B.box(grp, 'hr_concrete_cast', a - .29, a + .29, 1.3, 1.38, z0 - .09, z1 + .09)
                else:
                    self.B.box(grp, 'hr_brick_stock', x0 - .05, x1 + .05, 0, 1.3, a - .25, a + .25)
                    self.B.box(grp, 'hr_concrete_cast', x0 - .09, x1 + .09, 1.3, 1.38, a - .29, a + .29)

    def build_all(self):
        self.walls()
        self.openings()
        self.slabs()
        self.guards()
        self.stairs()
        self.columns()
        self.roofs()
        self.ground()
        self.undercroft()
        self.interiors()
        self.boundary()
        self.cores_extra()
        self.facade_dressing()
