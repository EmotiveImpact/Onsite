"""Original ONSITE building joints and private stair construction, Blender 4.3+.

blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_building_detail.py
Only additive building-detail files are written. No existing Blender source is opened.
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
from heron_art_arch import Arch

LAYOUT_PATH = ROOT/'assets/blender/heron-reach/layout.json'
L = json.loads(LAYOUT_PATH.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1
collection = bpy.data.collections.new('HR_BUILDING_CONSTRUCTION')
bpy.context.scene.collection.children.link(collection)
B = Builder(lambda _: collection)
report = {'features': [], 'protectedOpenings': []}
CAST, BLACK, GALV, PAINT, RUBBER = 'hr_concrete_cast', 'hr_steel_black', 'hr_steel_galv', 'hr_door_paint', 'hr_rubber'


"""Original ONSITE private maisonette stair construction fragment, 20 October 2026.

Authored from the existing ST-H collision contract. No imported model or image.
Call build_private_stairs(B, L, report) with the project's heron_art_mesh.Builder.
This module does not load Blender files, export assets, or change physical geometry.
"""


def build_private_stairs(B, L, report):
    import math

    S = L['stairs']['ST-H']
    pitch = S['rise'] / S['going']
    eps = 1e-6
    concrete = 'hr_stair_concrete'
    soffit = 'hr_concrete_board'
    tread_mat = 'hr_stair_tread'
    rail_mat = 'hr_steel_black'
    paint = 'hr_door_paint'
    galv = 'hr_steel_galv'
    paint_colour = (.35, .40, .36, 1)
    homes = [h for h in L['homes'] if h['module'] == 'H2-L']
    assert len(homes) == 8
    report.setdefault('privateStairs', [])
    report.setdefault('privateSheetRetirement', [])

    def subtract_rect(outer, hole):
        x, z, w, d = outer
        hx, hz, hw, hd = hole
        ax, bx = max(x, hx), min(x+w, hx+hw)
        az, bz = max(z, hz), min(z+d, hz+hd)
        if bx <= ax or bz <= az:
            return [list(outer)]
        parts = [[x, z, w, az-z], [x, bz, w, z+d-bz],
                 [x, az, ax-x, bz-az], [bx, az, x+w-bx, bz-az]]
        return [p for p in parts if p[2] > eps and p[3] > eps]

    for h in homes:
        hx, hz, base = h['x'], h['z'], h['y']
        mirrored = h['mirror']
        origin_x = hx + S['localOriginInHome'][0]
        origin_z = hz if mirrored else hz + S['localOriginInHome'][1]
        top = base + S['storey']
        quadrant = h['id'].split('-', 1)[0]
        group = 'building/' + quadrant
        home_id = h['id'].removesuffix('-L')
        before = {key: len(acc.verts) for key, acc in B.groups.items()}
        record = {'id': h['id'], 'homeId': home_id, 'quadrant': quadrant,
                  'home': {'x': hx, 'z': hz, 'y': base, 'mirror': mirrored},
                  'frame': {'x': origin_x, 'z': origin_z, 'depth': 6, 'mirror': mirrored},
                  'fromY': base, 'toY': top, 'flights': [],
                  'provenance': 'Original ONSITE procedural geometry around unchanged ST-H collision boxes.'}

        def point(p):
            x, y, z = p
            return (origin_x+x, y, origin_z+6-z if mirrored else origin_z+z)

        def bounds(x0, x1, y0, y1, z0, z1):
            a, b = point((x0, y0, z0)), point((x1, y1, z1))
            return {'min': [min(a[i], b[i]) for i in range(3)],
                    'max': [max(a[i], b[i]) for i in range(3)]}

        def poly(mat, points, normal, uv=None, col=(1, 1, 1, 1)):
            pts = [point(p) for p in points]
            target = (normal[0], normal[1], -normal[2] if mirrored else normal[2])
            a = [pts[1][i]-pts[0][i] for i in range(3)]
            b = [pts[2][i]-pts[0][i] for i in range(3)]
            cross = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
            if sum(cross[i]*target[i] for i in range(3)) < 0:
                pts.reverse()
                if uv is not None:
                    uv = list(reversed(uv))
                if isinstance(col, list):
                    col = list(reversed(col))
            if uv is None:
                axis = max(range(3), key=lambda i: abs(target[i]))
                if axis == 1:
                    uv = [(p[0], -p[2]) for p in pts]
                elif axis == 0:
                    uv = [((-1 if target[0] > 0 else 1)*p[2], p[1]) for p in pts]
                else:
                    uv = [((1 if target[2] > 0 else -1)*p[0], p[1]) for p in pts]
            B.acc(group, mat).poly(pts, uv, col)

        def box(mat, x0, x1, y0, y1, z0, z1, col=(1, 1, 1, 1), faces='all'):
            bb = bounds(x0, x1, y0, y1, z0, z1)
            a, b = bb['min'], bb['max']
            B.box(group, mat, a[0], b[0], a[1], b[1], a[2], b[2], faces=faces, col=col)

        def tube(mat, a, b, radius, seg=8, col=(.75, .77, .73, 1), caps=False):
            B.cylinder(group, mat, point(a), point(b), radius, seg=seg, caps=caps, col=col)

        def bolt(x, sign, y, z):
            tube(galv, (x, y, z), (x+sign*.004, y, z), .006, seg=6, col=(.53, .56, .52, 1))
            pts = [(x+sign*.004, y+.006*math.cos(i*math.tau/6), z+.006*math.sin(i*math.tau/6)) for i in range(6)]
            poly(galv, pts, (sign, 0, 0), col=(.63, .65, .61, 1))

        # The actual opaque divider was absent from the old architecture renderer.
        # Recess each handrail into the existing 150 mm volume, leaving a solid backing.
        box(paint, 1.422, 1.488, base, top+1.2, 1.4, 3.92, col=paint_colour)
        for za, zb in [(1.4, 1.44), (3.88, 3.92)]:
            box(paint, 1.38, 1.53, base, top+1.2, za, zb, col=(.26, .30, .27, 1))
        for y in [base, base+1.5, top, top+1.18]:
            box(paint, 1.420, 1.490, y, min(y+.02, top+1.2), 1.44, 3.88, col=(.29, .34, .30, 1))
        record['spineBounds'] = bounds(1.38, 1.53, base, top+1.2, 1.4, 3.92)
        record['opaqueSpineBounds'] = bounds(1.422, 1.488, base, top+1.2, 1.4, 3.92)

        for first in [True, False]:
            x0 = S['firstFlightX'] if first else S['secondFlightX']
            x1 = x0+S['flightWidth']
            foot = base if first else base+1.5
            direction = -1 if first else 1
            zfoot = S['flightZ']+S['flightRun'] if first else S['flightZ']
            zhead = zfoot+direction*S['flightRun']
            flight = {'id': home_id+('/first' if first else '/return'), 'first': first,
                      'fromY': foot, 'toY': foot+1.5, 'treads': [],
                      'clearWidth': S['flightWidth'],
                      'soffitEndpoints': [point((x0, foot-.15, zfoot)), point((x0, foot+1.2, zhead))]}
            for i in range(1, S['treadsPerFlight']+1):
                y = foot+i*S['rise']
                za = zfoot+direction*(i-1)*S['going']
                zb = za+direction*S['going']
                nose = za+direction*.006
                poly(tread_mat, [(x0, y, nose), (x1, y, nose), (x1, y, zb), (x0, y, zb)],
                     (0, 1, 0), [(0, .006/S['going']), (1, .006/S['going']), (1, 1), (0, 1)],
                     [(.88, .89, .85, 1), (.88, .89, .85, 1), (.97, .97, .94, 1), (.97, .97, .94, 1)])
                poly(tread_mat, [(x0, y-.006, za), (x1, y-.006, za), (x1, y, nose), (x0, y, nose)],
                     (0, 1, -direction), [(0, 0), (1, 0), (1, .006/S['going']), (0, .006/S['going'])], col=(.9, .91, .87, 1))
                bottom = foot-.15 if i == 1 else y-.15
                poly(concrete, [(x0, bottom, za), (x1, bottom, za), (x1, y-.006, za), (x0, y-.006, za)],
                     (0, 0, -direction), col=[(.60, .63, .59, 1), (.60, .63, .59, 1), (.92, .93, .88, 1), (.92, .93, .88, 1)])
                for xx, nx in [(x0, -1), (x1, 1)]:
                    poly(concrete, [(xx, y-.30, za), (xx, y-.006, za), (xx, y, nose), (xx, y, zb), (xx, y-.15, zb)],
                         (nx, 0, 0), col=(.77, .79, .74, 1))
                bb = bounds(x0, x1, y-.30, y, min(za, zb), max(za, zb))
                keys = ('x0', 'y0', 'z0', 'x1', 'y1', 'z1')
                matches = [b for b in L['boxes'] if b['id'] == 'stair' and
                           all(abs(b[k]-v) < eps for k, v in zip(keys, bb['min']+bb['max']))]
                assert len(matches) == 1, (h['id'], first, i, bb)
                flight['treads'].append({'index': i, 'mapBounds': bb})
            poly(soffit, [(x0, foot-.15, zfoot), (x1, foot-.15, zfoot), (x1, foot+1.2, zhead), (x0, foot+1.2, zhead)],
                 (0, -1, 0), col=(.66, .69, .64, 1))
            # Close the waist on its existing end plane. Nothing extends under the
            # retained half landing or upper floor, so their clearance is unchanged.
            poly(concrete, [(x0, foot+1.2, zhead), (x1, foot+1.2, zhead),
                            (x1, foot+1.35, zhead), (x0, foot+1.35, zhead)],
                 (0, 0, direction), col=(.69, .72, .67, 1))

            inner_x = 1.398 if first else 1.512
            outer_x = .150 if first else 2.765
            inner_support = 1.426 if first else 1.484
            outer_support = .122 if first else 2.798
            za, zb = zfoot+direction*.020, zhead-direction*.020

            def rail_y(z):
                return foot+.15+(z-zfoot)*direction*pitch+.95

            a, b = (inner_x, rail_y(za), za), (inner_x, rail_y(zb), zb)
            oa, ob = (outer_x, a[1], za), (outer_x, b[1], zb)
            tube(rail_mat, a, b, .018, caps=True)
            tube(rail_mat, oa, ob, .018, caps=True)
            for inner, outer in [(a, oa), (b, ob)]:
                tube(rail_mat, inner, (inner_support, inner[1], inner[2]), .018)
                tube(rail_mat, outer, (outer_support, outer[1], outer[2]), .018)
            for t in [.22, .78]:
                z = za+(zb-za)*t
                y = rail_y(z)
                for x, support in [(inner_x, inner_support), (outer_x, outer_support)]:
                    tube(rail_mat, (x, y-.012, z), (x, y-.072, z), .009, seg=6)
                    tube(rail_mat, (x, y-.072, z), (support, y-.072, z), .009, seg=6)
                    toward_lane = 1 if x > support else -1
                    face = support+toward_lane*.004
                    box(galv, min(support, face), max(support, face), y-.106, y-.038, z-.025, z+.025, col=(.43, .47, .43, 1))
                    bolt(face, toward_lane, y-.072, z)
            flight['rail'] = {'start': point(a), 'end': point(b), 'radius': .018,
                              'outerStart': point(oa), 'outerEnd': point(ob), 'outerRadius': .018,
                              'heightAboveNosingPitch': .95, 'sealedEnds': True}
            flight['handrailSupportFaces'] = {'innerX': origin_x+inner_support, 'outerX': origin_x+outer_support}
            record['flights'].append(flight)

        # At the top the physical guard closes the first-flight edge. Its opaque
        # backing and supported tube stay within the unchanged guard/divider union.
        box(paint, .12, 1.38, top, top+1.2, 3.86, 3.880, col=paint_colour)
        for xa, xb in [(.12, .17), (1.33, 1.38)]:
            box(paint, xa, xb, top, top+1.2, 3.86, 3.92, col=(.26, .30, .27, 1))
        box(rail_mat, .12, 1.38, top+1.182, top+1.2, 3.86, 3.92, col=(.62, .66, .61, 1))
        gy = top+.95-.02*pitch
        tube(rail_mat, (.145, gy, 3.90), (1.512, gy, 3.90), .018, caps=True)
        for x in [.43, 1.05]:
            tube(rail_mat, (x, gy-.012, 3.90), (x, gy-.07, 3.90), .009, seg=6)
            tube(rail_mat, (x, gy-.07, 3.90), (x, gy-.07, 3.872), .009, seg=6)
        record['guardBounds'] = bounds(.12, 1.38, top, top+1.2, 3.86, 3.92)
        record['landingRail'] = {'start': point((.145, gy, 3.90)), 'end': point((1.512, gy, 3.90)), 'radius': .018, 'sealedEnds': True}

        # Exclude the full-home membrane replacements when measuring the stair
        # assembly itself, so its bounds remain useful for route regression checks.
        authored = [(v[0]+72, v[2], 60-v[1]) for key, acc in B.groups.items()
                    for v in acc.verts[before.get(key, 0):]]
        assert authored
        stair_bb = bounds(.12, 2.8, base-.151, top+1.201, 1.4, 3.92)
        assert all(stair_bb['min'][i]-eps <= p[i] <= stair_bb['max'][i]+eps for p in authored for i in range(3)), h['id']
        record['actualMapBounds'] = {'min': [min(p[i] for p in authored) for i in range(3)],
                                    'max': [max(p[i] for p in authored) for i in range(3)]}
        record['legacyRetirement'] = {'treadTriangles': 312, 'railTriangles': 136, 'totalTriangles': 448,
                                     'materialTriangles': {'hr_concrete_cast': 180, 'hr_concrete_board': 36,
                                                          'hr_rubber': 96, 'hr_steel_black': 136},
                                     'epsilon': .008,
                                     'treadMasks': [{'min': [x0, base-.151, 1.4], 'max': [x1, top+.006, 3.92]}
                                                    for x0, x1 in [(.18, 1.38), (1.53, 2.73)]],
                                     'treadMaterials': ['hr_concrete_cast', 'hr_concrete_board', 'hr_rubber'],
                                     'guardMask': {'min': [.11, top, 3.86], 'max': [1.39, top+1.2, 3.92]},
                                     'guardMaterial': 'hr_steel_black', 'maskCoordinates': 'local x/z frame; absolute map y'}
        report['privateStairs'].append(record)

        # The old full-home ceiling and upper floor cards cover the stair void.
        # Replace only those cards with planar rectangles around the exact hole.
        vx, vz, vw, vd = S['floorVoid']
        vb = bounds(vx, vx+vw, top, top, vz, vz+vd)
        hole = [vb['min'][0], vb['min'][2], vw, vd]
        assert any(all(abs(a-b) < eps for a, b in zip(hole, v)) for v in L['voids']), (h['id'], hole)
        old_rect = [hx+.2, hz+.2, 8.6, 7.6]
        pieces = subtract_rect(old_rect, hole)
        for material, plane_y, source_home, up in [('hr_ceiling', top-.205, h['id'], False),
                                                 ('hr_floor_laminate', top+.004, home_id+'-U', True)]:
            for x, z, w, d in pieces:
                B.box(group, material, x, x+w, plane_y, plane_y, z, z+d, faces='+y' if up else '-y')
            report['privateSheetRetirement'].append({'owner': h['id'], 'homeId': source_home,
                                                      'material': material, 'planeY': plane_y,
                                                      'oldRect': old_rect, 'voidRect': hole,
                                                      'newAnnularParts': pieces, 'triangles': 2})

    assert len(report['privateStairs']) == 8
    assert sum(len(c['flights']) for c in report['privateStairs']) == 16
    assert sum(len(f['treads']) for c in report['privateStairs'] for f in c['flights']) == 144
    assert len(report['privateSheetRetirement']) == 16
    report['privateStairProvenance'] = 'Original ONSITE geometry and existing shared materials; source ST-H collision/void contract retained.'
    report['privateStairRetirementTotals'] = {'homes': 8, 'treadTriangles': 2496, 'guardTriangles': 1088,
                                             'stairTriangles': 3584, 'sheetTriangles': 32, 'totalTriangles': 3616}



"""Original ONSITE narrow-door joinery correction, 20 October 2026.

