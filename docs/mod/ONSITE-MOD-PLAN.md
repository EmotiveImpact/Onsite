# Onsite Mod: build plan for Codex

Written 22 October 2026 for Edem (owner). Hand this whole file to Codex.

## 1. What Edem wants

A private, non-commercial mod build of Onsite that:

1. Runs on Edem's Mac (Mac mini, Apple silicon).
2. Uses Onsite's own estate maps: **Heron Court** first, then **Heron Reach**.
3. Gives the player a **selection of guns** taken from two Garry's Mod add-ons:
   - **ArcCW-MW2**: https://github.com/Fesiug/ArcCW-MW2 (commit `8a417b7e99052e006536da66536e241db867f1f4`), 52 weapon files, MW2 guns.
   - **ARC9 Modern Warfare Classic**: https://github.com/PalindroneV2/ARC9_ModernWarfareClassic (commit `867659cd1bb6f1fc557af554cb76e93278462ae4`), 99 weapon files covering CoD4, MW2 and MW3 guns.
4. Plays like MW2: pick a loadout, swap between primary and secondary, aim down sights, reload, fight bots.

This is a trial. If Edem likes it, proper development follows later.

## 2. Ground rules (do not skip)

- Work in a **new private repo** (suggested name `onsite-mod`). Never commit the gun-pack files to the main Onsite repo (https://github.com/EmotiveImpact/Onsite) and never deploy this build to the public site (https://onsite-azure.vercel.app).
- The gun packs have **no licence** and their art and sounds come from Activision's games. Keep the build private and personal. Do not publish, share builds publicly, or sell.
- Do not fetch the packs into the build at runtime from GitHub. Convert them once, locally, and keep the converted files in the private repo (Git LFS for large binaries).
- Keep a `SOURCES.md` listing each converted gun, the pack it came from, the pack commit and the original file paths.

## 3. Which engine

Two candidates were looked at. **Recommendation: Track A.**

### Track A (recommended): fork Onsite's own browser engine

- Onsite is Three.js + Rapier + TypeScript, entry `index.html` → `src/onsite/main.ts`. It already has movement, an `Arsenal` weapon system (`src/wwb/game/weapons.ts`, defs in `src/wwb/game/config.ts`), bots (`src/wwb/game/bots.ts`), layered navigation, rounds, a front-end menu and both maps.
- It already runs on a Mac in Safari or Chrome. For a desktop app feel, wrap it with **Tauri** later (small, native on macOS).
- Guns arrive as glTF + WAV, which Three.js loads directly.
- Fastest route to "Heron Court with a full gun selection".

### Track B (not recommended for the trial): fork iw4L

- iw4L (https://github.com/vladtrc/iw4L, Apache 2.0) is a Rust/Bevy re-implementation of the MW2 engine. It builds and runs on Apple silicon (its `docs/BUILD.md` confirms Metal).
- But almost everything it shows comes from an installed copy of MW2: maps, weapons, match rules (GSC scripts), menus, shaders, player models. Without MW2 you would need to write new loaders for maps, guns, materials and UI, plus new match scripts. That is months, not weeks.
- Worth reading for ideas only: `docs/BOTS.md` (bot rules), `docs/SIM-STEP.md` (one shared game step for host, prediction and replay).

The rest of this plan is Track A.

## 4. Phase 1: set up the private fork

1. Create private repo `onsite-mod` from a copy of Onsite `main`. Keep Onsite's history so later Onsite map work can be merged in.
2. Node 24 is required (`npm test` uses a Node 24 flag). Run `npm install`, `npm test`, `npm run typecheck`, `npm run build` and confirm all pass before changing anything.
3. Read Onsite's `CLAUDE.md`, `AGENTS.md` and `docs/development/CLAUDE-HANDOFF.md` first. Preserve movement, bots, rounds, stacked floors and both stair routes.
4. Load both maps locally: `npm run dev`, then `/?map=heron-reach` for Heron Reach. Heron Court is the default.

## 5. Phase 2: convert the guns

Both packs are Source engine (Garry's Mod) content:

| Pack content | Format | Convert to |
| --- | --- | --- |
| Viewmodels `models/weapons/...c_*.mdl` (+ `.vvd`, `.vtx`, `.phy`) | Source model with animation sequences | glTF `.glb` with named animation clips |
| Textures `materials/...*.vtf` + `*.vmt` | Valve texture + material script | PNG or KTX2, PBR material |
| Sounds `sound/weapons/...` | WAV / MP3 | keep WAV, or OGG |
| Weapon stats `lua/weapons/*.lua` | Lua `SWEP` tables | `weapons.json` |

### Tools

- **Blender + SourceIO add-on** (https://github.com/REDxEYE/SourceIO) imports `.mdl` with sequences and `.vtf` textures, and runs on macOS and Linux. Check it supports the Blender version you use; fall back to Blender 4.x if needed.
- Alternative on Windows: **Crowbar** to decompile `.mdl` to SMD/QC, then **Blender Source Tools** to import.
- Script the whole conversion in Blender Python (`blender -b --python convert_gun.py -- <weapon>`) so it can be rerun per gun. Export `.glb` with animations, Y-up, metres.

### Per gun

1. Read the weapon's Lua file. Record: `ViewModel`, `WorldModel`, `Damage`, `DamageMin`, `Range` (ArcCW: game units × 0.025 = metres), `Delay` or RPM, `Primary.ClipSize`, `Recoil`, `RecoilSide`, `RecoilRise`, `AccuracyMOA`, `HipDispersion`, `MoveDispersion`, `ShootSound`, `ShootSoundSilenced`, and the `SWEP.Animations` table (each entry's `Source` sequence name and `Time`).
2. Import the viewmodel `.mdl` and keep these clips at minimum: `idle`, `fire` (and `fire_iron` if present), `reload`, `reload_empty`, `draw`, `holster`, `sprint`. Rename to a fixed set so the game code can rely on them.
3. Find the muzzle and shell-eject attachment points from the model and export them as empty nodes named `MuzzleSocket` and `EjectionPort` (the names Onsite's rifle already uses).
4. **Hands**: Garry's Mod `c_` viewmodels expect the player's hands to be merged at runtime (the "c_arms" system), so most guns ship without arms. Either keep Onsite's existing first-person arms (`public/models/onsite-carbine.glb`, credited in `public/licenses/DONOR-ASSETS.md`) and retarget them onto each gun's hand bones, or bake one shared hands mesh onto every gun's skeleton during conversion. Prove this on one gun before converting the rest.
5. Convert `.vmt` to PBR: `$basetexture` → base colour, `$bumpmap` → normal (Source normals may need the green channel flipped), `$phongexponent` / `$envmapmask` → roughness and metalness estimates. Darken or tint to suit Onsite's rainy dusk lighting.
6. Write the result to `public/mod/guns/<id>/` (`<id>.glb`, textures, `fire.wav`, `reload.wav` etc.) and add an entry to `public/mod/guns/weapons.json`.

### Starter set (prove the pipeline, then add more)

| Slot | Gun | Source file |
| --- | --- | --- |
| Assault rifle | M4A1 | ArcCW-MW2 `arccw_mw2_m4.lua` |
| Assault rifle | ACR | ArcCW-MW2 `arccw_mw2_acr.lua` |
| SMG | UMP45 | ArcCW-MW2 `arccw_mw2_ump45.lua` |
| SMG | MP5K | ArcCW-MW2 `arccw_mw2_mp5k.lua` |
| Shotgun | SPAS-12 | ArcCW-MW2 `arccw_mw2_spas12.lua` |
| Sniper | Intervention | ArcCW-MW2 `arccw_mw2_intervention.lua` |
| Pistol | USP .45 | ArcCW-MW2 `arccw_mw2_usp.lua` |
| Pistol | Desert Eagle | ArcCW-MW2 `arccw_mw2_deagle.lua` |

Then extend with the ARC9 pack (files are named `arc9_cod4e_*`, `arc9_mw2e_*`, `arc9_mw3e_*`), for example CoD4 AK-47, MP5 and M40A3, and MW3 MP7, ACR and FMG9. ARC9 uses a different weapon base from ArcCW, so read its base files under `lua/` to map its stat names before converting.

## 6. Phase 3: data-driven weapons in the game

Today `WeaponId` is a fixed union of `'rifle' | 'shotgun' | 'rocket'` and viewmodels are hard-wired.

1. Replace the fixed union with a registry loaded from `weapons.json`. Each entry: `id`, `name`, `class` (`ar`, `smg`, `shotgun`, `sniper`, `lmg`, `pistol`), `slot` (`primary` or `secondary`), `model`, `sounds`, and gameplay numbers mapped onto Onsite's existing `WeaponDef` fields (`damage`, `interval`, `auto`, `mag`, `reserveStart`, `reserveMax`, `reload`, `perShell`, `spread`, `spreadAds`, `bloom`, `bloomMax`, `recoilPitch`, `recoilYaw`, `punch`, `shake`, `range`, `adsFov`, `headMultiplier`, `pellets`).
2. Map the Lua stats with simple, documented formulas (for example `spread = AccuracyMOA / 60` degrees converted to radians; damage falls off from `Damage` to `DamageMin` across `Range`). Put the formulas in one file so they can be tuned.
3. Viewmodels: load each `.glb` and drive its clips with a `THREE.AnimationMixer` from the Arsenal's existing state (fire, reload, reload empty, draw, holster, sprint). Keep Onsite's existing springs for sway, bob and recoil on top.
4. Aim down sights: derive the ADS offset per gun from its sight nodes, or store a hand-tuned `ads` offset in `weapons.json`.
5. Sounds: route through Onsite's existing `Audio` class with per-gun keys.
6. Keep the current ONS-01 carbine as a fallback gun so the game still works if a converted gun fails to load.

## 7. Phase 4: loadout and swapping

1. Add a **Loadout** panel to the front-end menu (`src/onsite/FrontEnd.ts`, next to the existing kit panel): choose one primary and one secondary. Save the choice in the existing profile (`src/onsite/profile.ts`).
2. In game: `1` primary, `2` secondary, mouse wheel cycles, `Q` swaps to the last weapon (the Arsenal already has `select`, `cycle` and `quickSwitch`; `Input` already maps `slot1` to `slot3`). Wire those inputs in `src/onsite/main.ts`, which currently passes none of them.
3. HUD: show the current gun's name instead of the fixed `ONS-01 / CARBINE` label in `main.ts`.
4. Bots: give each bot a gun from the registry and use its damage, fire rate and sound, so fights sound and feel right.

## 8. Phase 5: run it on the Mac

1. `npm run dev` on the Mac mini and open the local address in Safari or Chrome.
2. Optional: wrap with Tauri for a double-click Mac app.
3. Check smoothness on the Mac's real GPU and report the frame rate honestly. Software-rendered results in the cloud do not count.

## 9. Done means

- Heron Court loads with the starter set of 8 guns, loadout picked from the menu, `1`/`2`/wheel/`Q` swapping, aim, reload and firing animations playing, correct sounds, bots using guns.
- Heron Reach works the same.
- `npm test`, `npm run typecheck` and `npm run build` pass.
- `SOURCES.md` lists every converted gun with pack, commit and original paths.
- Nothing from the gun packs is in the main Onsite repo or on the public site.

## 10. Known risks

- **Hands on Garry's Mod viewmodels** are the hardest part. Prove one gun end to end before doing the rest.
- SourceIO may lag behind the newest Blender. Pin a Blender version that works.
- Source animations are authored at 30 fps with their own timings; the Lua `Time` values tell you the intended speed.
- Converted texture sets add up quickly; Onsite is already at about 600 MB of texture memory. Use KTX2 and 1K textures for guns.
