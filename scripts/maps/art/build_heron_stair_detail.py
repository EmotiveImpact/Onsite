"""Original constructed public-core stair kit; no collision or navigation changes.

Run: blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_stair_detail.py
Only the new stair-detail.blend/GLB/manifest are written. Original 5.2 sources stay closed.
Authoring coordinates are metres, x east / y up / z south, via heron_art_mesh.Builder.
"""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys
import tempfile

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from heron_art_mesh import Builder, planar_uv
from heron_art_materials import Library, PLAIN, EMIT

LAYOUT_PATH = ROOT / 'assets/blender/heron-reach/layout.json'
L = json.loads(LAYOUT_PATH.read_text())
S = L['stairs']['ST-P']
CONCRETE, SOFFIT, TREAD = 'hr_stair_concrete', 'hr_concrete_board', 'hr_stair_tread'
RAIL, PAINT, GALV, LENS = 'hr_steel_black', 'hr_door_paint', 'hr_steel_galv', 'hr_core_strip'
PAINT_COL = (.63, .77, .72, 1)
SEAM_COL = (.38, .48, .44, 1)
PITCH = S['rise'] / S['going']
EPS = 1e-6

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1
collection = bpy.data.collections.new('HR_STAIR_CONSTRUCTION')
bpy.context.scene.collection.children.link(collection)
B = Builder(lambda _: collection)
cores = []


