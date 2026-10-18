// Original ONSITE visual adapter; no donor character meshes, rigs or animation clips.
import * as THREE from 'three'
export type RobotAsset={scene:THREE.Object3D;clips:THREE.AnimationClip[]}
export type RobotLook='operator'|'breacher'|'sentinel'|'exo'|'warden'
export type HeldKind='rifle'|'shotgun'|'minigun'|'cannon'
export type RobotParts=ReturnType<typeof buildRobot>
export function buildRobot(asset:RobotAsset,_look:RobotLook,_visor:string,_held:HeldKind,_vm:unknown){
 const root=new THREE.Group(),model=asset.scene.clone(true);root.add(model);model.rotation.y=Math.PI;
 const muzzle=new THREE.Object3D();muzzle.position.set(.2,1.25,-.6);root.add(muzzle);
 const weak=new THREE.Object3D();weak.position.y=1.3;root.add(weak);
 return {root,model,muzzle,weak,weakRadius:0,scale:1,gibs:[] as THREE.Mesh[],human:true};
}
export class RobotAnimator{
 private dead=false;private stagger=0;private phase=0;
 constructor(private p:RobotParts){}
 get staggered(){return this.stagger>0}
 reset(){this.dead=false;this.p.model.rotation.z=0}
 hit(_x:number,_z:number,_power:number){}
 fire(){}
 staggerFor(t:number){this.stagger=t}
 die(_x:number,_z:number,_head:boolean){this.dead=true}
 update(dt:number,speed:number,_f:number,_s:number,_a:number,_p:number,_time:number){this.stagger=Math.max(0,this.stagger-dt);this.phase+=dt*speed*2.6;
 if(this.dead){this.p.model.rotation.z=THREE.MathUtils.damp(this.p.model.rotation.z,1.4,5,dt);return}
 this.p.model.traverse(o=>{if(/Leg_|Trainer_/.test(o.name))o.rotation.x=Math.sin(this.phase+(o.name.endsWith('L')?0:Math.PI))*.2*Math.min(1,speed);});}
}
