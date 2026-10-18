# Before WWB runtime integration

Recoverable archive: `/workspace/checkpoints/onsite-before-wwb-20261018.tar.gz`.
SHA-256: `ac2bdb831083819094530885b7d1cc6addf9674925fdb880b468cd88ec1f3d44`.

Created before structural edits, including Git metadata/index, all source, original art, Blender files, textures, documentation and both existing reference clones. Excludes reproducible node_modules/dist and ignored test-results. Archive listing verified with tar; list alongside archive. Kept outside the checkout so it cannot enter the game bundle.

Restore safely to a separate directory: `mkdir -p /workspace/onsite-restored` then `tar -xzf /workspace/checkpoints/onsite-before-wwb-20261018.tar.gz -C /workspace/onsite-restored`. Run `npm ci` there. Do not extract over ongoing work. The archive is local and not pushed; retain it with this cloud session.

At checkpoint, runtime was an original JavaScript Simulation/WorldView prototype with selected WWB-inspired helpers, not WWB's actual complete runtime. The old files and tests remain preserved during integration.
