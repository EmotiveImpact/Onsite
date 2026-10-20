# Next visual-quality donors

Reviewed 19 October 2026. The source/licence inspection led to an actual scoped
adaptation of Operation Blackout's height/directional fog in
`src/onsite/HeronDepthFog.ts`, with the [MIT integration record](OPERATION-BLACKOUT-NOTICE.md)
and shipped notice, plus the two-asset additive Blender build recorded below.
Claude of Duty remains a study reference; no donor game was run or benchmarked.
The active WWB player, Arsenal, bots, rounds, single Rapier world and layered
collision/navigation remain the base.

The strongest next sources are **Operation Blackout for material response and
atmosphere**, **Claude of Duty for isolated rendering techniques**, and **the
already-present IRONLINE scan assets for near-eye dressing**. None warrants an
engine replacement. Both new clones have actual MIT licence files; their military
presentation is procedurally authored, rather than proprietary Call of Duty art.
Their names and promotional quality claims are not evidence of AAA fidelity.

## Verified checkouts and rights

| Source | Pinned commit | Licence evidence and reuse boundary |
| --- | --- | --- |
| [Operation Blackout](https://github.com/rushindrasinha/operation-blackout) | `51816a061cac321e9fdd3e85f34db1969985dd77` | [Full MIT licence](https://github.com/rushindrasinha/operation-blackout/blob/51816a061cac321e9fdd3e85f34db1969985dd77/LICENSE), © 2026 Rushindra Sinha. Code can be adapted with the notice. Original textures, models and sounds are generated in source; no external game-asset loader was found in the inspected runtime tree. Repository screenshots/video are not proposed assets. |
| [Claude of Duty](https://github.com/mshumer/Claude-of-Duty) | `d9b237b75c9304ab8d9ef4cfa0c3568c7c11a853` | [Full MIT licence](https://github.com/mshumer/Claude-of-Duty/blob/d9b237b75c9304ab8d9ef4cfa0c3568c7c11a853/LICENSE), © 2026 mshumer. README and source describe procedural art/audio; no external game-asset loader was found in the inspected runtime tree. Preserve the licence for any adapted code. |
| [IRONLINE](https://github.com/cktang88/3d-fps) | `130ac2a5c856401ec36e7d35afcfefe40c5801f4` | `package.json` declares ISC, but there is no root project licence/notice. Continue the existing reference-only code boundary. Individual CC0/CC BY assets can be reused only with their own source evidence. Previously imported assets retain their existing notices. |
| [WWB](https://github.com/jeevesh2515/WWB) | `4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1` | [MIT licence](https://github.com/jeevesh2515/WWB/blob/4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1/LICENSE), © 2026 Jeevesh Singale. Already the selectively integrated gameplay foundation. Bundled third-party art is separately licensed. |
| [Open Claudefare mirror](https://github.com/jasonkneen/open-claudefare) | `51bdc6e94e60c60abfae9c23f39851bb01e088fd` | No root project licence or package licence declaration. Personal mirror, not a reuse grant: study only; no code/assets should ship from it. Individual ambientCG references can lead back to original sources, but do not license the mirror. |

New study copies are `research/reference-clones/operation-blackout` and
`research/reference-clones/claude-of-duty`. Existing clones were inspected before
these two were downloaded. All five are outside `public/` and runtime dependencies.
No proprietary game dump, leaked source or commercial asset extraction was used.

## File-level findings and recommended next work

Paths below are relative to the named repository and refer to the pinned revision.

| Priority | Files | Concrete finding and ONSITE adaptation |
| --- | --- | --- |
| 1 — small, eligible code adaptation | Blackout `src/materials/surface.js` | Layers material-specific detail normals and roughness, distance-fades fine detail, and ties dust/grime to orientation. Brick courses, woven fabric and metal tread deliberately receive little/no repeated micro-normal structure to avoid moiré. Adapt only the material response to existing photographed/generated ONSITE maps. Do not apply one noisy grunge layer uniformly to every surface. |
| 2 — small, eligible code adaptation | Blackout `src/lighting/AtmosphereFog.js` | Analytically integrates an exponential height-density layer, with separate directional sun/zenith/ground tint and a quadratic distance term. Keeps the near foreground clear while establishing depth at 40–60 m; useful for Reach's skyline and galleries. The donor replaces global Three.js fog chunks. Implement an ONSITE-scoped material patch with an explicit cache key/cleanup rather than copying that global ownership. Preserve the blue-hour palette. |
| 3 — improve existing lamp presentation | Blackout `src/lighting/LightPools.js`; `src/lighting/Practicals.js` | Instanced projected far-light pools complement a bounded set of nearby real lights. Floors are found by a downward ray, pools fade near the camera to prevent double lighting, and a grazing-angle fade prevents bright floating smears. ONSITE already has floor-aware pools/streaks: adopt these refinements, not a second overlapping pool system. Keep the authoritative floor query. |
| 4 — measured reflection prototype | Claude of Duty `src/render/ssr.js`, `prepass.js`, `materialpatch.js`, `pass.js`, `glsl.js` | Half-resolution SSR uses 28 view-space march steps plus five refinements, border/range confidence fades, previous HDR colour and a velocity buffer. It replaces the material's environment-specular contribution instead of adding a second reflection. This requires linear depth, view normals, history/velocity and material integration; it is **not** a standalone drop-in `EffectComposer` pass. Prototype only the wet-ground mask, with environment fallback and a quality switch; retain the current cheap path. |
| 5 — contact and depth | Claude of Duty `src/render/contact.js`, `gtao.js`, `materialpatch.js` | Short depth-buffer contact rays restore grounding near prop bases; bilateral filtering preserves depth edges. Contact shadows attenuate the direct sun term, whereas AO affects indirect light. Avoid multiplying the whole finished frame into muddy darkness. The donor's sun-specific contact term alone will not solve a blue-hour estate lit chiefly by local lamps. |
| 6 — prevent first-use stalls | Claude of Duty `src/core/prewarm.js`, `tools/baseline.mjs`, `tools/profile.mjs` | Uses `compileAsync` plus controlled subsystem warm-up; transient draws are guarded because they can mutate temporal state. Captures isolate each camera in a fresh page to prevent particles/exposure/history leaking between shots. Adapt these verification ideas when additional shaders are introduced. The donor's hardware performance numbers do not describe ONSITE. |
| Already licensed, incremental option | WWB `src/engine/renderer.ts` | Its half-resolution smoke pass composites premultiplied smoke using scene depth, saving fill rate for soft effects; its grade is a restrained display-space pass after `OutputPass`. Useful if ONSITE adds denser mist/smoke. Keep colour-space/tonemapping ownership singular; do not stack two output transforms or import the full WWB web shell. |

The two new projects target Three.js r180 while ONSITE uses r186.1. Shader chunk
names, normal/depth encoding, colour space, render-target formats and disposal need
explicit adaptation. The MIT grant permits reuse; it does not establish compatibility.
Their custom collision, movement, AI and navigation are out of scope.

**Existing references worth revisiting without copying:** IRONLINE
`src/render/LightPool.js` keeps a fixed physical light count, selects influence
spheres against the frustum and fades outgoing slots; `ShadowCache.js` reuses static
shadow depth with dynamic casters layered over it; `Lod.js` separates render/shadow
budgets and shares original vertex attributes across reduced index buffers. Those
are useful design studies, but static-shadow code relies on renderer internals and
is not a low-risk immediate port. Its `Fsr.js` names a separate AMD MIT source: if
upscaling is later requested, obtain it from the original AMD repository with its
own notice rather than treating IRONLINE's tree as cleared.

The unlicensed mirror's `js/render/PostFX.js` and `shaders.js` illustrate two useful
observations: animated stochastic dither without temporal accumulation shimmers,
and grain need not refresh every render frame. Its `js/render/LightPool.js` and map
separation are design references only. No mirror code or configured service was run.

## Additional open projects screened, not cloned

| Source and reviewed HEAD | Licence evidence | Decision |
| --- | --- | --- |
| [Leonxlnx/claude-of-duty](https://github.com/Leonxlnx/claude-of-duty), `7f8a15ae54dd65e7ce22c80c074f9b1da7daee2f` | [MIT](https://github.com/Leonxlnx/claude-of-duty/blob/7f8a15ae54dd65e7ce22c80c074f9b1da7daee2f/LICENSE), © 2026 Leonxlnx | `src/render/RenderGraph.js` explicitly owns MRT, AO, TAA, bloom and exposure, including separate viewmodel motion history. Valid further rendering reference, but overlaps the two selected clones and would be a larger integration. |
| [Hiraeth010/blackwater](https://github.com/Hiraeth010/blackwater), `80e56105690c963e3263d075ade41afce533d44e` | [MIT](https://github.com/Hiraeth010/blackwater/blob/80e56105690c963e3263d075ade41afce533d44e/LICENSE), © 2026 Hiraeth010; README explicitly includes original procedural assets; third-party notices retained separately | Rain-soaked tactical terminal is a useful mood reference. `app/game/environment.ts` mixes presentation and collision; inspect individual presentation functions if needed, do not replace Reach with the map builder. |
| [StarKnightt/operation-ironhold](https://github.com/StarKnightt/operation-ironhold), `4098330664d66085cb1775c0783597070c32172b` | [MIT](https://github.com/StarKnightt/operation-ironhold/blob/4098330664d66085cb1775c0783597070c32172b/LICENSE), © 2026 StarKnightt | Single-file procedural FPS. Lower integration value than separable rendering modules; keep as a visual reference candidate. |

These repositories are browser prototypes, not substitutes for production art
pipelines. Claude of Duty's own README identifies procedural material richness,
hands, characters and indirect lighting as remaining weaknesses. Keep ONSITE's
licensed detailed rifle, London art direction and Black British character brief.

## Individually checked art already available locally

Two of these IRONLINE derivatives now have an additive Blender/runtime art export
(see the next section); the other three remain candidates. Each source lives at
`public/assets/models/props/<id>/<id>.glb` inside the pinned IRONLINE clone. All have
embedded buffers/textures; the GLB JSON contains no external URI dependency.
Original author metadata was fetched from `https://api.polyhaven.com/info/<id>` on
19 October 2026. [Poly Haven's licence](https://polyhaven.com/license) explicitly
states “Our assets are all licensed as CC0”, covering its HDRIs, textures and models.
That supports these original assets; IRONLINE's README supplies the derivative
trail (simplification/WebP conversion). New imports still need a separate manifest
record linking the original, derivative hash, modifications and ONSITE output hash.

| Candidate | Original author | Local bytes | Intended placement |
| --- | --- | --- | --- |
| [utility_box_01](https://polyhaven.com/a/utility_box_01) | James Ray Cock | 244,540 | Weathered electrical cabinet near core entrances; position within existing wall/service footprints. |
| [utility_box_02](https://polyhaven.com/a/utility_box_02) | James Ray Cock | 266,844 | Variation for shop/service walls, avoiding repeated identical geometry. |
| [water_manhole_cover](https://polyhaven.com/a/water_manhole_cover) | Raunox | 385,564 | Close-view ground detail, render-only and flush with the authoritative paving. |
| [mounted_fluorescent_lights](https://polyhaven.com/a/mounted_fluorescent_lights) | Ulan Cabanilla | 211,204 | Replace selected primitive strip fittings in core/shop dressing, keeping the existing light budget. |
| [modular_industrial_pipes_01](https://polyhaven.com/a/modular_industrial_pipes_01) | Jorge Camacho | 834,920 | Select small pipe sections for ground-floor service walls; the full kit is not a single placement. |

Exact local SHA-256 values, in the table's order:

```text
utility_box_01                b61859ebc3b70219217be5d7930642d81e4463e56fe06f1869905aede9907943
utility_box_02                74cb0d63c218982286048e31d8fa9011eb965d84e3a6e31e1dc854e97680139a
water_manhole_cover           04f305364c9e0ffcff0ba453f02c41de91bf1ab1b84bfcb904f695eb465be0f3
mounted_fluorescent_lights    8852f9cad1005d4a01f29d98e2af4508f93abfec927cc43e09e134d76f4052ad
modular_industrial_pipes_01   1a3afb1fac9b957ae42b4f8da03a5c85002a6b393c1e11b6caac95c6b224b564
```

Keep new pipes/cabinets outside walkable space unless separately authorised
collision work is undertaken. A military character mesh from another project is
not automatically suitable for the Black British hoodie/balaclava direction.
IRONLINE's soldier meshes, mocap and Fab-derived rifle clips each have different
rights: no new character, rig or animation was cleared by this review. Its mixed
decal atlas also combines third-party scans with original project-generated cells;
source any wanted ambientCG decals directly rather than copying the whole atlas.

## Verification and handover

- Existing clone revisions matched `research/SOURCES.json`; both new clones are
  detached at the recorded SHAs and have clean working trees.
- `git check-ignore -v` resolves both new licence files to root `.gitignore:7`.
  `git ls-files research/reference-clones` returned no entries.
- No donor dependencies were installed or donor scripts executed. The later
  two-asset build below uses an original ONSITE import script and changes art only.
- Before a code import, retain its full MIT notice and record source files/revision
  beside the adaptation. Before an art import, write individual provenance; a
  repository's code licence is not blanket permission for bundled art.
- Validate each implemented visual change with matched actual-runtime stills and
  relevant Court/Reach regression checks. Hardware benchmarking remains deferred
  by the owner; software-rendered images can demonstrate appearance, not GPU speed.

## Implemented additive scan export

`scripts/maps/art/import_heron_scanned_detail.py` imports the individually checked
Water Manhole Cover and Mounted Fluorescent Lights derivatives into a separate
Blender 4.3.2 scene. Unmodified donor GLBs are preserved at
`assets/reference/polyhaven-scanned/`, outside the web delivery. Output:

- `assets/blender/heron-reach/scanned-detail.blend` and
  `scanned-detail-manifest.json`: editable geometry, seven packed original image
  maps, source/output hashes, author/licence evidence and individual bounds.
- `public/models/heron-reach/heron-reach-scanned.glb`: **499,580 bytes, 2,484
  authored triangles**, three embedded PBR materials. Meshopt compression and WebP
  require the existing GLTFLoader/MeshoptDecoder path; apply an identity root transform.
- `public/licenses/polyhaven-scanned-notice.md`: shipped individual asset notices.

Manholes are centred at map `(108,45)` and `(92,61)`, each 0.691 m in diameter,
with the frame embedded below ground and highest relief at y=0.0185 m. Both have
existing ground beneath their full footprint, no above-ground collision overlap
and more than 2 m clearance from ground-floor door centres.

The fluorescent source was visually inspected and found to contain **seven
separate variants laid out side by side**. The builder extracts the first complete
162-triangle strip including housing and glass, then places two instances at map
`(106.5,48.9)` and `(115.5,48.9)`. Each is 0.912 m long, 0.040 m wide and spans
y=2.71486–2.75 m. The original emissive texture runs at strength 1.4; no additional
light is created. Load with embedded materials intact. Once the new model has
loaded, hide only `E-shop/interior / hr_shop_fitting` and
`E-shop/interior / hr_shop_strip` in the existing shop-detail scene to prevent
overlap. Preserve the Corner's backdrop node and all other shops.

Two additional copies now sit beneath the northern upper-gallery soffits, centred
at map `(52,38.1)` and `(61,38.1)`, y=5.77486–5.81 m. Both have a complete y3
gallery floor beneath them and a slab whose physical **and rendered** underside
is y5.8. Their upper 10 mm is embedded into that slab; minimum head clearance is
2.77486 m. The initial x60 proposal straddled the S2 wall at x59.8–60, so the second
fixture moves to the verified adjacent x61 position. The scene therefore contains
six objects: two covers, two Corner strips and two gallery strips. Runtime gallery
light anchors are owned by the parent integration and are not exported in this GLB.

The builder checks dimensions, placement clearance, texture references, packed
images, output size and triangle budget. Source-oriented and authored Cycles
inspection renders were checked separately from runtime evidence. It also caught
and fixes a Blender 4.3 edge case: repacking already embedded WebP images clears
their packed bytes, so the source bytes are retained and decoded before export.
The final GLB embeds all seven valid images. No collision, navigation or gameplay
module was changed; runtime integration and browser checks belong to the parent
visual implementation pass.
