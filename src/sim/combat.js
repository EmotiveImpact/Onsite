/** CombatWorld-style boundary inspired by WWB src/game/combat.ts (MIT 4cf34e8).
 * No renderer, audio or input dependencies: a future server can own this adapter.
 * The current encounter is bots-only; there is no network transport.
 */
import RAPIER from '@dimforge/rapier3d-compat';
export class CombatQueries {
  constructor(world){this.world=world;}
  raycast(origin,direction,maxDistance,excludeCollider){return this.world.castRay(new RAPIER.Ray(origin,direction),maxDistance,true,undefined,undefined,excludeCollider);}
  lineOfSight(origin,target,excludeCollider,targetCollider){
    const distance=Math.hypot(target.x-origin.x,target.y-origin.y,target.z-origin.z);
    if(distance<.0001)return true;
    const dir={x:(target.x-origin.x)/distance,y:(target.y-origin.y)/distance,z:(target.z-origin.z)/distance};
    const hit=this.raycast(origin,dir,distance+.01,excludeCollider);
    return !hit || hit.collider.handle===targetCollider?.handle;
  }
}
