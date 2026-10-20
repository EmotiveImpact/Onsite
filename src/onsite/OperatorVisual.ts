// Original ONSITE character presentation. The WWB actor owns all physical movement.
import * as THREE from 'three'
import {clone} from 'three/addons/utils/SkeletonUtils.js'

export type OperatorKit={trainers:'court'|'runner'|'high';hood:'up'|'down'}
export const DEFAULT_OPERATOR_KIT:Readonly<OperatorKit>={trainers:'court',hood:'up'}
export const OPERATOR_ASSET='/models/onsite-operator.glb'

/** Changes authored geometry, never a collider, weapon stat or shared material. */
export function setOperatorKit(model:THREE.Object3D,kit:OperatorKit){
 model.traverse(o=>{
  if(o.name.startsWith('Trainers_'))o.visible=o.name==='Trainers_'+kit.trainers
  if(o.name.startsWith('Hood_'))o.visible=o.name==='Hood_'+kit.hood
 })
 model.userData.operatorKit={...kit}
}

export function createOperatorVisual(source:THREE.Object3D,kit:OperatorKit=DEFAULT_OPERATOR_KIT){
 // A plain Object3D.clone would share the skeleton and move every bot together.
 const model=clone(source)
 model.rotation.y=Math.PI
 model.traverse(o=>{if(o instanceof THREE.Mesh){
  o.castShadow=true;o.receiveShadow=true
  // Animated joints leave the rest-pose box. Preserve the small skins during motion.
  if(o instanceof THREE.SkinnedMesh)o.frustumCulled=false
 }})
 setOperatorKit(model,kit)
 const muzzle=model.getObjectByName('MuzzleSocket')
 if(!muzzle)throw new Error('ONSITE operator asset is missing its authored muzzle socket')
 return {model,muzzle}
}

type Joint={bone:THREE.Object3D;position:THREE.Vector3;quaternion:THREE.Quaternion;axes:THREE.Vector3[]}
const axis=new THREE.Vector3(),rotation=new THREE.Quaternion()

/** Original analytic motion using hip/knee/ankle pivots. It only follows the actor. */
export class OperatorAnimator{
 private readonly joints=new Map<string,Joint>()
 private phase=0
 private motion=0
 private recoil=0
 private impact=0
 private dead=false
 private death=0
 private stagger=0
 constructor(private readonly model:THREE.Object3D){
  model.updateMatrixWorld(true)
  const modelQ=model.getWorldQuaternion(new THREE.Quaternion())
  model.traverse(bone=>{
   if(!(bone instanceof THREE.Bone))return
   const inverse=bone.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(modelQ)
   this.joints.set(bone.name,{bone,position:bone.position.clone(),quaternion:bone.quaternion.clone(),
    axes:[new THREE.Vector3(1,0,0),new THREE.Vector3(0,1,0),new THREE.Vector3(0,0,1)].map(v=>v.applyQuaternion(inverse))})
  })
 }
 get staggered(){return this.stagger>0}
 reset(){this.dead=false;this.death=0;this.recoil=0;this.impact=0;this.stagger=0;this.motion=0;this.phase=0;this.restore()}
 fire(){this.recoil=Math.min(1,this.recoil+.72)}
 hit(x:number,z:number,power:number){this.impact=THREE.MathUtils.clamp((x+z)*.025*power,-.12,.12)}
 staggerFor(t:number){this.stagger=Math.max(this.stagger,t)}
 die(_x:number,_z:number,_head:boolean){this.dead=true}
 private restore(){for(const j of this.joints.values()){j.bone.position.copy(j.position);j.bone.quaternion.copy(j.quaternion)}}
 private turn(name:string,x=0,y=0,z=0){
  const j=this.joints.get(name);if(!j)return
  for(const [i,angle]of[x,y,z].entries())if(angle){axis.copy(j.axes[i]);rotation.setFromAxisAngle(axis,angle);j.bone.quaternion.multiply(rotation)}
 }
 update(dt:number,speed:number,forward:number,side:number,aimYaw:number,aimPitch:number,time:number){
  this.stagger=Math.max(0,this.stagger-dt)
  this.recoil=THREE.MathUtils.damp(this.recoil,0,17,dt)
  this.impact=THREE.MathUtils.damp(this.impact,0,9,dt)
  this.motion=THREE.MathUtils.damp(this.motion,Math.min(1,speed/2.5),8,dt)
  this.restore()
  if(this.dead){
   this.death=THREE.MathUtils.damp(this.death,1,5,dt)
   this.turn('Root',this.death*1.48,0,this.death*.12)
   const root=this.joints.get('Root');if(root)root.bone.position.y+=this.death*.08
   this.turn('Thigh_L',-.3*this.death);this.turn('Shin_L',.65*this.death)
   this.turn('Thigh_R',.14*this.death);this.turn('Shin_R',.28*this.death)
   this.turn('Head',-.2*this.death)
   return
  }
  this.phase+=dt*Math.min(speed,6)*3.0
  const breath=Math.sin(time*2.2)*.009,bob=Math.abs(Math.sin(this.phase))*.022*this.motion
  const pelvis=this.joints.get('Pelvis');if(pelvis)pelvis.bone.position.y+=bob
  for(const [index,sideName]of(['L','R']as const).entries()){
   const cycle=Math.sin(this.phase+index*Math.PI),lift=Math.max(0,-cycle)
   this.turn('Thigh_'+sideName,-cycle*.37*this.motion*forward,0,cycle*.23*this.motion*side)
   this.turn('Shin_'+sideName,lift*.56*this.motion)
   this.turn('Foot_'+sideName,-lift*.20*this.motion)
  }
  this.turn('Pelvis',0,Math.sin(this.phase)*.045*this.motion,-side*.035*this.motion)
  this.turn('Spine',breath+speed*.004,THREE.MathUtils.clamp(aimYaw,-.8,.8)*.32,-this.impact)
  // Rifle, wrists and sleeves follow the chest together; hands stay on the prop.
  this.turn('Chest',-THREE.MathUtils.clamp(aimPitch,-.65,.65)*.8-this.recoil*.055,
   THREE.MathUtils.clamp(aimYaw,-.8,.8)*.58,Math.sin(this.phase)*.012*this.motion+this.impact)
  this.turn('Neck',-breath*.6)
  this.turn('Head',-THREE.MathUtils.clamp(aimPitch,-.65,.65)*.2,THREE.MathUtils.clamp(aimYaw,-.8,.8)*.1)
 }
}
