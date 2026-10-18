# ONSITE: playable estate prototype

A first browser-playable slice of the ONSITE concept, built with Three.js. One night-time London estate with rain, wet paving, deck-access walkways, the football court and The Corner shop on Heron Way, plus the concept HUD.

This is a single-player prototype: you play Hold the Court against four bots. There is no networking yet.

## Run it

The page loads Three.js from jsDelivr and the textures from `game/textures`, so it needs to be served over HTTP rather than opened as a file:

```sh
cd game
python3 -m http.server 8000
# then open http://localhost:8000
```

Any static server works (`npx serve game` too).

## Controls

| Key | Action |
| --- | --- |
| WASD | Move |
| Mouse | Look (click the view to capture the mouse) |
| Left click | Fire |
| Right click | Aim down the red dot |
| Shift | Sprint |
| Space | Jump |
| R | Reload |
| M | Mute |
| Esc | Pause |

## How the match works

- The match starts at 04 : 02 with 03:17 on the clock, as in the concept art.
- Stand inside the amber ring on the football court to take it. Seven seconds uncontested scores a point for you.
- Bots patrol the courtyard, Heron Way, the court and the first-floor walkway. A bot standing in the ring on its own pushes the court the other way and scores for them.
- Bodyshots take three hits, headshots one. You regenerate health after four seconds out of fire.

## What is in the scene

- Block A: four-storey stock-brick deck-access block with walkways, bulkhead lights and a stair you can climb.
- Block B (north) with balconies and a lit entrance lobby, Block C (south), and backdrop blocks and tower blocks with lit windows.
- The caged football court with floodlights, goals and the Hold the Court zone.
- Heron Way with its turning head, double yellow lines, bollards, a parked car and The Corner shop.
- Rain, fog, bloom, puddle-mapped wet ground and lamp reflections streaking towards the camera.

Textures are downscaled copies of the source set in `assets/textures/source-30`. Everything else (signs, shop interior, court markings, tower windows, graffiti) is drawn at load time on canvas.
