// Original ONSITE light placement from the existing B01 stair geometry.
// Presentation only: no floor, collider, navigation or shadow-map changes.
import spec from '../../docs/maps/heron-reach-32/blueprints/build-spec.json'
import type {ReceiverLightAnchor} from './heronLightSelection'

export type StairLightAnchor=ReceiverLightAnchor&{
 kind:'core';coreId:string;landing:'full'|'half';floorY:number;fixtureFloorY:number;
};

/** Warm-neutral fluorescent presentation, used inside the existing 4/10-light pool.
 * Shorter reach contains the local pool; visible fixture geometry supplies the emission. */
export const stairCorePhotometry=Object.freeze({color:'#efe3ca',intensity:15,range:7});

/** Keep the 32 authored entry strips and add a strip over each of the 24 half-landings.
 * The return-flight side stays visible past the opaque well spine. Midpoint lights belong
 * to their LOWER three-metre storey for selection, even though their receiver is at +1.5m.
 * Explicit floorY prevents the old core-height rounding from assigning them upstairs.
 * Points are fixture centres; prepareReceiverLights already lowers the source by 0.35m. */
export function buildStairLightAnchors():StairLightAnchor[]{
 const stair=spec.stairs['ST-P'],halfX=stair.secondFlightX+stair.flightWidth/2;
 const halfZ=stair.halfLanding[1]+stair.halfLanding[3]/2;
 const halfRise=stair.rise*stair.risersPerFlight,fixtureHeight=2.65;
 return spec.cores.flatMap(core=>core.levels.flatMap((floorY,i)=>{
  const point=(localX:number,localZ:number,fixtureFloorY:number,landing:'full'|'half'):StairLightAnchor=>({
   x:core.rect[0]+localX-72,y:fixtureFloorY+fixtureHeight,
   z:core.rect[1]+(core.mirrorZ?core.rect[3]-localZ:localZ)-60,
   kind:'core',coreId:core.id,landing,floorY,fixtureFloorY,
  });
  const anchors=[point(1.75,5,floorY,'full')];
  if(i<core.levels.length-1)anchors.push(point(halfX,halfZ,floorY+halfRise,'half'));
  return anchors;
 }));
}

export const stairLightAnchors=buildStairLightAnchors();
