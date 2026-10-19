"""The world beyond the Heron Reach boundary: render-only streets, terraces and the tower skyline.

Nothing here can be reached. It gives the frame the concept art's depth: a street with parked cars
around the estate wall, three- and four-storey terraces and walk-up blocks across the road, and
council towers with lit windows at 70 to 260 m. Windows are flat cards (lit or dark) with frames,
so the skyline reads at blue hour without any texture; the tower facade texture refines it later.
"""
import math
import random


ROAD_IN, ROAD_W, PAVE = 0.0, 9.0, 3.2  # pavement against the wall, then the road, then the far pavement


class Context:
    def __init__(self, L, builder, seed=1966):
        self.L = L
        self.B = builder
        self.rng = random.Random(seed)
        x, z, w, d = L['site']
        self.site = (x, z, w, d)

    # --- streets ring -------------------------------------------------------------------------
    def streets(self):
        x, z, w, d = self.site
        g = 'OUT/street'
        e = .3  # boundary wall thickness
        P0, R0, R1, P1 = e, e + PAVE, e + PAVE + ROAD_W, e + PAVE + ROAD_W + PAVE
        far = 420
        def ring(a, b, mat, y=0.0, kerb=False):
            # four strips around the site from offset a to b outside the wall
            self.B.box(g, mat, x - b, x + w + b, y - .2, y, z - b, z - a, faces='+y')
            self.B.box(g, mat, x - b, x + w + b, y - .2, y, z + d + a, z + d + b, faces='+y')
            self.B.box(g, mat, x - b, x - a, y - .2, y, z - a, z + d + a, faces='+y')
            self.B.box(g, mat, x + w + a, x + w + b, y - .2, y, z - a, z + d + a, faces='+y')
        ring(P0, R0, 'hr_paving', .12)
        ring(R0, R1, 'hr_asphalt', 0)
        ring(R1, P1, 'hr_paving', .12)
        # kerb faces
        for off in (R0, R1):
            self.B.box(g, 'hr_concrete_cast', x - off, x + w + off, 0, .12, z - off - .01, z - off + .01, faces='+z -z')
            self.B.box(g, 'hr_concrete_cast', x - off, x + w + off, 0, .12, z + d + off - .01, z + d + off + .01, faces='+z -z')
            self.B.box(g, 'hr_concrete_cast', x - off - .01, x - off + .01, 0, .12, z - off, z + d + off, faces='+x -x')
            self.B.box(g, 'hr_concrete_cast', x + w + off - .01, x + w + off + .01, 0, .12, z - off, z + d + off, faces='+x -x')
        # centre line dashes and the yellow lines along the estate kerb
        mid = (R0 + R1) / 2
        for k in range(int((w + 2 * R1) / 6)):
            a = x - R1 + k * 6
            for zz in (z - mid, z + d + mid):
                self.B.box(g, 'hr_paint_white', a, a + 3, .004, .006, zz - .06, zz + .06, faces='+y')
        for k in range(int((d + 2 * R1) / 6)):
            a = z - R1 + k * 6
            for xx in (x - mid, x + w + mid):
                self.B.box(g, 'hr_paint_white', xx - .06, xx + .06, .004, .006, a, a + 3, faces='+y')
        for (x0, x1, z0, z1) in [(x - R0, x + w + R0, z - R0 - .35, z - R0 - .25), (x - R0, x + w + R0, z + d + R0 + .25, z + d + R0 + .35)]:
            self.B.box(g, 'hr_paint_yellow', x0, x1, .004, .006, z0, z1, faces='+y')
        # distant ground out to the fog
        for (x0, x1, z0, z1) in [(x - far, x + w + far, z - far, z - P1), (x - far, x + w + far, z + d + P1, z + d + far),
                                 (x - far, x - P1, z - P1, z + d + P1), (x + w + P1, x + w + far, z - P1, z + d + P1)]:
            self.B.box('OUT/far', 'hr_asphalt', x0, x1, -.25, .1, z0, z1, faces='+y')
        self.front = P1

    # --- buildings ----------------------------------------------------------------------------
    def facade_cards(self, grp, x0, z0, x1, z1, y0, y1, n_out, storey=2.9, pitch=2.6, ww=1.1, wh=1.4, lit=.45, frame='hr_upvc_white'):
        """Window cards on a flat facade from (x0,z0) to (x1,z1), outward normal n_out = (nx, nz)."""
        nx, nz = n_out
        length = math.hypot(x1 - x0, z1 - z0)
        ux, uz = (x1 - x0) / length, (z1 - z0) / length
        cols = max(1, int((length - .8) / pitch))
        rows = max(1, int((y1 - y0 - .4) / storey))
        rng = self.rng
        for r in range(rows):
            vy = y0 + r * storey + .9
            if vy + wh > y1 - .2:
                break
            for c in range(cols):
                u = (c + .5) * length / cols
                cx, cz = x0 + ux * u + nx * .12, z0 + uz * u + nz * .12
                is_lit = rng.random() < lit
                mat = 'hr_window_interior' if is_lit else 'hr_window_dark'
                hw = ww / 2
                p = [(cx - ux * hw, vy, cz - uz * hw), (cx + ux * hw, vy, cz + uz * hw), (cx + ux * hw, vy + wh, cz + uz * hw), (cx - ux * hw, vy + wh, cz - uz * hw)]
                if (p[1][0] - p[0][0]) * nz - (p[1][2] - p[0][2]) * nx < 0:
                    p = [p[1], p[0], p[3], p[2]]
                self.B.quad(grp, mat, *p)
                acc = self.B.acc(grp, mat)
                cell = rng.randrange(32) if is_lit else rng.choice([4, 12, 20, 28])
                cu, cv = cell % 8, cell // 8
                acc.uvs[-1] = [(cu / 8, 1 - (cv + 1) / 4), ((cu + 1) / 8, 1 - (cv + 1) / 4), ((cu + 1) / 8, 1 - cv / 4), (cu / 8, 1 - cv / 4)]

    def block(self, grp, x0, z0, x1, z1, h, mat, roof='hr_roof_felt', lit=.45, storey=2.9, parapet=.6, windows=True):
        self.B.box(grp, mat, x0, x1, 0, h, z0, z1, faces='+x -x +z -z', col=self.grime())
        self.B.box(grp, roof, x0, x1, h - .01, h, z0, z1, faces='+y')
        self.B.box(grp, 'hr_concrete_cast', x0 - .05, x1 + .05, h, h + parapet * .3, z0 - .05, z1 + .05)
        if windows:
            self.facade_cards(grp, x0, z1, x1, z1, 0, h, (0, 1), storey=storey, lit=lit)
            self.facade_cards(grp, x1, z0, x0, z0, 0, h, (0, -1), storey=storey, lit=lit)
            self.facade_cards(grp, x0, z0, x0, z1, 0, h, (-1, 0), storey=storey, lit=lit)
            self.facade_cards(grp, x1, z1, x1, z0, 0, h, (1, 0), storey=storey, lit=lit)

    def grime(self):
        def f(p):
            k = 1 - .3 * math.exp(-p[1] / .6)
            return (k, k, k * .98, 1)
        return f

    def terraces(self):
        """Low frontage across the road: terraces, walk-up blocks and a parade of shops."""
        x, z, w, d = self.site
        rng = self.rng
        f = self.front + 1.5
        sides = [('N', (x - 30, x + w + 30), z - f, -1), ('S', (x - 30, x + w + 30), z + d + f, 1)]
        for name, (a0, a1), edge, n in sides:
            a = a0
            while a < a1:
                L = rng.choice([24, 30, 36, 18])
                h = rng.choice([8.7, 11.6, 11.6, 14.5])
                deep = rng.uniform(10, 14)
                mat = rng.choice(['hr_brick_stock', 'hr_brick_stock', 'hr_brick_red', 'hr_render'])
                z0, z1 = (edge - deep, edge) if n < 0 else (edge, edge + deep)
                self.block('OUT/terraces', a, z0, a + L, z1, h, mat, lit=.4)
                a += L + rng.choice([0, 0, 4, 8])
        sides = [('W', (z - 30, z + d + 30), x - f, -1), ('E', (z - 30, z + d + 30), x + w + f, 1)]
        for name, (a0, a1), edge, n in sides:
            a = a0
            while a < a1:
                L = rng.choice([24, 30, 18])
                h = rng.choice([8.7, 11.6, 14.5])
                deep = rng.uniform(10, 14)
                mat = rng.choice(['hr_brick_stock', 'hr_brick_red', 'hr_render'])
                x0, x1 = (edge - deep, edge) if n < 0 else (edge, edge + deep)
                self.block('OUT/terraces', x0, a, x1, a + L, h, mat, lit=.4)
                a += L + rng.choice([0, 4, 8])

    def towers(self):
        """Council towers ringing the estate at a distance: the skyline in every concept frame."""
        x, z, w, d = self.site
        cx, cz = x + w / 2, z + d / 2
        rng = self.rng
        placed = []
        for i in range(26):
            for _ in range(40):
                ang = rng.uniform(0, math.tau)
                r = rng.uniform(150, 300)
                tx, tz = cx + math.cos(ang) * r * 1.0, cz + math.sin(ang) * r * .9
                if all(math.hypot(tx - px, tz - pz) > 34 for px, pz in placed):
                    break
            placed.append((tx, tz))
            storeys = rng.choice([14, 18, 20, 22, 24, 26])
            h = storeys * 2.75
            fw, fd = rng.choice([(18, 18), (22, 16), (30, 14), (16, 16)])
            ry = rng.random() < .5
            if ry:
                fw, fd = fd, fw
            mat = rng.choice(['hr_concrete_board', 'hr_concrete_cast', 'hr_brick_stock', 'hr_concrete_board'])
            self.block('OUT/towers', tx - fw / 2, tz - fd / 2, tx + fw / 2, tz + fd / 2, h, mat, lit=.38, storey=2.75, parapet=1.2)
            # lift motor room on top
            self.B.box('OUT/towers', mat, tx - 3, tx + 3, h, h + 3.2, tz - 2.5, tz + 2.5, col=self.grime())
        # a few walk-up slab blocks in the middle distance
        for i in range(10):
            ang = rng.uniform(0, math.tau)
            r = rng.uniform(95, 140)
            tx, tz = cx + math.cos(ang) * r, cz + math.sin(ang) * r * .85
            if abs(tx - cx) < w / 2 + 40 and abs(tz - cz) < d / 2 + 40:
                continue
            L, D, h = rng.choice([(48, 12, 14.5), (60, 12, 17.4), (36, 12, 11.6)])
            if rng.random() < .5:
                self.block('OUT/towers', tx - L / 2, tz - D / 2, tx + L / 2, tz + D / 2, h, rng.choice(['hr_brick_stock', 'hr_brick_red']), lit=.42)
            else:
                self.block('OUT/towers', tx - D / 2, tz - L / 2, tx + D / 2, tz + L / 2, h, rng.choice(['hr_brick_stock', 'hr_brick_red']), lit=.42)

    def build_all(self):
        self.streets()
        self.terraces()
        self.towers()
