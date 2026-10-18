/** Desktop action mapping adapted from WWB engine/input.ts, 4cf34e8.
 * MIT © 2026 Jeevesh Singale; public/licenses/WWB-MIT.txt.
 * Browser event ownership remains in main; simulation only sees intent.
 */
export function movementIntent(keys){
  let x=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft'));
  let z=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown'));
  const len=Math.hypot(x,z);if(len>1){x/=len;z/=len;}
  return {moveX:x,moveZ:z,sprint:keys.has('ShiftLeft')||keys.has('ShiftRight'),jump:keys.has('Space')};
}
