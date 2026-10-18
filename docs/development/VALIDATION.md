# Validation history

For the current WWB integration see [CURRENT-VALIDATION.md](CURRENT-VALIDATION.md). The record below is the preserved initial prototype validation.

# Local validation — 18 October 2026

- `npm test`: 10 simulation tests passed (collision, stairs, jumping, movement normalization/command sequence, cover and sight, reload, victory/reset, defeat/timeout, multilevel graph, fixed clock).
- `npm run build`: passed. Vite warns about the large JavaScript chunk: approximately 4.99 MB uncompressed / 1.84 MB gzip, including Rapier. Total dist is approximately 8.1 MB. Further splitting/loading optimization remains.
- `ONSITE_URL=http://127.0.0.1:4173 npm run test:browser`: all 11 interaction checks passed against the production preview, with no page errors or failed requests. Real pointer lock, WASD, jump, fire, reload, pause/resume, mouse-aimed bot elimination, capture/victory, restart and physical stair traversal were exercised. No teleport or damage hooks were used.
- A previous development-server browser run completed the same interactions but failed its final request assertion on four Vite dependency requests. Their failure reasons were not captured in that run; request diagnostics now record reasons. Production-preview verification avoids the development dependency pipeline and passed; the original failure is not attributed to a proven cause.
- Software rendering profile at 960×600, reduced pixel ratio and shadows disabled: mean frame time **323.69 ms** over 298 samples, 53 draw calls, 10,188 triangles at the recorded view. This is slow (about 3.1 FPS) and is not an acceptable performance target. The cloud uses SwiftShader; no hardware-GPU frame rate has been verified. Frame-time measurement includes pauses/screenshots and is not an isolated render benchmark. A controlled GPU profile and optimization remain necessary.
- A subsequent load-readiness fix waits for all 18 texture maps as well as models. The final build passed; the full interaction run above preceded that one-line readiness fix. The separate final Chromium load smoke check passed (`ready: true`, no page errors).

Browser screenshots/report are in ignored `test-results/`; these are actual prototype renders, not generated concepts. Art remains a blockout with original procedural materials and Blender props. Full character rigs, weapon animation and detailed estate dressing remain unfinished. Source concepts were preserved.

## Study clones

Both requested checkouts exist and were clean at verification. Exact revisions, paths and licence caveats are in [SOURCES.json](../../research/SOURCES.json). `git check-ignore -v` resolves both trees to root `.gitignore` line 7; `git ls-files research/reference-clones` returns nothing. Only the manifest and study notes are staged under research. No reference content is imported into runtime code or present in the build.

No merge, push or deployment was performed. The playable remains local working-tree work.
