# ONSITE

A bots-first Three.js first-person shooter prototype set on a fictional London estate.

## Run the playable

Requires Node.js 24 and a desktop WebGL2 browser.

```sh
npm ci
npm run dev
```

Open the local URL printed by Vite, then **Enter Estate**. WASD / arrows move, mouse looks, left click fires, Shift sprints, Space jumps, R reloads and Escape pauses. Eliminate three opponents, then hold the central court for 2.5 seconds. Both stairs lead to the connected upper gallery. Restart is available from pause or the end screen.

```sh
npm test
npm run build
npm run test:browser  # local server running; Chromium at /usr/bin/chromium
```

Set `CHROMIUM_PATH` and `ONSITE_URL` if needed. Browser screenshots and reports go to ignored `test-results/`.

The active game uses actual MIT-licensed WWB Player, Arsenal, Bot, Physics, Input, fixed-step loop, effects and round-rule modules, integrated through an ONSITE encounter wrapper. It has three opponents, a 36×30 m London courtyard, rooms, two dogleg stairs and a continuous upper gallery at 3 m. RMB aims, C crouches/slides. No networking. [Donor mapping](docs/development/DONOR-MAP.md) · [As-built layout](docs/development/evidence/as-built.svg) · [Checkpoint / restore](docs/development/CHECKPOINT.md) · [Current handoff](docs/development/HANDOFF.md).

The original prototype remains accessible locally at `/legacy.html`, with its source, tests, original art, Blender assets and procedural textures preserved. `npm run typecheck` checks the current TypeScript integration; `npm test` runs legacy regression tests plus physical WWB navigation tests. Browser verification: build, start `npm run preview -- --port 4173`, then `ONSITE_URL=http://127.0.0.1:4173 npm run test:browser`. Install Chromium and `npx playwright install ffmpeg` for capture.

`npm run evidence:layout` derives the plan from actual collision solids. `npm run evidence:route` uses the development server and a clearly labelled automated physical traversal fixture with bots disabled; its screenshots must not be described as human-played combat. The main browser test records real pointer-lock input combat separately.

Rebuild original visual assets with `blender -b --python scripts/build-assets.py`; regenerate original procedural maps with `python3 scripts/build-materials.py` (NumPy/Pillow). `python3 scripts/fetch-pbr.py` fetches the separately inventoried CC0 maps. Editable Blender sources remain separate from runtime GLBs.

## Visual direction

![ONSITE concept art showing an estate courtyard, elevated walkway, and football court with a consistent white and amber HUD](docs/concepts/onsite-london-fps.png)

[View the full-size concept image](docs/concepts/onsite-london-fps.png).

Visual direction: wet concrete, brick tower blocks, blue-hour skies, and warm street lighting. The ONSITE name, minimap, score, health, ammo, and amber objective markers stay consistent across all three views.

The image above is the original concept art, not a screenshot of the current playable. The galleries below remain preserved as visual references.

## More gameplay concepts

[View all 10 additional ONSITE screens](docs/concepts/GALLERY.md) — estate entrance, stairwell, rooftop, railway underpass, corner shop, covered car park, canal path, launderette, elevated walkway, and football court.

## Character kit, intro and menu flow

[View the 15-screen front-end concept gallery](docs/concepts/FRONT-END-GALLERY.md): selectable trainers and outfits, intro stills, three title directions, character and borough selection, match setup, squad lobby, loading, pause/settings, and results.

## Black characters and modelling references

[View Jay, Alex and the individual asset sheets](docs/concepts/CHARACTER-ASSET-GALLERY.md) — three consistent UI screens and eight modelling references covering two characters, trainers, hoodie, joggers, balaclava, facade and court fence. [Modelling handoff](docs/concepts/MODELLING-NOTES.md).

## 50 individual asset references

[Browse the 50-image asset gallery](docs/concepts/ASSET-PACK-50.md): black clothing and trainer variants, first-person arms, equipment, court props, street furniture, modular buildings, vehicles, foliage and ground surfaces. Includes a [modelling manifest](docs/concepts/asset-pack-50/manifest.json).

## 30 texture candidates

[Browse the texture gallery](docs/concepts/TEXTURE-PACK-30.md): brick, concrete, roads, paving, metals, black clothing fabrics, trainer materials, timber and ground cover. These are colour images awaiting seamless-repeat checks and PBR material authoring.