Standalone assembly fragment: no Blender file loading/export, no physical changes.
The held-open leaves keep their material and dimensions, folding flat against
the longer P2 wall on the opposite jamb. Head strips and thresholds remain.
"""


def build_narrow_door_jambs(B, L, report):
    import math

    openings = [o for o in L['openings'] if o['kind'] == 'inner-door' and o['width'] <= .800001]
    assert len(openings) == 16
    report.setdefault('narrowDoorJoinery', [])
    for o in openings:
        cx, cz, base = o['x'], o['z'], o['y']
        w, h, t = o['width'], o['height'], o['wall']
        assert abs(w-.8) < 1e-6 and abs(h-2.2) < 1e-6 and abs(t-.12) < 1e-6
        home = next(q for q in L['homes'] if q['x']-.01 <= cx <= q['x']+9.01 and q['z']-.01 <= cz <= q['z']+8.01)
        ax, az = (1, 0) if o['axis'] == 'x' else (0, 1)
        nx, nz = (0, o['normal']) if o['axis'] == 'x' else (o['normal'], 0)
        side = -1 if ax*(cx-home['x']-4.5)+az*(cz-home['z']-4) <= 0 else 1
        group = 'building/' + o['owner'].split('-', 1)[0]

        def point(u, v, d):
            return (cx+ax*u+nx*d, base+v, cz+az*u+nz*d)

        def bounds(u0, u1, v0, v1, d0, d1):
            a, b = point(u0, v0, d0), point(u1, v1, d1)
            return {'min': [min(a[i], b[i]) for i in range(3)],
                    'max': [max(a[i], b[i]) for i in range(3)]}

        def box(mat, u0, u1, v0, v1, d0, d1, faces='all', col=(1, 1, 1, 1)):
            bb = bounds(u0, u1, v0, v1, d0, d1)
            a, b = bb['min'], bb['max']
            B.box(group, mat, a[0], b[0], a[1], b[1], a[2], b[2], faces=faces, col=col)
            return bb

        old_hinge = side*(w/2-.06)
        old_u0, old_u1 = sorted([old_hinge, old_hinge-side*.045])
        old_d0 = -t/2-.02-(w-.12)*math.sin(math.radians(92))
        old_d1 = -t/2-.02
        new_side = -side
        new_u0, new_u1 = sorted([new_side*w/2, new_side*(w/2+w-.12)])
        new_d0, new_d1 = -t/2-.02-.045, -t/2-.02
        record = {'id': '%s/%g/narrow-door' % (o['owner'], base), 'owner': o['owner'],
                  'opening': dict(o), 'hingeSide': new_side, 'originalHingeSide': side, 'clearOpeningWidth': w,
                  'jambProjection': .012, 'casings': [], 'hinges': [],
                  'oldLeafBounds': bounds(old_u0, old_u1, .01, h-.06, old_d0, old_d1),
                  'newLeafBounds': bounds(new_u0, new_u1, .01, h-.06, new_d0, new_d1),
                  'leafPose': 'Held fully open parallel to the longer P2 wall, hinged on the opposite jamb; original 0.68 m width and 45 mm thickness.',
                  'provenance': 'Original ONSITE geometry derived from the existing inner-door record.'}

        # Casing boards sit on each wall face, outside the opening's two edges.
        # Their buried backs are omitted: no coincident new face over the wall.
        for u0, u1 in [(-w/2-.06, -w/2), (w/2, w/2+.06)]:
            support = bounds(u0, u1, 0, h, -t/2, t/2)
            supports = [b for b in L['boxes'] if b['id'].startswith('wall-') and
                        all(b[k]-1e-6 <= v for k, v in zip(('x0', 'y0', 'z0'), support['min'])) and
                        all(b[k]+1e-6 >= v for k, v in zip(('x1', 'y1', 'z1'), support['max']))]
            assert supports, (o, support)
            for face_side in [-1, 1]:
                d0, d1 = sorted([face_side*t/2, face_side*(t/2+.012)])
                sign = face_side*o['normal']
                back = ('-x' if sign > 0 else '+x') if nx else ('-z' if sign > 0 else '+z')
                faces = ' '.join(k for k in ['+x', '-x', '+y', '-y', '+z', '-z'] if k != back)
                bb = box('hr_timber', u0, u1, 0, h, d0, d1, faces=faces, col=(.92, .92, .89, 1))
                record['casings'].append({'mapBounds': bb, 'supportBounds': support,
                                          'supportBoxIds': sorted(set(b['id'] for b in supports)),
                                          'side': face_side})

        # A perpendicular leaf outside this portal still crosses the external
        # entry approach. Fold it flat against the longer opposite-side wall.
        # The whole original 680 mm leaf is backed by an unchanged solid wall.
        support = bounds(new_u0, new_u1, .01, h-.06, -t/2, t/2)
        supports = [b for b in L['boxes'] if b['id'].startswith('wall-') and
                    all(b[k]-1e-6 <= v for k, v in zip(('x0', 'y0', 'z0'), support['min'])) and
                    all(b[k]+1e-6 >= v for k, v in zip(('x1', 'y1', 'z1'), support['max']))]
        assert supports, (o, support)
        record['leafSupportBounds'] = support
        record['leafSupportBoxIds'] = sorted(set(b['id'] for b in supports))
        box('hr_plaster', new_u0, new_u1, .01, h-.06, new_d0, new_d1)
        hinge_u = new_side*(w/2+.0225)
        hinge_d = -t/2-.016
        for v in [.35, h-.35]:
            hu0, hu1 = sorted([new_side*(w/2+.006), new_side*(w/2+.042)])
            casing_plate = box('hr_steel_galv', hu0, hu1, v-.040, v+.040,
                               -t/2-.018, -t/2-.005, col=(.50, .54, .49, 1))
            leaf_plate = box('hr_steel_galv', hu0, hu1, v-.040, v+.040,
                             new_d1-.025, new_d1, col=(.50, .54, .49, 1))
            a, b = point(hinge_u, v-.050, hinge_d), point(hinge_u, v+.050, hinge_d)
            B.cylinder(group, 'hr_steel_galv', a, b, .009, seg=6, caps=True, col=(.62, .65, .60, 1))
            record['hinges'].append({'start': a, 'end': b, 'radius': .009,
                                      'casingPlateBounds': casing_plate, 'leafPlateBounds': leaf_plate})

        record['legacyRetirement'] = {
            'epsilon': .008, 'jambMaterial': 'hr_timber', 'jambTriangles': 24,
            'jambMasks': [{'min': [u0, 0, -t/2], 'max': [u1, h, t/2]}
                          for u0, u1 in [(-w/2, -w/2+.06), (w/2-.06, w/2)]],
            'jambFacePredicate': {
                'longVertical': {'minHeightExclusive': h-.03},
                'horizontalEnd': {'maxHeightExclusive': .001, 'minAlongWidthExclusive': .04,
                                  'minWallDepthExclusive': t-.02, 'heightPlanes': [0, h], 'planeEpsilon': .008}},
            'preservedCoincidentHeadCapTriangles': 4,
            'preservedCoincidentThresholdCapTriangles': 4,
            'leafMaterial': 'hr_plaster', 'leafTriangles': 12,
            'leafMask': {'min': [old_u0, .01, old_d0], 'max': [old_u1, h-.06, old_d1]},
            'totalTriangles': 36,
            'maskCoordinates': 'doorway local [along-wall u, above-floor v, outward-normal d]'}
        report['narrowDoorJoinery'].append(record)

    assert len(report['narrowDoorJoinery']) == 16
    report['narrowDoorJoineryTotals'] = {'doors': 16, 'oldJambTriangles': 384, 'oldLeafTriangles': 192,
                                       'retiredTriangles': 576, 'preservedHeadCapTriangles': 64,
                                       'preservedThresholdCapTriangles': 64,
                                       'clearOpeningWidth': .8, 'casingProjection': .012}


"""Original ONSITE P1 D02 hallway-leaf pose correction, 20 October 2026.

