# Continuing ONSITE

Start with [the Claude handoff](docs/development/CLAUDE-HANDOFF.md), then inspect the current
working tree and [latest validation](docs/development/CURRENT-VALIDATION.md).

- Continue the active WWB/Three.js/Rapier game at `index.html` → `src/onsite/main.ts`.
  Preserve its movement, Arsenal, bots and round systems. Do not restart with another prototype.
- ONSITE is a fictional South London estate FPS, bots first. Networking is deferred.
  Preserve the original concept art, Black British character direction and consistent ONSITE UI.
- Use the editable Blender estate and rifle sources in `assets/blender/`. Keep metre scale,
  rendering, collision and navigation separate. `src/onsite/level.ts` owns physical geometry;
  a single Rapier world owns movement. Preserve stacked floors and both stair routes.
- Preserve all existing work and checkpoint before structural edits or scripted Blender rebuilds.
  Builders can replace manually edited collections. Read the Blender workflow before running them.
- Donor imports need individual provenance and notices. Keep `research/reference-clones/` ignored.
  The unlicensed Modern Claudefare mirror is reference-only; no code/assets from it ship here.
- Run relevant checks and verify actual browser behaviour after implementation changes. Distinguish
  concept images, inspection fixtures and input-driven combat evidence. Report real performance;
  software-rendered results are not real-GPU benchmarks or evidence of smooth gameplay.
- Commit/push/merge/deploy only within the user's authorization for the current task. The handoff
  publication does not authorize a later deployment or unrelated merges.

An existing separate Claude prototype is recorded in the handoff. Inspect branches before editing
and do not replace this runtime with that prototype or merge it wholesale.
