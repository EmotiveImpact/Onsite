# Heron Reach contact grounding

The original ONSITE module `src/onsite/HeronContactShadows.ts` adds subtle contact darkening beneath
existing props, columns, tree trunks, cover and live bot feet. This is **contact grounding**, not
complete physical shadows, screen-space ambient occlusion, a ray-traced effect or new physics.
The soft mask is an original analytic GLSL ellipse. No donor code, external image, asset download,
generated texture file, render target or extra scene render is introduced.

## Integration

```ts
import {HeronContactShadows} from './HeronContactShadows'

// In the existing Reach scene after loading art:
this.contacts = new HeronContactShadows(this.scene, this.level)

// Each frame, after bots have run render(alpha), before the world render:
this.contacts?.update(game.bots)

// If the world view is destroyed:
this.contacts?.dispose()
```

The constructor adds one InstancedMesh on Heron Reach. Passing Heron Court adds nothing.
`update` accepts the current bot array structurally: `alive`, optional `scale`, and `parts.root`.
It follows the existing interpolated body presentation, so it does not read/write Rapier or
advance another animation/physics clock. Two small foot proxies follow each living visible
root's yaw and position. Hidden, dead, unsupported and sufficiently airborne actors lose them.
They approximate the foot area; they do not trace articulated trainer geometry or corpse poses.

## Receivers and appearance

The support index is built once over the level's existing `surfaceIds`. A four-metre grid
narrows each query to nearby floor boxes. The highest floor at/below the object's base receives
the contact, with at most 4 cm of interpolation tolerance. This preserves B1, ground, galleries,
roof levels, stair treads and actual floor holes independently at shared x/z coordinates.
The soft patch is clipped to that receiver's x/z bounds and fades over the last 3.5 cm at an edge.
A nearby coplanar floor seam can therefore clip part of a patch; it never extends onto an
unsupported part of a deck or another storey to hide that approximation.

The contact plane sits 1.4 cm above the physical finished-floor level: the existing procedural
grass surface is 1 cm above that level, leaving 4 mm clearance there. The material uses depth
testing and a small polygon offset, with depth writes disabled. This is a render-only offset.
Contact fades smoothly between 4 cm and 55 cm of body clearance. It fades with camera distance
from 35 to 70 m, so the distance haze remains readable. The material has no second fog blend and
applies neutral darkening without changing the blue-hour lights, sky or material colours.

Static footprints derive from existing measured `dress`, `tree`, `column`, and `cover-*` boxes.
The footprint extends only 13 cm beyond each side of its box. Very large architectural masses
over 24 m² and sub-5 cm thin boxes are excluded. Peak static alpha is 0.16; feet peak at 0.22
before height/distance/edge falloff. Render-only litter, scanned fittings, furniture internal
details and arbitrary walls are not given invented collision or inferred contact receivers.

## Fixed costs and validation

The current Reach layout produces 278 static proxies: 257 at ground, 11 at +3 m, two at +6 m,
and eight at +9 m. Six living bots add twelve foot proxies. The resulting 290 instances submit
580 small triangles in **one extra draw**. A fixed 32-actor capacity allows up to 342 instances
without growing buffers. Matrix, opacity and receiver-bound attributes allocate 28,728 bytes,
plus the shared four-vertex plane and Three object overhead; there is no new texture allocation.
Only the used dynamic tail is uploaded per update; static matrices are retained. The batch
does not cast into the existing shadow map. It retains the software-renderer fallback budget.

`npx tsx --test tests/heron-contact-shadows.test.ts` covers overlapping levels, real Reach bot
spawns, actual stair tread rectangles, floor-edge bounds, smooth height fading, immutable collision
input, bounded dynamic updates, dead/hidden/airborne actors, cleanup and Heron Court isolation.
Actual shader compilation and appearance need the parent task's serial browser validation;
CPU tests and source checks do not establish GPU performance or physical shadow accuracy.

A later GPU-only upgrade could give one or two nearby practical lights constrained shadow maps
after profiling their caster lists and atlas resolution. That would add directional occlusion
and silhouettes that this cheap receiver-bound contact layer cannot supply. It is not part of
this implementation, and it should keep this simple software path available.
