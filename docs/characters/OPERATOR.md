# Original ONSITE operator and kit

19 October 2026. This replaces the earlier disconnected placeholder limbs with an
original, editable Blender character and weighted anatomical skeleton. It is a
playable character-art foundation, not a scanned or production-finished character.
The original `assets/blender/hooded-opponent.blend` and GLB remain untouched.

## Art and provenance

- Source: `assets/blender/characters/onsite-operator.blend`, Blender 4.3.2.
- Generator: `scripts/characters/build_operator.py`.
- Runtime: `public/models/onsite-operator.glb`; exact payload hash, byte size and
  triangle counts are in the adjacent `onsite-operator.json`.
- All clothing, gloves, trainers, balaclava, exposed brown skin, eyes, compact
  carbine prop and skeleton are original ONSITE authoring. No donor character,
  skeleton, photograph, branded trainer, motion clip or font is imported.
- Two original 128 × 128 woven-cotton colour/normal tiles are generated from
  deterministic weave/noise mathematics. Editable PNGs live in
  `assets/textures/operators/`; the GLB embeds both. Their hashes and source are
  recorded in the JSON. No external texture requests are needed.

The clothing is black throughout. The eye opening retains the project's Black
British character direction. Actual selectable meshes provide hood up/down and
court, runner or high-top trainers. The black balaclava and gloves stay fixed.
These choices are cosmetic; they do not change hitboxes, speed, damage or armour.

## Geometry and animation contract

Metre scale, soles at zero, raised hood at 1.75 m. Blender faces -Y; the GLB faces
+Z. `createOperatorVisual` rotates it by PI to match the existing WWB -Z forward
convention. Twenty original bones include hip, spine, shoulder, elbow, wrist,
knee and ankle pivots, plus weapon and muzzle sockets. The leg/seat surface is a
single smoothed, weighted garment, avoiding overlapping hip and knee shells.

There is one glTF skin and six variant mesh groups. Only the body, one hood and
one trainer pair are visible: ten material draws, seven unique materials. The
complete file contains 16,714 triangles including all hidden alternatives;
the default raised-hood/court-trainer kit displays 13,874 triangles, and the
largest raised-hood/runner kit 14,818. Blender exports no animation clips.

`src/onsite/OperatorVisual.ts` supplies original procedural idle breathing,
velocity-driven walk/strafe, aiming, recoil, hit reaction and a resettable death
pose. Each bot uses `SkeletonUtils.clone`, so bones and visibility are private
while geometry/materials are shared. The gun and both hands follow the upper
body together; the muzzle is the authored barrel socket. The existing WWB bot
capsule, navigation, hitscan/damage logic and movement ownership remain intact.

This is an analytic pose system, not motion capture: there is no foot planting
IK, cloth simulation, facial animation, articulated fingers or ragdoll. Those
remain later character-production work. Do not describe these assets as AAA.

## Kit preview

`KitPreview` renders the same GLB in the existing menu. It is created lazily on
opening the operator panel, uses a resize observer, supports dragging to rotate,
and cancels its animation frame when the panel/menu closes. It owns no gameplay
loop or physics state. `dispose()` releases its resources. The API is:

```ts
const preview = new KitPreview(container)
await preview.ready
preview.setKit({hood: 'up', trainers: 'court'})
preview.setActive(true) // false when closed or gameplay starts
```

## Rebuild and validation

```sh
blender -b --python-exit-code 1 --python scripts/characters/build_operator.py
npx tsx --test tests/operator-assets.test.ts tests/wwb-navigation.test.ts tests/heron-reach.test.ts
npm run typecheck
```

All 29 targeted asset/navigation checks and typecheck passed during development.
The three new actual-GLB tests cover scale, provenance, skeleton and geometry
budget; independent actor bones/kit visibility and reset; and the muzzle following
aim/recoil without translating its actor. Navigation fixtures now load the real
rig, omitting only browser image decoding, and retain every previous route and
collision assertion. Full runtime browser checks belong to the parent delivery;
Blender source renders alone do not establish in-game appearance or performance.