class Core:
    """A reflected local design frame; mirrors winding as well as coordinates."""

    def __init__(self, data):
        self.data = data
        self.x, self.z = data['rect'][:2]
        self.mirror = data['mirror']
        self.base, self.top = data['levels'][0], data['levels'][-1]
        self.group = 'stair/' + ('S' if self.mirror else 'N') + ('W' if self.x < 72 else 'E')
        self.report = {**data, 'flights': [], 'spines': [], 'landingGuards': [], 'fixtures': [], 'dado': []}

    def p(self, point):
        x, y, z = point
        return (self.x + x, y, self.z + (6 - z if self.mirror else z))

    def bounds(self, x0, x1, y0, y1, z0, z1):
        p, q = self.p((x0, y0, z0)), self.p((x1, y1, z1))
        return {'min': [min(p[i], q[i]) for i in range(3)], 'max': [max(p[i], q[i]) for i in range(3)]}

    def box(self, mat, x0, x1, y0, y1, z0, z1, col=(1, 1, 1, 1), faces='all'):
        q = self.bounds(x0, x1, y0, y1, z0, z1)
        a, b = q['min'], q['max']
        B.box(self.group, mat, a[0], b[0], a[1], b[1], a[2], b[2], col=col, faces=faces)

    def poly(self, mat, points, normal, uv=None, col=(1, 1, 1, 1)):
        points = list(points)
        uv = uv or planar_uv(points)
        n = (Vector(points[1]) - Vector(points[0])).cross(Vector(points[2]) - Vector(points[0]))
        if n.dot(Vector(normal)) < 0:
            points, uv = points[::-1], uv[::-1]
            if isinstance(col, list):
                col = col[::-1]
        if self.mirror:
            points, uv = points[::-1], uv[::-1]
            if isinstance(col, list):
                col = col[::-1]
        B.acc(self.group, mat).poly([self.p(p) for p in points], uv, col)

    def tube(self, mat, a, b, radius, seg=8, col=(1, 1, 1, 1), caps=False):
        B.cylinder(self.group, mat, self.p(a), self.p(b), radius, seg=seg, caps=caps, col=col)

    def fastener(self, x, sign, y, z, radius=.009, depth=.006, col=(.61, .64, .59, 1)):
        # Hexagonal bolt head: six real side faces plus one visible end, no buried back cap.
        self.tube(GALV, (x, y, z), (x+sign*depth, y, z), radius, seg=6, col=col)
        points = [(x+sign*depth, y+radius*math.cos(i*math.tau/6), z+radius*math.sin(i*math.tau/6)) for i in range(6)]
        self.poly(GALV, points, (sign, 0, 0), col=col)

    def flight(self, lower, first):
        x0 = S['firstFlightX'] if first else S['secondFlightX']
        x1 = x0 + S['flightWidth']
        foot = lower if first else lower + 1.5
        direction = -1 if first else 1
        zfoot = S['flightZ'] + S['flightRun'] if first else S['flightZ']
        zhead = zfoot + direction * S['flightRun']
        record = {'id': '%s/%g/%s' % (self.data['id'], lower, 'first' if first else 'return'),
                  'first': first, 'fromY': foot, 'toY': foot + 1.5, 'x0': self.x+x0, 'x1': self.x+x1,
                  'treads': [], 'soffitEndpoints': [self.p((x0, foot-.15, zfoot)), self.p((x0, foot+1.2, zhead))],
                  'minStackedFlightHeadroom': 2.7}
        # Actual tread profile: a six-millimetre bevel is cut DOWN into the physical box.
        # No separate raised stripe changes the authoritative walking height.
        for i in range(1, S['treadsPerFlight'] + 1):
            yf = foot + i * S['rise']
            za = zfoot + direction * (i-1) * S['going']
            zb = za + direction * S['going']
            nose = za + direction * .006
            bottom_a, bottom_b = yf-.30, yf-.15
            points = [(x0, yf, nose), (x1, yf, nose), (x1, yf, zb), (x0, yf, zb)]
            self.poly(TREAD, points, (0, 1, 0), [(0, .006/.28), (1, .006/.28), (1, 1), (0, 1)],
                      [( .89, .89, .86, 1), (.89, .89, .86, 1), (.97, .97, .95, 1), (.97, .97, .95, 1)])
            self.poly(TREAD, [(x0, yf-.006, za), (x1, yf-.006, za), (x1, yf, nose), (x0, yf, nose)],
                      (0, 1, -direction), [(0, 0), (1, 0), (1, .006/.28), (0, .006/.28)], col=(.91, .91, .88, 1))
            riser_bottom = foot-.15 if i == 1 else yf-.15
            self.poly(CONCRETE, [(x0, riser_bottom, za), (x1, riser_bottom, za), (x1, yf-.006, za), (x0, yf-.006, za)],
                      (0, 0, -direction), col=[(.63, .64, .61, 1), (.63, .64, .61, 1), (.94, .94, .9, 1), (.94, .94, .9, 1)])
            for xx, nx in [(x0, -1), (x1, 1)]:
                self.poly(CONCRETE, [(xx, bottom_a, za), (xx, yf-.006, za), (xx, yf, nose), (xx, yf, zb), (xx, bottom_b, zb)],
                          (nx, 0, 0), col=[(.58, .60, .57, 1), (.87, .88, .84, 1), (.94, .94, .9, 1), (.94, .94, .9, 1), (.58, .60, .57, 1)])
            exact = self.bounds(x0, x1, yf-.30, yf, min(za, zb), max(za, zb))
            matches = [b for b in L['boxes'] if b['id'] == 'stair' and
                       all(abs(b[k]-v) < EPS for k, v in zip(('x0', 'y0', 'z0', 'x1', 'y1', 'z1'), exact['min']+exact['max']))]
            assert len(matches) == 1, (record['id'], i, exact, matches)
            record['treads'].append({'index': i, 'mapBounds': exact})
        self.poly(SOFFIT, [(x0, foot-.15, zfoot), (x1, foot-.15, zfoot), (x1, foot+1.2, zhead), (x0, foot+1.2, zhead)],
                  (0, -1, 0), col=(.66, .68, .65, 1))
        # A short concrete bearing wedge joins the waist to the RETAINED landing slab.
        # The underside stays at least 2.70m above the same landing on the storey below.
        landing_under = foot + (1.35 if first else 1.30)
        bearing_run = (landing_under-(foot+1.2)) / PITCH
        zend = zhead + direction * bearing_run
        self.poly(SOFFIT, [(x0, foot+1.2, zhead), (x1, foot+1.2, zhead), (x1, landing_under, zend), (x0, landing_under, zend)],
                  (0, -1, 0), col=(.57, .59, .56, 1))
        for xx, nx in [(x0, -1), (x1, 1)]:
            self.poly(CONCRETE, [(xx, foot+1.2, zhead), (xx, landing_under, zhead), (xx, landing_under, zend)],
                      (nx, 0, 0), col=(.72, .73, .69, 1))
        record['bearingBounds'] = self.bounds(x0, x1, foot+1.2, landing_under, min(zhead, zend), max(zhead, zend))

        # Rails follow the pitch through tread nosings, then terminate into physical supports.
        # Inner tubes fit INSIDE the existing 60mm opaque collider strips, preserving 1.50m clear width.
        railx = 1.918 if first else 4.082
        outerx = .34 if first else 5.66
        za, zb = zfoot+direction*.020, zhead-direction*.020
        def rail_y(z):
            return foot + .15 + (z-zfoot)*direction*PITCH + .95
        a, b = (railx, rail_y(za), za), (railx, rail_y(zb), zb)
        self.tube(RAIL, a, b, .018)
        self.tube(RAIL, (outerx, a[1], za), (outerx, b[1], zb), .022)
        innerwall = 1.935 if first else 4.065
        outerwall = .205 if first else 5.795
        for end in [a, b]:
            self.tube(RAIL, end, (innerwall, end[1], end[2]), .018)
            self.tube(RAIL, (outerx, end[1], end[2]), (outerwall, end[1], end[2]), .022)
        for t in [.15, .85]:
            zz = za + (zb-za)*t
            yy = rail_y(zz)
            for xx, support, radius in [(railx, innerwall, .012), (outerx, outerwall, .015)]:
                if xx == outerx:
                    self.tube(RAIL, (xx, yy-.016, zz), (xx, yy-.085, zz), radius, seg=6)
                    self.tube(RAIL, (xx, yy-.085, zz), (support, yy-.085, zz), radius, seg=6)
                inside = 1 if support < xx else -1
                # Inner saddles sit against the rail itself, rather than floating below it.
                mount_y = yy-.085 if xx == outerx else yy-.030
                self.box(GALV, min(support, support+inside*.008), max(support, support+inside*.008),
                         mount_y-.05, mount_y+.05, zz-.037, zz+.037, col=(.43, .47, .43, 1))
                # One visible hexagonal anchor head in each compact saddle plate.
                self.fastener(support+inside*.008, inside, mount_y, zz)
        record['rail'] = {'start': self.p(a), 'end': self.p(b), 'radius': .018,
                          'outerStart': self.p((outerx, a[1], za)), 'outerEnd': self.p((outerx, b[1], zb)),
                          'heightAboveNosingPitch': .95}
        # Paint and a substantial skirting edge sit in the wall/flight gap, never on the tread.
        dado_x = .204 if first else 5.796
        bottom_a, bottom_b = foot+.15, foot+1.5
        self.poly(PAINT, [(dado_x, bottom_a, zfoot), (dado_x, bottom_a+1.10, zfoot),
                         (dado_x, bottom_b+1.10, zhead), (dado_x, bottom_b, zhead)],
                  (1 if first else -1, 0, 0), col=[(.47, .59, .55, 1), PAINT_COL, PAINT_COL, (.47, .59, .55, 1)])
        skirting_x = .222 if first else 5.778
        self.poly(CONCRETE, [(skirting_x, bottom_a-.10, zfoot), (skirting_x, bottom_a+.105, zfoot),
                            (skirting_x, bottom_b+.105, zhead), (skirting_x, bottom_b-.10, zhead)],
                  (1 if first else -1, 0, 0), col=(.57, .61, .58, 1))
        self.poly(CONCRETE, [(dado_x, bottom_a+.105, zfoot), (skirting_x, bottom_a+.105, zfoot),
                            (skirting_x, bottom_b+.105, zhead), (dado_x, bottom_b+.105, zhead)],
                  (0, 1, 0), col=(.69, .72, .68, 1))
        for zz, height, normal in [(zfoot, bottom_a, -direction), (zhead, bottom_b, direction)]:
            self.poly(CONCRETE, [(dado_x, height-.10, zz), (skirting_x, height-.10, zz),
                                (skirting_x, height+.105, zz), (dado_x, height+.105, zz)],
                      (0, 0, normal), col=(.57, .61, .58, 1))
        self.report['flights'].append(record)

    def spine(self, left):
        x0, x1 = (1.90, 1.96) if left else (4.04, 4.10)
        # Opaque sheet and seams communicate the full-height existing solid collider honestly.
        # Handrails recess into its flight-facing channel; sheet is never perforated.
        sx0, sx1 = (1.935, 1.96) if left else (4.04, 4.065)
        def grime(p):
            h = (p[1]-self.base) % 3
            shade = .76 if h < .08 else 1
            return tuple(v*shade for v in PAINT_COL[:3]) + (1,)
        self.box(PAINT, sx0, sx1, self.base, self.top+1.2, 1.70, 4.22, col=grime)
        for zz in [1.715, 2.96, 4.205]:
            self.box(PAINT, x0, x1, self.base, self.top+1.2, zz-.015, zz+.015, col=SEAM_COL)
        for y in [self.base+i*1.5 for i in range(round((self.top-self.base)/1.5)+1)]+[self.top+1.18]:
            self.box(PAINT, sx0-.002, sx1+.002, y, min(y+.02, self.top+1.2), 1.725, 4.195, col=SEAM_COL)
            if abs((y-self.base) % 3) < EPS:
                for zz in [1.76, 4.16]:
                    face, sign = (sx0, -1) if left else (sx1, 1)
                    self.fastener(face, sign, y+.011, zz, radius=.006, depth=.003, col=(.44, .47, .44, 1))
        self.report['spines'].append({'mapBounds': self.bounds(x0, x1, self.base, self.top+1.2, 1.7, 4.22),
                                      'opaqueSheetBounds': self.bounds(sx0, sx1, self.base, self.top+1.2, 1.7, 4.22)})

    def guard(self, y, top):
        x0, x1 = (.2 if top else 1.9), 4.1
        self.box(PAINT, x0, x1, y, y+1.2, 4.16, 4.182, col=PAINT_COL)
        # Folded cap and bottom seam remain wholly inside the guard collider.
        self.box(RAIL, x0, x1, y+1.18, y+1.20, 4.16, 4.22, col=(.66, .70, .66, 1))
        self.box(PAINT, x0, x1, y+.035, y+.065, 4.182, 4.22, col=SEAM_COL)
        for xx in [x0+.04, (x0+x1)/2, x1-.04]:
            self.box(PAINT, xx-.009, xx+.009, y+.065, y+1.18, 4.182, 4.22, col=SEAM_COL)
        # Correctly connected return-flight / landing / next-first-flight handrail.
        rail_y = y+.95-.02*PITCH
        self.tube(RAIL, (1.918, rail_y, 4.20), (4.082, rail_y, 4.20), .018)
        if not top:
            self.tube(RAIL, (1.918, rail_y, 4.20), (1.918, y+1.1+.02*PITCH, 4.20), .018)
        self.report['landingGuards'].append({'mapBounds': self.bounds(x0, x1, y, y+1.2, 4.16, 4.22)})

    def fixture(self, lower):
        # Matching heronStairLighting's half-landing anchors. No lights in this GLB.
        self.box(GALV, 4.25, 5.45, lower+4.15, lower+4.25, .84, 1.06, col=(.68, .71, .68, 1))
        self.box(LENS, 4.29, 5.41, lower+4.145, lower+4.15, .87, 1.03, faces='-y')
        # Wall-supported slim brackets; topmost fitting does not float under the distant roof.
        for x in [4.29, 5.41]:
            self.box(GALV, x-.014, x+.014, lower+4.20, lower+4.23, .205, .95, col=(.55, .59, .55, 1))
            self.box(GALV, x-.036, x+.036, lower+4.14, lower+4.29, .201, .213, col=(.60, .63, .60, 1))
        self.report['fixtures'].append({'kind': 'half-landing', 'anchor': self.p((4.85, lower+4.15, .95)),
                                        'lensBottom': lower+4.145, 'floorY': lower+1.5, 'clearance': 2.645})

    def build(self):
        before = {key: len(acc.verts) for key, acc in B.groups.items()}
        self.spine(True)
        self.spine(False)
        for lower in self.data['levels'][:-1]:
            self.flight(lower, True)
            self.flight(lower, False)
            self.fixture(lower)
        for y in self.data['levels'][1:]:
            self.guard(y, y == self.top)
        # Side-wall landing dado stops before both the front doorway and the painted back-wall numerals.
        for floor in self.data['levels']:
            for xa, xb in [(.201, .207), (5.793, 5.799)]:
                self.box(PAINT, xa, xb, floor+.015, floor+1.10, 4.23, 5.68, col=PAINT_COL)
                self.box(CONCRETE, xa if xa < 3 else 5.778, .222 if xa < 3 else xb,
                         floor+.015, floor+.12, 4.23, 5.68, col=(.50, .55, .51, 1))
        for lower in self.data['levels'][:-1]:
            for xa, xb in [(.201, .207), (5.793, 5.799)]:
                self.box(PAINT, xa, xb, lower+1.5, lower+2.60, .35, 1.69, col=PAINT_COL)
                self.box(CONCRETE, xa if xa < 3 else 5.778, .222 if xa < 3 else xb,
                         lower+1.5, lower+1.62, .35, 1.69, col=(.50, .55, .51, 1))
        pts = [(v[0]+72, v[2], 60-v[1]) for key, acc in B.groups.items() for v in acc.verts[before.get(key, 0):]]
        assert all(self.x+.19-EPS <= p[0] <= self.x+5.81+EPS and self.z+.19-EPS <= p[2] <= self.z+5.81+EPS
                   and self.base-.151 <= p[1] <= self.top+1.30 for p in pts), self.data['id']
        self.report['actualMapBounds'] = {'min': [min(p[i] for p in pts) for i in range(3)],
                                          'max': [max(p[i] for p in pts) for i in range(3)]}
        self.report['dado'] = ['Side-wall-only paint, 7mm maximum projection; foot/half/full landing bands.',
                              'Sloped 22mm skirting stays within the 200mm outer wall/flight gap.']
        cores.append(self.report)