Only the sixteen evidenced 0.9 m P1 D02 leaves are replaced. Their frames,
thresholds, openings and collision stay intact. Other joinery records are separate.
"""


def build_adjacent_hallway_leaves(B, L, report):
    import math

    eps = 1e-6
    report.setdefault('adjacentHallwayLeaves', [])
    for home in [h for h in L['homes'] if h['module'] == 'H2-L']:
        owner = home['id'].removesuffix('-L')
        expected_x = home['x']+4.44
        expected_z = home['z']+(6.5 if home['mirror'] else 1.5)
        doors = [o for o in L['openings'] if o['kind'] == 'inner-door' and o['owner'] == owner
                 and abs(o['width']-.9) < eps and o['axis'] == 'z' and o['normal'] == -1
                 and abs(o['x']-expected_x) < eps and abs(o['z']-expected_z) < eps
                 and any(abs(o['y']-y) < eps for y in [home['y'], home['y']+3])]
        assert len(doors) == 2, (home['id'], doors)
        for o in doors:
            group = 'building/'+owner.split('-', 1)[0]
            cx, cz, base = o['x'], o['z'], o['y']
            w, height, wall = o['width'], o['height'], o['wall']
            source_home = next(h for h in L['homes'] if h['x']-.01 <= cx <= h['x']+9.01 and h['z']-.01 <= cz <= h['z']+8.01)
            side = -1 if cz-(source_home['z']+4) <= 0 else 1
            hinge = side*(w/2-.06)
            length = w-.12
            old_u0, old_u1 = sorted([hinge, hinge-side*.045])
            old_d0, old_d1 = -wall/2-.02-length*math.sin(math.radians(92)), -wall/2-.02
            new_u0, new_u1 = sorted([hinge, hinge+side*length])
            new_d0, new_d1 = -wall/2-.02-.045, -wall/2-.02

            def point(u, v, d):
                return (cx-d, base+v, cz+u)

            def bounds(u0, u1, v0, v1, d0, d1):
                a, b = point(u0, v0, d0), point(u1, v1, d1)
                return {'min': [min(a[i], b[i]) for i in range(3)],
                        'max': [max(a[i], b[i]) for i in range(3)]}

            def box(mat, u0, u1, v0, v1, d0, d1, col=(1, 1, 1, 1)):
                bb = bounds(u0, u1, v0, v1, d0, d1)
                a, b = bb['min'], bb['max']
                B.box(group, mat, a[0], b[0], a[1], b[1], a[2], b[2], col=col)
                return bb

            # The 720 mm part beyond the opening is backed by the unchanged P1
            # wall; its remaining 60 mm aligns with the existing timber jamb.
            support_u0, support_u1 = sorted([hinge+side*length, side*w/2])
            support = bounds(support_u0, support_u1, .01, height-.06, -wall/2, wall/2)
            supports = [b for b in L['boxes'] if b['id'].startswith('wall-') and
                        all(b[k]-eps <= v for k, v in zip(('x0', 'y0', 'z0'), support['min'])) and
                        all(b[k]+eps >= v for k, v in zip(('x1', 'y1', 'z1'), support['max']))]
            assert supports, (o, support)
            new_bounds = box('hr_plaster', new_u0, new_u1, .01, height-.06, new_d0, new_d1)
            hinges = []
            for v in [.35, height-.35]:
                pin_u, pin_d = side*(w/2-.043), -wall/2-.011
                a, b = point(pin_u, v-.05, pin_d), point(pin_u, v+.05, pin_d)
                B.cylinder(group, 'hr_steel_galv', a, b, .012, seg=6, caps=True, col=(.59, .63, .58, 1))
                u0, u1 = sorted([side*(w/2-.055), side*(w/2-.005)])
                frame_plate = box('hr_steel_galv', u0, u1, v-.04, v+.04,
                                  -wall/2-.015, -wall/2+.005, col=(.48, .52, .47, 1))
                leaf_plate = box('hr_steel_galv', u0, u1, v-.04, v+.04,
                                 new_d1-.012, new_d1, col=(.48, .52, .47, 1))
                hinges.append({'start': a, 'end': b, 'radius': .012,
                               'framePlateBounds': frame_plate, 'leafPlateBounds': leaf_plate})
            report['adjacentHallwayLeaves'].append({
                'id': '%s/%g/P1-D02' % (owner, base), 'owner': owner, 'opening': dict(o),
                'home': dict(home), 'hingeSide': side,
                'oldLeafBounds': bounds(old_u0, old_u1, .01, height-.06, old_d0, old_d1),
                'newLeafBounds': new_bounds, 'supportWallBounds': support,
                'supportWallIds': sorted(set(b['id'] for b in supports)), 'hinges': hinges,
                'pose': 'Held fully open parallel to the existing hallway wall; same 0.78 m width, 45 mm thickness and height.',
                'legacyRetirement': {'material': 'hr_plaster', 'epsilon': .008, 'triangles': 12,
                                     'mask': {'min': [old_u0, .01, old_d0], 'max': [old_u1, height-.06, old_d1]},
                                     'maskCoordinates': 'doorway local [along-wall u, above-floor v, outward-normal d]'},
                'provenance': 'Original ONSITE correction of the existing sixteen P1 D02 held-open leaf poses.'})
    assert len(report['adjacentHallwayLeaves']) == 16
    report['adjacentHallwayLeafTotals'] = {'doors': 16, 'retiredTriangles': 192,
                                         'material': 'hr_plaster', 'collisionChanges': 0}



"""Original ONSITE upper D01 exterior leaf-pose correction, 20 October 2026.

