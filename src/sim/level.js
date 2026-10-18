// Metres, Y up. Shared collision/layout data; no renderer or browser dependencies.
export const SPAWN = { x: 0, y: 1, z: 16 };
export const BOT_SPAWN = { x: 7, y: 1, z: -7 };
export const OBJECTIVE = { x: 7, y: 0, z: -7, radius: 3 };
export const PATROL = [{ x: 7, z: -7 }, { x: 11, z: -10 }, { x: 3, z: -10 }, { x: 3, z: -5 }];
export const solids = [];
function box(id, x, y, z, w, h, d, material = 'concrete') {
  const item = { id, position: { x, y, z }, size: { x: w, y: h, z: d }, material };
  solids.push(item); return item;
}
box('ground', 0, -.3, 0, 48, .6, 52, 'asphalt');
box('north-block', 0, 8, -24, 48, 16, 5, 'brick');
box('west-block', -22, 7, -1, 5, 14, 46, 'brick');
box('east-block', 22, 9, -4, 5, 18, 40, 'stock');
box('south-wall', 0, 1.5, 25, 48, 3, 1, 'brick');
// South wing frames the entrance, keeping a readable street-like space.
box('south-west', -17, 5, 22, 10, 10, 5, 'brick');
box('south-east', 17, 6, 22, 10, 12, 5, 'stock');
box('west-pavement', -16.8, .06, -1, 5.5, .12, 43, 'paving');
box('north-pavement', 0, .06, -19.5, 34, .12, 3, 'paving');
box('court', 7, .035, -7, 18, .07, 19, 'court');
// Actual stair risers, not an invisible ramp: 16 x 0.2m climb to a 3.2m deck.
for (let i = 0; i < 16; i++) {
  const height = (i + 1) * .2;
  box(`stair-${i}`, -13.8, height / 2, 4 - i * .42, 2.8, height, .42);
}
box('stair-landing', -13.8, 3.05, -3.4, 3.6, .3, 2.2);
box('west-deck', -16, 3.05, -11.2, 6, .3, 13.5);
box('north-deck', 0, 3.05, -19, 38, .3, 4);
box('stair-side', -15.45, 1.65, 1.2, .22, 3.3, 7.2, 'brick');
box('landing-rail', -11.9, 3.75, -3.4, .1, 1.1, 2.1, 'steel');
box('deck-rail', -12.95, 3.75, -11, .1, 1.1, 13.1, 'steel');
box('north-rail', 3, 3.75, -16.95, 32, 1.1, .1, 'steel');
for (const z of [-6, -12, -18]) box(`deck-column-${z}`, -13.4, 1.5, z, .38, 3, .38);
// Fence colliders stay solid even though the visual mesh is open wire.
box('fence-east', 16.15, 1.5, -7, .1, 3, 19, 'fence');
box('fence-north', 7, 1.5, -16.5, 18.4, 3, .1, 'fence');
box('fence-west', -2.15, 1.5, -9, .1, 3, 15, 'fence');
box('fence-south-left', .15, 1.5, 2.5, 4.6, 3, .1, 'fence');
box('fence-south-right', 12.3, 1.5, 2.5, 7.7, 3, .1, 'fence');
box('planter-entry', -5, .65, 8, 3.8, 1.3, 1.5);
box('planter-east', 17.8, .65, 7, 2, 1.3, 4);
box('cover-west', 1, .65, -4, 1.5, 1.3, 2.3);
box('cover-north', 11.6, .65, -12, 2.5, 1.3, 1.4);
box('shop', 16.8, 2.5, -20, 5, 5, 3, 'brick');
export const lamps = [{x:-10,z:9},{x:17.5,z:1},{x:17.5,z:-14},{x:-10,z:-14}];
for (const [i,p] of lamps.entries()) box(`lamp-collider-${i}`,p.x,2,p.z,.18,4,.18,'invisible');