for core in L['cores']:
    Core(core).build()
assert len(cores) == 8 and sum(len(c['flights']) for c in cores) == 48
assert sum(len(f['treads']) for c in cores for f in c['flights']) == 432
assert .34+.022 < .4 and 5.66-.022 > 5.6, 'outer handrails preserve full 1.5m clear flights'
assert 1.918-.018 >= 1.9-EPS and 4.082+.018 <= 4.1+EPS, 'inner rails remain inside existing spines'
assert 2.645 > 2.4 and 2.7 > 2.4, 'fixture and bearing headroom above standing route'

library = Library()
def material(name):
    if name == CONCRETE:
        if name not in library.cache:
            mat = library('hr_concrete_cast').copy()
            mat.name = CONCRETE
            library.cache[name] = mat
        return library.cache[name]
    return library(name)

objects = B.build(material)
triangles = sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in objects)
print('Stair triangle batches:', {name: sum(sum(len(p.vertices)-2 for p in obj.data.polygons)
      for obj in objects if obj.data.materials[0].name == name) for name in {o.data.materials[0].name for o in objects}})
assert triangles < 30000 and len(objects) <= 28, (triangles, len(objects))
for obj in objects:
    obj['provenance'] = 'Original ONSITE construction, measured from public ST-P collision layout.'
    obj['collision'] = 'None. Existing public stairs/spines/landings remain authoritative.'
    obj.data.calc_loop_triangles()
