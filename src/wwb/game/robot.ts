// Original ONSITE visual adapter; no donor character meshes, rigs or animation clips.
import * as THREE from 'three'
import {createOperatorVisual,OperatorAnimator,type OperatorKit} from '../../onsite/OperatorVisual'
export type RobotAsset={scene:THREE.Object3D;clips:THREE.AnimationClip[]}
export type RobotLook='operator'|'breacher'|'sentinel'|'exo'|'warden'
export type HeldKind='rifle'|'shotgun'|'minigun'|'cannon'
export type RobotParts=ReturnType<typeof buildRobot>
export function buildRobot(asset:RobotAsset,look:RobotLook,_visor:string,_held:HeldKind,_vm:unknown){
 const kit:OperatorKit={trainers:look==='breacher'?'high':look==='sentinel'?'runner':'court',hood:look==='sentinel'?'down':'up'};
 const {model,muzzle}=createOperatorVisual(asset.scene,kit),root=new THREE.Group();root.add(model);
 const weak=new THREE.Object3D();weak.position.y=1.3;root.add(weak);
 return {root,model,muzzle,weak,weakRadius:0,scale:1,gibs:[] as THREE.Mesh[],human:true};
}
export class RobotAnimator extends OperatorAnimator{
 constructor(p:RobotParts){super(p.model)}
}