Only the eight evidenced upper maisonette entry leaves and their glass inserts
are replaced. Existing frames, thresholds, partitions and physics stay intact.
"""


def build_upper_entry_leaves(B, L, report):
    import math

    eps = 1e-6
    report.setdefault('upperEntryLeaves', [])
    for home in [h for h in L['homes'] if h['module'] == 'H2-L']:
        owner = home['id'].removesuffix('-L')
        doors = [o for o in L['openings'] if o['kind'] == 'door' and o['owner'] == owner
                 and o['axis'] == 'x' and abs(o['width']-1.1) < eps
                 and abs(o['y']-(home['y']+3)) < eps
                 and abs(o['x']-(home['x']+5.25)) < eps
                 and abs(o['z']-(home['z']+(7.9 if home['mirror'] else .1))) < eps]
        assert len(doors) == 1, (home, doors)
        o = doors[0]
        group = 'building/'+owner.split('-', 1)[0]
        cx, cz, base = o['x'], o['z'], o['y']
        width, height, wall, normal = o['width'], o['height'], o['wall'], o['normal']
        assert abs(height-2.2) < eps and abs(wall-.2) < eps
        assert normal == (1 if home['mirror'] else -1)
        # Original module-centre hinge rule; all selected doors use +u.
        side = -1 if cx-(home['x']+4.5) <= 0 else 1
        assert side == 1
        hinge, length = side*(width/2-.06), width-.12
        old_u0, old_u1 = sorted([hinge, hinge-side*.045])
        old_d0, old_d1 = -wall/2-.02-length*math.sin(math.radians(92)), -wall/2-.02
        new_u0, new_u1 = sorted([hinge, hinge+side*length])
        new_d0, new_d1 = wall/2+.02, wall/2+.02+.045
        glass_u0, glass_u1 = new_u0+.12, new_u1-.12
        glass_v0, glass_v1 = (height-.06)*.45, height-.06-.15

        def point(u, v, d):
            return (cx+u, base+v, cz+normal*d)

        def bounds(u0, u1, v0, v1, d0, d1):
            a, b = point(u0, v0, d0), point(u1, v1, d1)
            return {'min': [min(a[i], b[i]) for i in range(3)],
                    'max': [max(a[i], b[i]) for i in range(3)]}

        def box(mat, u0, u1, v0, v1, d0, d1, col=(1, 1, 1, 1)):
            bb = bounds(u0, u1, v0, v1, d0, d1)
            a, b = bb['min'], bb['max']
            B.box(group, mat, a[0], b[0], a[1], b[1], a[2], b[2], col=col)
            return bb

        # Same hinge and leaf width, folded outwards fully flat. The unchanged
        # exterior wall backs 920 mm; the remaining 60 mm aligns with its jamb.
        support = bounds(width/2, new_u1, .01, height-.06, -wall/2, wall/2)
        supports = [b for b in L['boxes'] if b['id'].startswith('wall-') and
                    all(b[k]-eps <= v for k, v in zip(('x0', 'y0', 'z0'), support['min'])) and
                    all(b[k]+eps >= v for k, v in zip(('x1', 'y1', 'z1'), support['max']))]
        assert supports, (o, support)
        frame_support = bounds(hinge, width/2, .01, height-.06, -wall/2, wall/2)
        # Four painted pieces surround the real glass aperture, retaining both
        # original materials without burying transparent glass in an opaque slab.
        painted = []
        for u0, u1, v0, v1 in [
                (new_u0, glass_u0, .01, height-.06),
                (glass_u1, new_u1, .01, height-.06),
                (glass_u0, glass_u1, .01, glass_v0),
                (glass_u0, glass_u1, glass_v1, height-.06)]:
            painted.append(box('hr_door_paint', u0, u1, v0, v1, new_d0, new_d1))
        glass = box('hr_glass', glass_u0, glass_u1, glass_v0, glass_v1,
                    new_d0-.002, new_d1+.002)
        hinges = []
        for v in [.35, height-.35]:
            pin_u, pin_d = hinge+.026, wall/2+.013
            a, b = point(pin_u, v-.05, pin_d), point(pin_u, v+.05, pin_d)
            B.cylinder(group, 'hr_steel_galv', a, b, .012, seg=6, caps=True, col=(.59, .63, .58, 1))
            frame_plate = box('hr_steel_galv', hinge+.005, width/2-.005, v-.04, v+.04,
                              wall/2-.005, wall/2+.022, col=(.48, .52, .47, 1))
            leaf_plate = box('hr_steel_galv', hinge+.005, width/2-.005, v-.04, v+.04,
                             new_d0, new_d0+.012, col=(.48, .52, .47, 1))
            hinges.append({'start': a, 'end': b, 'radius': .012,
                           'framePlateBounds': frame_plate, 'leafPlateBounds': leaf_plate})
        report['upperEntryLeaves'].append({
            'id': '%s/%g/upper-D01' % (owner, base), 'owner': owner, 'opening': dict(o),
            'home': dict(home), 'hingeSide': side,
            'oldLeafBounds': bounds(old_u0, old_u1, .01, height-.06, old_d0, old_d1),
            'oldGlassBounds': bounds(old_u0-.002, old_u1+.002, glass_v0, glass_v1, old_d0+.12, old_d1-.12),
            'newLeafBounds': bounds(new_u0, new_u1, .01, height-.06, new_d0, new_d1),
            'paintedPartBounds': painted, 'newGlassBounds': glass,
            'supportWallBounds': support, 'supportWallIds': sorted(set(b['id'] for b in supports)),
            'supportFrameBounds': frame_support, 'hinges': hinges,
            'pose': 'Same hinge; held fully open flat against the exterior wall, with the original painted leaf and glass materials.',
            'legacyRetirement': {'epsilon': .008, 'triangles': 24, 'parts': [
                {'material': 'hr_door_paint', 'triangles': 12,
                 'mask': {'min': [old_u0, .01, old_d0], 'max': [old_u1, height-.06, old_d1]}},
                {'material': 'hr_glass', 'triangles': 12,
                 'mask': {'min': [old_u0-.002, glass_v0, old_d0+.12],
                          'max': [old_u1+.002, glass_v1, old_d1-.12]}}],
                'maskCoordinates': 'doorway local [along-wall u, above-floor v, outward-normal d]'},
            'provenance': 'Original ONSITE correction of the eight upper H2 D01 held-open leaf poses.'})
    assert len(report['upperEntryLeaves']) == 8
    report['upperEntryLeafTotals'] = {'doors': 8, 'retiredPaintTriangles': 96,
                                     'retiredGlassTriangles': 96, 'retiredTriangles': 192,
                                     'collisionChanges': 0}


def quadrant(x, z):
    return 'building/'+('N' if z < 60 else 'S')+('W' if x < 72 else 'E')


def snapshot():
    return {key: len(acc.verts) for key, acc in B.groups.items()}


def feature(name, kind, owner, before, support, projection, extra=None):
    points = [(v[0]+72, v[2], 60-v[1]) for key, acc in B.groups.items() for v in acc.verts[before.get(key, 0):]]
    assert points, name
    bounds = {'min': [min(p[i] for p in points) for i in range(3)],
              'max': [max(p[i] for p in points) for i in range(3)]}
    report['features'].append({'name': name, 'kind': kind, 'owner': owner, 'mapBounds': bounds,
                               'support': support, 'maxSurfaceProjection': projection, **(extra or {})})


class Face:
    """Oriented facade coordinates: u along wall, y absolute height, d outward from face."""

    def __init__(self, x, z, ax, az, nx, nz, group=None):
        self.x, self.z, self.ax, self.az, self.nx, self.nz = x, z, ax, az, nx, nz
        self.group = group or quadrant(x, z)

    def p(self, u, y, d):
        return self.x+self.ax*u+self.nx*d, y, self.z+self.az*u+self.nz*d

    def box(self, mat, u0, u1, y0, y1, d0, d1, col=(1, 1, 1, 1)):
        a, b = self.p(u0, y0, d0), self.p(u1, y1, d1)
        B.box(self.group, mat, min(a[0], b[0]), max(a[0], b[0]), y0, y1,
              min(a[2], b[2]), max(a[2], b[2]), col=col)

    def poly(self, mat, pts, normal, col=(1, 1, 1, 1)):
        points = [self.p(*p) for p in pts]
        n = Vector((self.ax*normal[0]+self.nx*normal[2], normal[1], self.az*normal[0]+self.nz*normal[2]))
        cross = (Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0]))
        if cross.dot(n) < 0:
            points.reverse()
        B.acc(self.group, mat).poly(points, planar_uv(points), col)

    def profile(self, mat, u0, u1, profile, col=(1, 1, 1, 1)):
        # Closed extruded cross-section with explicit end returns, no flat stand-in card.
        area = sum(profile[i][0]*profile[(i+1) % len(profile)][1]
                   - profile[(i+1) % len(profile)][0]*profile[i][1] for i in range(len(profile)))
        sign = 1 if area > 0 else -1
        for i, (y0, d0) in enumerate(profile):
            y1, d1 = profile[(i+1) % len(profile)]
            self.poly(mat, [(u0, y0, d0), (u1, y0, d0), (u1, y1, d1), (u0, y1, d1)],
                      (0, sign*(d1-d0), sign*(y0-y1)), col)
        self.poly(mat, [(u0, y, d) for y, d in profile], (-1, 0, 0), col)
        self.poly(mat, [(u1, y, d) for y, d in profile], (1, 0, 0), col)

    def tube(self, mat, a, b, radius, seg=8, col=(1, 1, 1, 1), caps=False):
        B.cylinder(self.group, mat, self.p(*a), self.p(*b), radius, seg=seg, caps=caps, col=col)


def public_portals():
    core_ids = {c['id'] for c in L['cores']}
    for door in [o for o in L['openings'] if o['kind'] == 'door' and o['owner'] in core_ids]:
        x, z, y, width = door['x'], door['z'], door['y'], door['width']
        nx, nz = (0, door['normal']) if door['axis'] == 'x' else (door['normal'], 0)
        ax, az = (1, 0) if door['axis'] == 'x' else (0, 1)
        face = Face(x+nx*door['wall']/2, z+nz*door['wall']/2, ax, az, nx, nz)
        before = snapshot()
        # Jamb collars sit OVER the masonry, entirely outside the existing 1.5m opening.
        # Existing steel frames, held-open leaves, thresholds and name signs remain visible.
        for sign in [-1, 1]:
            u0, u1 = sorted([sign*(width/2+.002), sign*(width/2+.125)])
            face.box(CAST, u0, u1, y+.025, y+2.40, .001, .028,
                     col=(.80, .82, .77, 1))
            face.box(RUBBER, min(sign*(width/2+.002), sign*(width/2+.010)),
                     max(sign*(width/2+.002), sign*(width/2+.010)), y+.03, y+2.40, .029, .031,
                     col=(.58, .59, .55, 1))
            # A separate boot and horizontal bed joint give the surround a real base.
            face.box(CAST, u0, u1, y+.025, y+.22, .029, .035, col=(.55, .60, .55, 1))
            face.box(RUBBER, u0, u1, y+.221, y+.225, .028, .030, col=(.6, .61, .56, 1))
        # Shallow cast lintel facing with a chamfer/drip. It stops below the existing block sign.
        face.profile(CAST, -width/2-.14, width/2+.14,
                     [(y+2.405, .001), (y+2.405, .036), (y+2.417, .050),
                      (y+2.485, .050), (y+2.485, .001)], col=(.85, .86, .81, 1))
        face.box(GALV, -width/2-.145, width/2+.145, y+2.485, y+2.496, .002, .053,
                 col=(.44, .48, .44, 1))
        feature(door['owner']+' portal '+str(y), 'public-portal', door['owner'], before,
                {'opening': door, 'masonryFace': [face.x, face.z]}, .053,
                {'openingClearWidthUnchanged': width, 'minHeaderY': y+2.405})
        report['protectedOpenings'].append({'owner': door['owner'], 'x': x, 'z': z, 'floorY': y,
                                            'width': width, 'height': door['height'], 'axis': door['axis'],
                                            'normal': door['normal'], 'newTrimInsideOpening': False})


def core_drainage_and_sills():
    arch = Arch(L, B)  # Query existing cosmetic window placement only; never rebuild architecture.
    for core in L['cores']:
        x, z, _, _ = core['rect']
        n = -1 if core['mirror'] else 1
        front = z if core['mirror'] else z+6
        face = Face(x, front, 1, 0, 0, n)
        before = snapshot()
        # The 160mm left corner pier clears existing glazing/sills, right-side CCTV and door furniture.
        u = .16
        bottom, top = max(0, core['levels'][0])+.12, core['levels'][-1]+3.14
        face.tube(BLACK, (u, bottom, .044), (u, top, .044), .032, seg=10, col=(.65, .69, .64, 1))
        for height in [bottom+.07]+[y+.48 for y in core['levels'] if y >= 0]+[top-.18]:
            face.tube(BLACK, (u, height-.024, .044), (u, height+.024, .044), .039, seg=10, col=(.58, .63, .58, 1))
            face.box(GALV, u-.052, u+.052, height-.05, height+.05, .001, .009, col=(.39, .43, .39, 1))
            face.tube(GALV, (u, height, .009), (u, height, .044), .012, seg=6, col=(.48, .52, .47, 1))
        # Shallow hopper around a parapet scupper, fed into the pipe; no fabricated deep wall opening.
        hy = core['levels'][-1]+3.03
        face.profile(BLACK, u-.12, u+.12,
                     [(hy, .019), (hy, .085), (hy+.20, .115), (hy+.20, .012)], col=(.62, .66, .60, 1))
        face.box(GALV, u-.13, u+.13, hy+.19, hy+.205, .008, .120, col=(.46, .51, .46, 1))
        feature(core['id']+' attached drainage', 'core-drainage', core['id'], before,
                {'frontPlane': front, 'coreRect': core['rect'], 'cornerPierLocalX': [.03, .29]}, .120,
                {'doorCentreDistance': 2.84, 'pipeProjection': .083, 'newGroundFurniture': False})

        ext = '-z' if core['mirror'] else '+z'
        for wall in L['boxes']:
            if not wall['id'].startswith('wall-'+core['id']+'-'):
                continue
            wall_face = wall['z0'] if core['mirror'] else wall['z1']
            if abs(wall_face-front) > 1e-6 or wall['z1']-wall['z0'] > .21:
                continue
            for a0, a1, sill, _, floor in arch.blank_windows(wall, 'core', ext):
                before = snapshot()
                # Existing 70mm sill block remains. This proper folded lower lip is attached to its outer edge.
                u0, u1 = a0-x-.06, a1-x+.06
                face.profile(CAST, u0, u1,
                             [(sill-.073, .047), (sill-.082, .047), (sill-.082, .071),
                              (sill-.050, .076), (sill-.050, .059), (sill-.073, .059)],
                             col=(.62, .68, .62, 1))
                feature(core['id']+' sill drip '+str(round(a0, 3))+'/'+str(floor), 'sill-drip', core['id'], before,
                        {'existingSill': [a0-.06, a1+.06, sill-.07, sill, front]}, .016,
                        {'existingProjection': .06, 'newTotalProjection': .076})


def gallery_joints():
    for index, guard in enumerate(L['guards']):
        x0, z0, x1, z1 = (guard[k] for k in ['x0', 'z0', 'x1', 'z1'])
        length = math.hypot(x1-x0, z1-z0)
        if length < .30:
            continue
        ax, az = (x1-x0)/length, (z1-z0)/length
        nx, nz, y = guard['nx'], guard['nz'], guard['y']
        face = Face(x0+nx*.24, z0+nz*.24, ax, az, nx, nz)
        before = snapshot()
        # Existing fascia is y-.55..y, exterior offset .24. A formed lip makes its runoff edge legible.
        face.profile(CAST, .015, length-.015,
                     [(y-.548, -.005), (y-.554, .012), (y-.530, .026), (y-.514, .015), (y-.514, -.005)],
                     col=(.63, .66, .61, 1))
        joints = [u for u in [3+6*k for k in range(int(length/6)+1)] if .15 < u < length-.15]
        # Panel joints terminate under the coping instead of slicing through its top.
        top = y+1.10 if y > 8.9 else y+.995
        for u in joints:
            # The retained architecture has up to8mm quantisation error: a 9mm stand-off avoids flicker.
            face.box(RUBBER, u-.006, u+.006, y-.51, top, .009, .012, col=(.65, .66, .60, 1))
            face.box(CAST, u-.024, u-.006, y-.51, top, .009, .016, col=(.73, .77, .70, 1))
            # The separate top weathering joint sits on the existing coping, under its rail.
            coping_y = y+1.20 if y > 8.9 else y+1.05
            face.box(RUBBER, u-.006, u+.006, coping_y+.009, coping_y+.010, -.252, .018,
                     col=(.56, .59, .54, 1))
        feature('gallery fascia '+str(index), 'gallery-joint', str(guard.get('level', '')), before,
                {'guard': guard, 'existingFasciaOuterOffset': .24}, .026,
                {'minUnderEdgeY': y-.554, 'jointSpacing': 6, 'jointOffsets': joints})


def bearing_and_pendant_connections():
    for i, column in enumerate(L['columns']):
        x, z, half = column['x'], column['z'], column['size']/2
        group = quadrant(x, z)
        before = snapshot()
        # Capital stays above 2.74m and increases the existing column envelope by only 12mm.
        B.box(group, CAST, x-half-.012, x+half+.012, 2.745, 2.795, z-half-.012, z+half+.012,
              col=(.65, .70, .65, 1))
        B.box(group, RUBBER, x-half-.008, x+half+.008, 2.795, 2.799, z-half-.008, z+half+.008,
              col=(.52, .55, .49, 1))
        feature('column head '+str(i), 'column-bearing', str(i), before, column, .012, {'minimumHeadroom': 2.745})
    for home in L['homes']:
        x, z, floor = home['x']+6.5, home['z']+6, home['y']
        before = snapshot()
        group = quadrant(x, z)
        # Match the OLD shade's unmirrored absolute coordinates; no light/shade movement.
        B.cylinder(group, BLACK, (x, floor+2.60, z), (x, floor+2.789, z), .005, seg=6, caps=False,
                   col=(.66, .69, .65, 1))
        B.cylinder(group, GALV, (x, floor+2.777, z), (x, floor+2.794, z), .039, seg=8,
                   col=(.70, .73, .68, 1))
        feature(home['id']+' pendant support', 'pendant-support', home['id'], before,
                {'existingShadeCentre': [x, floor+2.60, z], 'ceilingY': floor+2.795}, 0,
                {'minimumHeadroom': 2.60, 'newLight': False})


build_private_stairs(B, L, report)
build_narrow_door_jambs(B, L, report)
build_adjacent_hallway_leaves(B, L, report)
build_upper_entry_leaves(B, L, report)
public_portals()
core_drainage_and_sills()
gallery_joints()
bearing_and_pendant_connections()

library = Library()
def material(name):
    if name == 'hr_stair_concrete':
        if name not in library.cache:
            mat = library('hr_concrete_cast').copy()
            mat.name = name
            library.cache[name] = mat
        return library.cache[name]
    return library(name)

objects = B.build(material)
triangles = sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in objects)
assert triangles < 60000 and len(objects) <= 52, (triangles, len(objects))
used_materials = sorted({obj.data.materials[0].name for obj in objects})
for obj in objects:
    obj['provenance'] = 'Original ONSITE construction around unchanged existing architecture.'
    obj['collision'] = 'None. Existing collision/navigation remain authoritative.'
folder = ROOT/'assets/blender/heron-reach'
output = ROOT/'public/models/heron-reach/building-detail.glb'
bpy.context.preferences.filepaths.save_version = 0
for image in bpy.data.images:
    if image.source == 'FILE':
        image.pack()
        assert image.packed_file, image.name
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'building-detail.blend'), compress=True)

# Source Blend remains textured and packed. Export only named material placeholders for runtime reuse.
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
    colour, roughness, metal = PLAIN.get('hr_concrete_cast' if name == 'hr_stair_concrete' else name, ((.7, .75, .8), .88, 0))
    mul.inputs['A'].default_value = (*colour, 1)
    nt.links.new(vcol.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .88 if name == 'hr_stair_concrete' else roughness
    bsdf.inputs['Metallic'].default_value = metal
flags = ['-cc', '-kn', '-km', '-kv', '-vpf', '-vtf']
with tempfile.TemporaryDirectory(prefix='heron-building-') as temp:
    raw = Path(temp)/'building-detail.raw.glb'
    bpy.ops.export_scene.gltf(filepath=str(raw), export_format='GLB', export_apply=True, export_yup=True)
    raw_bytes = raw.stat().st_size
    subprocess.run(['npx', '--no-install', 'gltfpack', '-i', str(raw), '-o', str(output), *flags], cwd=ROOT, check=True)
packed = output.read_bytes()
gltf = json.loads(packed[20:20+int.from_bytes(packed[12:16], 'little')])
assert not gltf.get('images') and not gltf.get('textures')
shipped_triangles = sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])
assert shipped_triangles == triangles, (shipped_triangles, triangles)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {
    'provenance': 'Original ONSITE procedural construction, shared existing project PBR materials. No imported models, new images or new lights.',
    'builder': str(Path(__file__).relative_to(ROOT)), 'builderSHA256': sha(Path(__file__)),
    'blender': bpy.app.version_string, 'layoutSHA256': sha(LAYOUT_PATH),
    'coordinates': 'Map metres x east/y up/z south; glTF world=(mapX-72,mapY,mapZ-60). No offset.',
    'collision': 'Unchanged. Public stairs remain untouched; private render flights follow every existing ST-H box.',
    'collection': 'HR_BUILDING_CONSTRUCTION', **report,
    'triangles': triangles, 'materialBatches': len(objects), 'sharedMaterials': used_materials,
    'materialContract': {'hr_stair_concrete': 'Same dry cast-concrete alias as public stairs, roughness .88/metalness0; no exterior wet shader.',
                         'others': 'Reuse exact existing HeronReachMaterials names and preserve COLOR_0 multiplication.',
                         'embeddedTextures': 0, 'newPointLights': 0},
    'rawGLBBytes': raw_bytes, 'compressedGLBBytes': len(packed), 'compressedGLBSHA256': sha(output),
    'blendSHA256': sha(folder/'building-detail.blend'),
    'compression': {'tool': 'npm gltfpack', 'version': json.loads((ROOT/'node_modules/gltfpack/package.json').read_text())['version'],
                    'flags': flags, 'lockfileSHA256': sha(ROOT/'package-lock.json')},
}
(folder/'building-detail-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('BUILDING_DETAIL', triangles, 'triangles;', len(objects), 'batches;', len(packed), 'bytes;', manifest['compressedGLBSHA256'])
