# ONSITE player flow

Original ONSITE interface and persistence code, 19 October 2026. The existing
WWB encounter owns movement, combat, rounds, physics and pointer lock. This layer
does not add multiplayer, progression rewards, difficulty modifiers or a second
simulation. The estate behind the menu is the current runtime, not concept art.

`index.html` and `src/style.css` provide the ONSITE cream/amber/charcoal interface.
`src/onsite/FrontEnd.ts` owns its panels and presentation. `main.ts` calls
`markReady`, `enterGame`, `showPause`, `showResult` and `returnToTitle` at actual
runtime transitions. Start, resume and retry still use the established button
IDs and real pointer-lock handlers. Leaving a paused encounter ends that attempt;
it does not create a completed-round record.

## Player journey

1. **Play:** Heron Court lists three bots, two levels and a three-minute round.
   Heron Reach lists six bots, five levels and a five-minute round. Map choices
   navigate to the real `/` or `/?map=heron-reach` runtime. The mission is to clear
   the opponents and hold the ground-floor capture area for 2.5 seconds.
2. **Operator:** fixed black balaclava, gloves, joggers and carbine; select hood
   up/down and court, runner or high-top trainers. These are cosmetic choices,
   previewed using the actual original operator GLB. See the operator asset
   documentation for its Blender source and provenance. The preview renderer
   loads on demand and stops when its panel closes or play begins.
3. **Settings:** sensitivity, volume, sound, reduced camera motion and render
   quality. Title and pause controls stay synchronised. Root runtime integration
   applies the settings; software rendering retains its conservative fallback.
4. **Encounter:** existing first-person HUD and movement/weapon controls.
5. **Pause:** resume, restart, adjust controls/audio or return to the title.
6. **Results:** actual time, accuracy, opponents cleared and fastest successful
   capture on this map. Retry the encounter or return to the title.

Tab/Shift+Tab and arrow keys navigate the menu tabs. Pause/results retain keyboard
focus within their visible dialog. Narrow screens can scroll the menu; the game
still requires a keyboard and mouse. Nothing claims touch gameplay support.

## Local records and failures

`src/onsite/profile.ts` stores a versioned `onsite.player.v1` localStorage entry.
It contains preferences, cosmetic kit and separate Court/Reach completed-run
records. A capture counts as a win; a death/timeout is a completed loss. Abandoning
an encounter does not count. Fastest winning simulation time defines the best;
accuracy breaks an exact time tie. No account, cloud upload, invented XP or ranking.

Input is bounded, unknown enum values fall back, corrupt/future-version data uses
defaults, and denied/quota-full storage cannot block play. Failed saves are shown
as session-only. The first default honours the browser's reduced-motion preference.

## Verification

`tests/profile.test.ts` covers round-trip persistence, corrupt/blocked storage,
invalid settings and kit values, record isolation, and loss/win ranking. The
separate UI fixture makes no gameplay claims:

```sh
npx tsx --test tests/profile.test.ts
npm run dev
ONSITE_URL=http://127.0.0.1:5173 node scripts/verify-player-flow.mjs
```

`tests/frontend-harness.html` loads the exact interface, preference module and
operator asset without importing Encounter or physics. It installs the actual WWB
Input listeners in their unlocked state, checking native Tab movement, Space button
activation and select-arrow behaviour against those listeners. Its synthetic round hooks
exist only in the test fixture, never the production entry. The browser script
checks keyboard focus, real kit asset loading, saved settings, actual UI transitions,
results persistence, both maps' descriptions and 390 px layout. Screenshots from
this fixture must be labelled **interface fixtures, not running-game evidence**.
The production build and both full input-driven encounter checks remain required.
