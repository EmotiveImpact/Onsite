// Original ONSITE procedural contact grounding; no donor code or texture pixels.
// Provenance, costs and limits: docs/maps/heron-reach-32/art/CONTACT-GROUNDING.md.
import * as THREE from 'three'
import type {Solid} from './level'
import type {Level} from './levels'

export type ContactSupport={surface:Solid;y:number;clearance:number};
export type ContactPatch={x:number;y:number;z:number;width:number;depth:number;yaw:number;opacity:number;support:Solid};
export type ContactActor={alive:boolean;scale?:number;parts:{root:THREE.Object3D}};
// Grass art is 1 cm above collision FFL; keep the proxy 4 mm clear of that finish.
const CONTACT_LIFT=.014,MAX_DROP=.55,MAX_ACTORS=32;

/** Read-only broad phase over existing floor boxes; no raycasts or second physics world. */
export class ContactSupportIndex {
 private readonly cells=new Map<string,Solid[]>();
 constructor(solids:readonly Solid[],surfaceIds:readonly string[],private readonly cellSize=4){
  const ids=new Set(surfaceIds);
  for(const s of solids){
   if(!ids.has(s.id))continue;
   for(let x=Math.floor((s.x-s.w/2)/cellSize);x<=Math.floor((s.x+s.w/2)/cellSize);x++)
    for(let z=Math.floor((s.z-s.d/2)/cellSize);z<=Math.floor((s.z+s.d/2)/cellSize);z++){
     const key=x+':'+z,list=this.cells.get(key);if(list)list.push(s);else this.cells.set(key,[s]);
    }
  }
 }
 /** At most 4 cm of render interpolation tolerance; an overhead storey cannot receive. */
 below(x:number,feetY:number,z:number,maxDrop=MAX_DROP):ContactSupport|null {
  let found:Solid|undefined,top=-Infinity;
  for(const s of this.cells.get(Math.floor(x/this.cellSize)+':'+Math.floor(z/this.cellSize))??[]){
   const y=s.y+s.h/2;
   if(y>feetY+.04||feetY-y>maxDrop||Math.abs(x-s.x)>s.w/2||Math.abs(z-s.z)>s.d/2)continue;
   if(y>top+1e-6||(Math.abs(y-top)<=1e-6&&s.w*s.d>(found?.w??0)*(found?.d??0))){found=s;top=y}
  }
  return found?{surface:found,y:top,clearance:Math.max(0,feetY-top)}:null;
 }
}

/** Smoothly disappear as the object lifts; full contact tolerates the capsule's skin gap. */
export function contactHeightFade(clearance:number):number {
 const t=THREE.MathUtils.clamp((clearance-.04)/(MAX_DROP-.04),0,1);
 return 1-t*t*(3-2*t);
}

/** Existing measured prop/cover/trunk/column boxes supply contact footprints, once at load. */
export function staticContactPatches(solids:readonly Solid[],support:ContactSupportIndex):ContactPatch[]{
 const patches:ContactPatch[]=[];
 for(const s of solids){
  if(!(s.id==='dress'||s.id==='tree'||s.id==='column'||s.id.startsWith('cover-')))continue;
  // Whole architectural masses would add little contact detail and excessive overdraw.
  if(s.w*s.d>24||Math.min(s.w,s.d)<.05)continue;
  const receiver=support.below(s.x,s.y-s.h/2,s.z);
  if(!receiver)continue;
  patches.push({x:s.x,y:receiver.y+CONTACT_LIFT,z:s.z,width:s.w+.26,depth:s.d+.26,yaw:0,
   opacity:.16*contactHeightFade(receiver.clearance),support:receiver.surface});
 }
 return patches;
}

/** One instanced draw of soft, shallow contact proxies. These are not physical light shadows.
 * Construct on Reach after the scene loads; update after bot.render(alpha), before rendering. */
export class HeronContactShadows {
 readonly mesh:THREE.InstancedMesh<THREE.PlaneGeometry,THREE.MeshBasicMaterial>;
 readonly staticCount:number;
 readonly actorCapacity=MAX_ACTORS;
 private readonly support:ContactSupportIndex;
 private readonly opacity:THREE.InstancedBufferAttribute;
 private readonly bounds:THREE.InstancedBufferAttribute;
 private readonly matrix=new THREE.Matrix4();
 private readonly rotation=new THREE.Quaternion();
 private readonly position=new THREE.Vector3();
 private readonly scale=new THREE.Vector3();
 private readonly up=new THREE.Vector3(0,1,0);
 private readonly enabled:boolean;

