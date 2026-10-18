# Local reference repositories

Pinned URLs, commits and checkout-relative paths are in [SOURCES.json](SOURCES.json). Both full trees are intentionally ignored by the root `.gitignore`; only these notes and the manifest belong in ONSITE history. Neither tree is a submodule, a runtime dependency or part of `public/`. No source or asset from these two repositories has been imported into the playable.

## IRONLINE

https://github.com/cktang88/3d-fps at `130ac2a5c856401ec36e7d35afcfefe40c5801f4`, locally `research/reference-clones/ironline`.

The package declares ISC, but no root project licence/notice was found. That declaration does not clear bundled models, textures, sounds, fonts or animations. Further code and per-asset review is required before reuse. This clone was made without hardlinks from the previously fetched study copy, with its origin set to the upstream URL.

Useful references: `docs/screenshots/catwalk.jpg`, `docs/screenshots/action.jpg`, `docs/FP_FRAMING.md` and `docs/QUALITY_BAR.md`. Industrial beams, railings, inset facades and elevated routes suggest ways to add depth to ONSITE's London estate. Weapon framing notes discuss a separate viewmodel field of view and keeping sights readable without obscuring the centre. These are visual/design observations, not permission to copy assets or code. The package uses Three.js ^0.186.1 and Rapier ^0.21.0, and lists Recast navigation packages; evaluate navigation independently for stacked floors before considering adoption.

## Open Claudefare

https://github.com/jasonkneen/open-claudefare at `51bdc6e94e60c60abfae9c23f39851bb01e088fd`, locally `research/reference-clones/open-claudefare`.

No root project licence or package licence declaration was found. Its README calls this a personal local mirror of modernclaudefare.com, not a redistribution package. Treat game code, models, audio and other bundled content as uncleared. `assets/tex/LICENSE.txt` claims particular ambientCG sets are CC0 and records asset IDs, resolutions and map roles; this is a useful provenance trail to verify against original sources, not a blanket licence for the mirror. No mirror scripts were executed and no dependencies installed.

Useful study findings: map directories separate geometry, collision, navigation, materials, ambience and spawn modules. This reinforces ONSITE's existing separation of render detail from collision/navigation. The texture inventory distinguishes normal-map conventions and photographic versus procedural surfaces. README documents a deployment confirmation flow and desktop controls. It also says remote multiplayer, analytics and other production endpoints remain configured: do not launch or copy those integrations into ONSITE. Its structural/HTTP tests are not evidence of gameplay correctness.

## Boundaries and verification

WWB remains the preferred selectively adapted gameplay foundation; see [prototype provenance](../docs/development/PROVENANCE.md). The London direction, original assets and bots-first milestone are unchanged. Do not copy these study trees to `public/`, add dependency aliases to them, force-add them, or stage them recursively. Any later reuse needs a specific source, pinned revision, licence and retained notices.

Verify locally with `git -C <localPath> rev-parse HEAD`, `git -C <localPath> status --short`, `git check-ignore -v <localPath>/README.md` and `git ls-files research/reference-clones`. The last command must produce no entries. Initial sizes were approximately 245 MB (IRONLINE) and 226 MB (mirror), with 29 GB free after cloning. Both checkouts were clean; no network or disk block remained. Clone files are intentionally absent from a fresh ONSITE checkout.

## WWB integration update

A third ignored clone, `research/reference-clones/wwb`, is pinned to `4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1`. Actual gameplay modules are now integrated in `src/wwb`; read [DONOR-MAP.md](../docs/development/DONOR-MAP.md). Two CC0 Poly Haven props have separately recorded provenance. This changes no rights assumptions for IRONLINE or the unlicensed mirror.
