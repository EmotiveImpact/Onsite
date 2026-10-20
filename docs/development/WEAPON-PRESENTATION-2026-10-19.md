# Rifle reload presentation — 19 October 2026

The existing licensed IRONLINE rifle remains driven by WWB Arsenal. This pass changes only the original procedural presentation in `src/onsite/DonorRifle.ts`; it adds no model, material, motion clip, weapon mechanic, or donor dependency.

## Observed defect and correction

At baseline `483cc0ae14a9e498b757fe15e1084a86829c27ec`, invoking reload phase 0 or 1 applied the analytic elbow solution immediately, although its pole differs from the artist's idle pose. On the shipped GLB, the right forearm rotated approximately 28.2 degrees and `BoneTwist_03R` moved 77.4 mm relative to idle. Returning to ordinary idle then reversed the jump. The hand target alone did not expose this defect because the wrist stayed in place.

The solved bone controls now blend smoothly into and out of the authored pose. Exact endpoints restore the authored transforms. The measured maximum bone displacement from idle is zero at phases 0 and 1, and below 0.00003 mm at phases 0.00001 and 0.99999.

The magazine keeps its existing extraction, pause, insertion and seating landmarks (18%, 40%, 52%, 72%) and full travel, but eases into both stops. The support hand stays on the fully seated magazine until 78%, then returns to the foregrip by 95%. The charging handle retains its 78–90% window and travel with eased endpoints. The magazine's authored rotation is restored rather than assuming it was identity.

WWB reload duration, ammunition updates, firing behaviour, recoil, root choreography and ADS coordinates are unchanged. Existing screenshots did not isolate an incorrect roughness response, so this pass makes no speculative material adjustment.

## Validation

`tests/donor-rifle-pose.test.ts` loads the actual shipped GLB, retaining its geometry, skin weights, inverse bind matrices, bones and sockets. Only texture image decoding is stubbed for Node; these checks provide pose evidence, not rendered appearance evidence.

Asset SHA-256: `4f192aa8377e203c07c16eb068eb53d47ede717a92e452fba57fd82424a8d798` (`public/models/onsite-carbine.glb`).

- Four tests passed with `node_modules/.bin/tsx --test tests/donor-rifle-pose.test.ts`.
- A 241-sample reload sweep checks finite bone transforms and sampled CPU-skinned arm vertices, including start/end continuity and a maximum 25 mm displacement per sample.
- Twelve extraction, insertion and seated-hold phases check support-hand/socket agreement within 1 mm, trigger-hand stability and the separate forearm/wrist branch junction. Both hip and tipped rifle frames run beneath a translated and rotated camera.
- Magazine and charging-handle checks verify bounded travel, seating and reduced speed at the stops. Reverse seeking and interrupted reloads must restore the exact authored pose without accumulated drift.
- The authored rear iron sight remains centered in ADS to a projected tolerance of 0.00001.
- `npm run typecheck` passed. No browser was launched for this subtask; the main task owns presentation-fixture and encounter verification.

No runtime integration change is required. The new test can be added to the repository test command or invoked directly. Existing presentation-harness reload phases 35% and 55% remain inside the fully constrained magazine-grip interval.
