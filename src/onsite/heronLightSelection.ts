import type {Solid} from './level'

type Position={x:number;y:number;z:number};
export type ReceiverLightAnchor=Position&{kind:string;floorY?:number};
export type LightOccluder={id:string;min:Position;max:Position;structuralFloor:boolean};
export type PreparedLight<T extends ReceiverLightAnchor=ReceiverLightAnchor>={
 anchor:T;position:Position;floorY:number|null;intensity:number;range:number;
};

/** Read-only floor lookup. Pass the existing surface solids, not walls or furniture. */
export function lightReceiverBelow(position:Position,surfaces:readonly Solid[]):number|null{
 let floor:number|null=null;
 for(const s of surfaces){
  const top=s.y+s.h/2;
  if(top>position.y-.35||Math.abs(position.x-s.x)>s.w/2||Math.abs(position.z-s.z)>s.d/2)continue;
  if(floor===null||top>floor)floor=top;
 }
 return floor;
}

/** Fixtures mounted from the street remain ground lamps even when a deck overlaps their heads. */
export function lightReceiverFloor(anchor:ReceiverLightAnchor,surfaces:readonly Solid[]):number|null{
 if(anchor.floorY!==undefined&&Number.isFinite(anchor.floorY))return anchor.floorY;
 if(['court','street','shop'].includes(anchor.kind))return 0;
 // Core fittings are authored 2.65 m above their own landing, including the undercroft.
 if(anchor.kind==='core')return Math.round((anchor.y-2.65)/3)*3;
 return lightReceiverBelow(anchor,surfaces);
}

export function lightPhotometry(kind:string){
 return kind==='court'?{intensity:850,range:42}:
  kind==='street'?{intensity:175,range:25}:
  kind==='shop'?{intensity:55,range:12}:
  kind==='gallery'?{intensity:6,range:7}:
  kind==='ceiling'||kind==='core'?{intensity:11,range:9}:{intensity:14,range:9};
}

/** Cache receiver identity and the actual light position once, outside the animation loop. */
export function prepareReceiverLights<T extends ReceiverLightAnchor>(anchors:readonly T[],surfaces:readonly Solid[]):PreparedLight<T>[] {
 return anchors.map(anchor=>({anchor,position:{x:anchor.x,y:anchor.y-.35,z:anchor.z},
  floorY:lightReceiverFloor(anchor,surfaces),...lightPhotometry(anchor.kind)}));
}

/** Conservative structural blockers; transparent glass and the porous Cage do not stop light. */
export function prepareLightOccluders(solids:readonly Solid[]):LightOccluder[]{
 return solids.filter(s=>s.w>0&&s.h>0&&s.d>0&&
  !['glass','lit','rail'].includes(s.mat)&&s.id!=='fence'&&!s.id.startsWith('glass-')&&!s.id.startsWith('cage-fence'))
  .map(s=>({id:s.id,min:{x:s.x-s.w/2,y:s.y-s.h/2,z:s.z-s.d/2},
   max:{x:s.x+s.w/2,y:s.y+s.h/2,z:s.z+s.d/2},
   structuralFloor:['ground','slab','roof','landing','stair'].includes(s.id)||s.id.endsWith('-cap')}));
}

/** Segment/AABB interval, including parallel rays. Never ignores an intervening slab. */
export function lightSegmentBlocked(from:Position,to:Position,occluders:readonly LightOccluder[]):boolean{
 const length=Math.hypot(to.x-from.x,to.y-from.y,to.z-from.z);
 if(length<1e-6)return false;
 for(const b of occluders){
  let enter=0,leave=1,hit=true;
  for(const axis of ['x','y','z'] as const){
   const delta=to[axis]-from[axis];
   if(Math.abs(delta)<1e-9){if(from[axis]<b.min[axis]||from[axis]>b.max[axis]){hit=false;break}}
   else{
    let a=(b.min[axis]-from[axis])/delta,c=(b.max[axis]-from[axis])/delta;
    if(a>c)[a,c]=[c,a];enter=Math.max(enter,a);leave=Math.min(leave,c);
    if(enter>leave){hit=false;break}
   }
  }
  if(!hit||leave<1e-5||enter>1-1e-5)continue;
  // A wall fixture may originate a few centimetres inside its mounting wall. Only forgive
  // that initial small exit; a remote wall and every structural floor still block the ray.
  if(!b.structuralFloor&&enter===0&&leave*length<=.22)continue;
  return true;
 }
 return false;
}

/** Three-metre storeys. Stair treads retain the lower landing's pool until the next landing. */
const receiverStorey=(floorY:number)=>Math.floor((floorY+.12)/3);

/** Call on the existing quarter-second lighting tick, not every frame. No physics mutations.
 * A perceptual score uses sqrt(intensity), so distant floodlights cannot monopolise a shop view.
 * Visibility is tested in descending score order and stops when the fixed pool is full.
 */
export function selectReceiverLights<T extends ReceiverLightAnchor>(lights:readonly PreparedLight<T>[],camera:Position,
 cameraFloorY:number|null,occluders:readonly LightOccluder[],limit:number):PreparedLight<T>[] {
 const count=Math.floor(limit);
 if(cameraFloorY===null||count<=0)return [];
 const storey=receiverStorey(cameraFloorY);
 const candidates=lights.filter(l=>l.floorY!==null&&receiverStorey(l.floorY)===storey).map((light,index)=>{
  const distance2=(light.position.x-camera.x)**2+(light.position.y-camera.y)**2+(light.position.z-camera.z)**2;
  const cutoff=Math.max(0,1-(distance2/(light.range*light.range))**2);
  return {light,index,score:Math.sqrt(light.intensity)*cutoff*cutoff/(distance2+4)};
 }).filter(c=>c.score>0).sort((a,b)=>b.score-a.score||a.index-b.index);
 const selected:PreparedLight<T>[]=[];
 for(const c of candidates){
  if(lightSegmentBlocked(c.light.position,camera,occluders))continue;
  selected.push(c.light);if(selected.length>=count)break;
 }
 return selected;
}