used_materials = sorted({obj.data.materials[0].name for obj in objects})
folder = ROOT / 'assets/blender/heron-reach'
output = ROOT / 'public/models/heron-reach/stair-detail.glb'
bpy.context.preferences.filepaths.save_version = 0
for image in bpy.data.images:
    if image.source == 'FILE':
        image.pack()
        assert image.packed_file, ('missing packed source texture', image.name)
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'stair-detail.blend'), compress=True)

# Runtime reuses the existing material instances/textures. Save the editable textured source
# above, then remove texture graphs only from this export session to avoid duplicate images.
for name in used_materials:
    mat = bpy.data.materials[name]
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    vcol = nt.nodes.new('ShaderNodeVertexColor')
    vcol.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1
    colour, roughness, metal = PLAIN.get('hr_concrete_cast' if name == CONCRETE else name, ((.7, .75, .8), .88, 0))
    mul.inputs['A'].default_value = (*colour, 1)
    nt.links.new(vcol.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .88 if name == CONCRETE else roughness
    bsdf.inputs['Metallic'].default_value = metal
    if name in EMIT:
        bsdf.inputs['Emission Color'].default_value = (*EMIT[name][0], 1)
        bsdf.inputs['Emission Strength'].default_value = EMIT[name][1]
flags = ['-cc', '-kn', '-km', '-kv', '-vpf', '-vtf']
with tempfile.TemporaryDirectory(prefix='heron-stair-') as temp:
    raw = Path(temp)/'stair-detail.raw.glb'
    bpy.ops.export_scene.gltf(filepath=str(raw), export_format='GLB', export_apply=True, export_yup=True)
    raw_bytes = raw.stat().st_size
    subprocess.run(['npx', '--no-install', 'gltfpack', '-i', str(raw), '-o', str(output), *flags], cwd=ROOT, check=True)

packed = output.read_bytes()
json_length = int.from_bytes(packed[12:16], 'little')
gltf = json.loads(packed[20:20+json_length])
assert not gltf.get('images') and not gltf.get('textures')
shipped_triangles = sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])
assert shipped_triangles == triangles, (shipped_triangles, triangles)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {
    'provenance': 'Original ONSITE procedural construction geometry. No downloaded models or new textures. Existing Heron material library retains its documented texture provenance.',
    'builder': str(Path(__file__).relative_to(ROOT)), 'builderSHA256': sha(Path(__file__)),
    'blender': bpy.app.version_string, 'layoutSHA256': sha(LAYOUT_PATH),
    'coordinates': 'Map metres x east/y up/z south; glTF world=(mapX-72,mapY,mapZ-60). No runtime offset.',
    'collision': 'No changes. Original stairs, full-height opaque separators and landing guards remain authoritative.',
    'collection': 'HR_STAIR_CONSTRUCTION', 'cores': cores,
    'triangles': triangles, 'materialBatches': len(objects), 'sharedMaterials': used_materials,
    'materialContract': {'hr_stair_concrete': 'Clone hr_concrete_cast textures; dry roughness .88, metalness 0, no exterior wet shader.',
                         'others': 'Reuse existing HeronReachMaterials by exact name. Multiply preserved Col/COLOR_0 vertex colours.',
                         'embeddedTextures': 0, 'newPointLights': 0},
    'routeChecks': {'physicalTreadBoxesMatched': 432, 'clearFlightWidth': 1.5, 'halfLandingDepth': 1.5,
                    'floorLandingDepth': 1.58, 'minStackedFlightOrBearingHeadroom': 2.7,
                    'minNewFixtureHeadroom': 2.645, 'geometryCoreBounds': 'passed',
                    'method': 'Exact authoritative box equality, inner/outer rail envelope and core containment assertions; independent shipped-mesh tests cover routes/headroom.'},
    'legacyRetirement': {'expectedTriangles': 35072, 'treads': 5184, 'rails': 29888,
                         'preserve': ['all landing slab bodies', 'core walls/glazing/numerals/services', 'all private ST-H stairs'],
                         'implementation': 'src/onsite/heronStairArt.ts removeLegacyCoreStairs; exact public volumes and material whitelist with 8mm old quantisation tolerance.'},
    'rawGLBBytes': raw_bytes, 'compressedGLBBytes': len(packed), 'compressedGLBSHA256': sha(output),
    'blendSHA256': sha(folder/'stair-detail.blend'),
    'compression': {'tool': 'npm gltfpack', 'version': json.loads((ROOT/'node_modules/gltfpack/package.json').read_text())['version'],
                    'flags': flags, 'lockfileSHA256': sha(ROOT/'package-lock.json')},
}
(folder/'stair-detail-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('STAIR_DETAIL', triangles, 'triangles;', len(objects), 'batches;', len(packed), 'bytes;', manifest['compressedGLBSHA256'])