 constructor(private readonly scene:THREE.Scene,level:Level){
  this.enabled=level.id==='heron-reach';
  this.support=new ContactSupportIndex(this.enabled?level.solids:[],level.surfaceIds);
  const patches=this.enabled?staticContactPatches(level.solids,this.support):[];
  this.staticCount=patches.length;
  const capacity=this.staticCount+MAX_ACTORS*2;
  const geometry=new THREE.PlaneGeometry(1,1).rotateX(-Math.PI/2);
  this.opacity=new THREE.InstancedBufferAttribute(new Float32Array(capacity),1).setUsage(THREE.DynamicDrawUsage);
  this.bounds=new THREE.InstancedBufferAttribute(new Float32Array(capacity*4),4).setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('onsiteContactOpacity',this.opacity);geometry.setAttribute('onsiteContactBounds',this.bounds);
  const material=new THREE.MeshBasicMaterial({name:'ONSITE contact grounding',color:0x000000,transparent:true,depthWrite:false,
   depthTest:true,fog:false,toneMapped:false,alphaTest:.001,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1});
  material.onBeforeCompile=shader=>{
   shader.vertexShader=`attribute float onsiteContactOpacity;
attribute vec4 onsiteContactBounds;
varying float vContactOpacity;
varying vec2 vContactUv;
varying vec2 vContactWorld;
varying vec4 vContactBounds;
`+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>',`#include <project_vertex>
    vec4 contactWorld = modelMatrix * instanceMatrix * vec4( position, 1.0 );
    vec3 contactCentre = ( modelMatrix * instanceMatrix[3] ).xyz;
    vContactOpacity = onsiteContactOpacity * ( 1.0 - smoothstep( 35.0, 70.0, distance( cameraPosition, contactCentre ) ) );
    vContactUv = uv;
    vContactWorld = contactWorld.xz;
    vContactBounds = onsiteContactBounds;`);
   shader.fragmentShader=`varying float vContactOpacity;
varying vec2 vContactUv;
varying vec2 vContactWorld;
varying vec4 vContactBounds;
`+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
    // Original analytic mask: soft ellipse, confined to the actual receiving rectangle.
    float contactRadius = length( vContactUv * 2.0 - 1.0 );
    vec2 contactEdge = min( vContactWorld - vContactBounds.xy, vContactBounds.zw - vContactWorld );
    float contactReceiver = smoothstep( 0.0, 0.035, min( contactEdge.x, contactEdge.y ) );
    diffuseColor.a *= vContactOpacity * ( 1.0 - smoothstep( 0.22, 1.0, contactRadius ) ) * contactReceiver;`);
  };
  material.customProgramCacheKey=()=>'onsite-contact-grounding-v1';
  this.mesh=new THREE.InstancedMesh(geometry,material,capacity);
  this.mesh.name='ONSITE / Heron Reach contact grounding';this.mesh.count=this.staticCount;
  this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  this.mesh.frustumCulled=false;this.mesh.renderOrder=2;
  this.mesh.castShadow=false;this.mesh.receiveShadow=false;
  patches.forEach((patch,i)=>this.write(i,patch.x,patch.y,patch.z,patch.width,patch.depth,patch.yaw,patch.opacity,patch.support));
  this.mesh.instanceMatrix.needsUpdate=true;
  if(this.enabled)scene.add(this.mesh);
 }

 /** Reuse the actor's interpolated presentation of its existing body; no simulation writes.
  * Dead/hidden actors and unsupported or airborne feet contribute no patch. */
 update(actors:readonly ContactActor[]):number {
  if(!this.enabled)return 0;
  let count=0;
  for(let i=0;i<Math.min(actors.length,MAX_ACTORS);i++){
   const actor=actors[i],root=actor.parts.root;
   if(!actor.alive||!root.visible)continue;
   const k=THREE.MathUtils.clamp(actor.scale??1,.5,2),yaw=root.rotation.y,c=Math.cos(yaw),s=Math.sin(yaw);
   for(const side of [-1,1]){
    const x=root.position.x+side*.14*k*c,z=root.position.z-side*.14*k*s;
    const receiver=this.support.below(x,root.position.y,z);
    if(!receiver)continue;
    const strength=.22*contactHeightFade(receiver.clearance);
    if(strength<.001)continue;
    this.write(this.staticCount+count,x,receiver.y+CONTACT_LIFT,z,.30*k,.46*k,yaw,strength,receiver.surface);count++;
   }
  }
  this.mesh.count=this.staticCount+count;
  if(count){
   this.mesh.instanceMatrix.clearUpdateRanges();this.mesh.instanceMatrix.addUpdateRange(this.staticCount*16,count*16);this.mesh.instanceMatrix.needsUpdate=true;
   this.opacity.clearUpdateRanges();this.opacity.addUpdateRange(this.staticCount,count);this.opacity.needsUpdate=true;
   this.bounds.clearUpdateRanges();this.bounds.addUpdateRange(this.staticCount*4,count*4);this.bounds.needsUpdate=true;
  }
  return count;
 }

 private write(i:number,x:number,y:number,z:number,width:number,depth:number,yaw:number,opacity:number,support:Solid){
  this.position.set(x,y,z);this.scale.set(width,1,depth);this.rotation.setFromAxisAngle(this.up,yaw);
  this.mesh.setMatrixAt(i,this.matrix.compose(this.position,this.rotation,this.scale));
  this.opacity.setX(i,opacity);
  this.bounds.setXYZW(i,support.x-support.w/2,support.z-support.d/2,support.x+support.w/2,support.z+support.d/2);
 }

 dispose(){this.scene.remove(this.mesh);this.mesh.geometry.dispose();this.mesh.material.dispose()}
}
