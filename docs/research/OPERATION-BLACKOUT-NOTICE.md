# Operation Blackout: scoped Heron Reach depth fog

This is a small source-code adaptation from
[rushindrasinha/operation-blackout](https://github.com/rushindrasinha/operation-blackout),
pinned to commit `51816a061cac321e9fdd3e85f34db1969985dd77`.
Only the height/directional fog technique in `src/lighting/AtmosphereFog.js` is adapted.
No donor art, audio, textures, game systems, other rendering passes or dependencies are imported.
The optional research checkout stays in the gitignored `research/reference-clones/` directory.

## Source and hashes

| File | SHA-256 |
| --- | --- |
| Donor `src/lighting/AtmosphereFog.js` | `6dc70c6b8463478b6203a4ab28bd36138c7daedb2725a7ed017210179f521320` |
| Donor `LICENSE` | `9ee5b6f9f4d5d8c6bcc9c56bba2830fd076690624d5adaf25fefd102f25d275c` |
| Adapted `src/onsite/HeronDepthFog.ts` | `67c05aa97abf84aa52dfe13f77e2fb78ce7311c516d3ff23f36dafc7bf833f08` |

The exact donor MIT notice is reproduced below and in
[`public/licenses/OPERATION-BLACKOUT-MIT.txt`](../../public/licenses/OPERATION-BLACKOUT-MIT.txt),
so Vite's public-directory copy includes it in production distributions. Retain that notice
with this adaptation. The source header records the author, upstream file and pinned revision.

## Integration and tuning

The entry point is [`installHeronDepthFog`](../../src/onsite/HeronDepthFog.ts).
Call it on the **Heron Reach world scene**, after its art assets, sky and material hooks finish
loading, including `applyWetGround`. Keep the viewmodel scene and other maps separate:

```ts
import {installHeronDepthFog} from './HeronDepthFog'

// Inside the existing Heron Reach branch, after awaited art/material setup:
installHeronDepthFog(this.scene)
```

The installer returns the number of newly wrapped material hooks. It is idempotent, including
materials shared by several objects. Call it again after adding late-loading stock materials.
Existing `onBeforeCompile` hooks execute first, and existing custom shader-cache keys still
evaluate dynamically. The default Three cache key keeps the identity of the previous hook;
the new fog suffix prevents reuse of an unpatched program. No global `ShaderChunk` is changed.

Both `scene.fog.color` and the `FogExp2` density remain live controls. Current tuning assumes
the existing Reach colour `#687b8d`, density `0.007`, metre units and Y-up world coordinates.
`HERON_DEPTH_FOG` holds the fixed layer coefficients used by both the CPU checks and GLSL.
Changing those coefficients requires rebuilding; changing the scene's fog density/colour does not.
The subdued warm direction matches the sky dome's existing azimuth of 2.4 radians. Its maximum
warm blend is 0.32, with relative colour `(1.40, 1.12, 0.90)`, retaining blue-hour air. The donor's
much brighter `(4.6, 3.1, 1.9)` sunrise-style multipliers are not used.

## Adaptation and limits

- Retained donor techniques: reconstruct world position from `mvPosition` and inverse view
  rotation; combine quadratic aerial extinction with a weaker linear ground layer; integrate
  exponential density along the viewing ray; evaluate base, downward, zenith and warm colour lobes.
- Replaced the donor's global chunk mutation/rebaking with per-material composition. The world
  reconstruction works after stock mesh skinning/instancing and for points/sprite billboarding;
  it needs no additional texture, framebuffer, draw call or render pass.
- Kept Three.js 0.186.1's original linear `Fog` chunk unchanged. `fog:false` materials, including
  the sky, are skipped. Custom `ShaderMaterial`/`RawShaderMaterial` programs keep their own fog.
  A prior hook that removes any of the four expected stock fog includes is left intact.
- Added a stable series around horizontal rays and bounded exponent inputs to ±16. This avoids
  division cancellation and extreme downward-ray overflow in Three's default `highp` shaders.
  The CPU helper uses `expm1` outside the series for an accurate reference. Inputs are finite,
  metre-scale ray lengths/heights and non-negative density; the function clamps negative length
  and density to zero. It is not intended as an API for arbitrary non-finite numbers.
- Retained the donor's camera-height floors and aerial-integral bounds. These are artistic
  approximations to a physical density integral: extremely high/low viewpoints keep readable
  haze rather than exact atmospheric transport. Fog also applies inside buildings, as stock
  scene fog did; there is no room/roof masking, local light scattering or volumetric shadow.
- Lowered the donor ground coefficient from `0.26` to `0.18` so the 10 m near-field target
  also holds when crouching on the B1 floor. Raising scene density can invalidate that target.
- The view-matrix reconstruction assumes an unscaled camera transform, matching the existing
  runtime. The wrapper is for stock WebGLRenderer shaders, not WebGPU/TSL. Do not share the
  patched material instances with another map, or overwrite their hooks after installation.
  Material clones need installation after cloning (Three does not copy these hooks).

## Verification

`npx tsx --test tests/heron-depth-fog.test.ts` passes five tests: near visibility including B1;
independent numerical density integration; continuity/finite horizontal and vertical rays;
composition with actual wet-ground hooks and shader-cache identity; and stock meshes,
instances, points and sprites with untouched linear fog/global chunks. `npm run typecheck` passes.
These are CPU/source checks; the parent integration must still validate actual shader compilation
and appearance in a browser, sequentially with the other software-rendered capture jobs.
No real-GPU performance, screenshot parity or actual GLSL compilation is asserted by these tests.

CPU reference values at eye height 1.75 m, horizontal ray and density 0.007:

| Distance | Fog blend |
| --- | ---: |
| 10 m | 1.249% |
| 40 m | 7.356% |
| 60 m | 13.128% |
| 150 m | 47.570% |
| 300 m | 89.679% |
| 470 m | 98.500% (cap) |

A 10 m ray from crouched B1 eye height −1.96 m towards its −3 m floor blends 1.913% haze.

## Exact upstream notice

```text
MIT License

Copyright (c) 2026 Rushindra Sinha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
