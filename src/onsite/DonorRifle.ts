// Original ONSITE adapter: IRONLINE's CC BY weapon/arms art, WWB's combat timing.
// No donor engine code or Fab animation tracks. Credits: public/licenses/DONOR-ASSETS.md.
import * as THREE from 'three'
import {clone} from 'three/addons/utils/SkeletonUtils.js'
import {flashGroup, type ViewModel} from '../wwb/game/guns'

export function donorRifle(source:THREE.Object3D, flashTexture:THREE.Texture, flameTexture:THREE.Texture):ViewModel {
  const root=new THREE.Group(),model=clone(source);model.scale.setScalar(.5);root.add(model);
  root.name='ONS-01 / IRONLINE M4 + DJMaesen hands';
  model.traverse(o=>{if(o instanceof THREE.Mesh){
    o.frustumCulled=false;o.castShadow=false;o.receiveShadow=false;
    const tune=(m:THREE.Material)=>{const c=(m as THREE.MeshStandardMaterial).clone();c.color.multiplyScalar(c.name==='arms'?.52:.48);c.roughness=Math.max(.68,c.roughness);if(c.name==='arms'){c.metalness=0;c.roughness=.95;c.roughnessMap=null;c.metalnessMap=null;c.envMapIntensity=.3}
      if(c.name==='arms'){c.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\n diffuseColor.rgb = vec3(dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722))) * vec3(0.55, 0.58, 0.62);')};c.customProgramCacheKey=()=> 'onsite-black-kit'}return c};
    o.material=Array.isArray(o.material)?o.material.map(tune):tune(o.material);
  }});
  const muzzle=model.getObjectByName('MuzzleSocket')!,eject=model.getObjectByName('EjectionPort')!;
  const magazine=model.getObjectByName('Magazine')!,magRest=magazine.position.clone();
  const bolt=model.getObjectByName('ChargingHandle')!,boltRest=bolt.position.clone();
  const flash=flashGroup(flashTexture,flameTexture,.6);muzzle.add(flash);
  // The artist-authored base pose already wraps the hands around this gun.
  // Move the left chain with an original analytic two-bone reach during magazine changes.
  const bones:THREE.Object3D[]=[];model.traverse(o=>{if(o instanceof THREE.Bone)bones.push(o)});
  const rest=bones.map(b=>({p:b.position.clone(),q:b.quaternion.clone(),s:b.scale.clone()}));
  // Use the authored rig's bore anchor, closer to the eye. The previous far-forward
  // placement exposed the open shoulder ends and filled the image with sleeves.
  const hip=new THREE.Vector3(.09,-.155,-.41);
  root.updateMatrixWorld(true);
  const world=(o:THREE.Object3D)=>o.getWorldPosition(new THREE.Vector3());
  const chain=(side:'L'|'R')=>{
    const upper=model.getObjectByName('UpArm_'+side)!,fore=model.getObjectByName('Forearm_'+side)!,hand=model.getObjectByName('Hand_'+side)!;
    const tip=model.getObjectByName('BoneTwist_01'+side+'_end')??model.getObjectByName('BoneTwist_01.'+side+'_end');
    if(!upper||!fore||!hand||!tip)throw new Error('Imported rifle is missing '+side+' arm controls');
    return {upper,fore,hand,tip,controlQ:upper.parent!.getWorldQuaternion(new THREE.Quaternion()),shoulder:root.worldToLocal(world(upper)),wrist:root.worldToLocal(world(hand)),u:world(upper).distanceTo(world(fore)),l:world(fore).distanceTo(world(tip))};
  };
  const left=chain('L'),right=chain('R');
  function pointBone(joint:THREE.Object3D,child:THREE.Object3D,destination:THREE.Vector3){
    const a=world(joint),from=world(child).sub(a).normalize(),to=destination.clone().sub(a).normalize();
    const q=new THREE.Quaternion().setFromUnitVectors(from,to).multiply(joint.getWorldQuaternion(new THREE.Quaternion()));
    joint.quaternion.copy(joint.parent!.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(q));root.updateMatrixWorld(true);
  }
  function solve(c:ReturnType<typeof chain>,target:THREE.Vector3,side:number){
    // Keep the open sleeve behind the camera's lower edge while the gun moves.
    // A small shoulder reach handles targets beyond the two-bone limb length.
    const a=root.parent!.localToWorld(c.shoulder.clone().add(hip)),dir=target.clone().sub(a).normalize();
    const max=c.u+c.l-.003,extra=Math.max(0,a.distanceTo(target)-max);a.addScaledVector(dir,extra);
    const control=c.upper.parent!,parent=control.parent!;
    control.quaternion.copy(parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(root.parent!.getWorldQuaternion(new THREE.Quaternion())).multiply(c.controlQ));root.updateMatrixWorld(true);
    control.position.add(parent.worldToLocal(a.clone()).sub(parent.worldToLocal(world(c.upper))));root.updateMatrixWorld(true);
    const d=THREE.MathUtils.clamp(a.distanceTo(target),Math.abs(c.u-c.l)+.001,max);
    const along=(c.u*c.u-c.l*c.l+d*d)/(2*d),height=Math.sqrt(Math.max(0,c.u*c.u-along*along));
    const pole=new THREE.Vector3(side,-1.3,.15).transformDirection(root.parent!.matrixWorld);pole.addScaledVector(dir,-pole.dot(dir)).normalize();
    const elbow=a.clone().addScaledVector(dir,along).addScaledVector(pole,height);
    pointBone(c.upper,c.fore,elbow);pointBone(c.fore,c.tip,target);
    // The donor wrist uses a separate control branch; it is not a forearm child.
    c.hand.position.copy(c.hand.parent!.worldToLocal(target.clone()));root.updateMatrixWorld(true);
  }
  return {root,muzzle,eject,mag:magazine,magRest,flash,sightY:.10548,sightZ:.11718,
    hip:hip.clone(),hipRoll:THREE.MathUtils.degToRad(5),ads:{x:.003233,y:-.10547856,z:-.43},
    animatePose(progress:number){
      bones.forEach((bone,i)=>{bone.position.copy(rest[i].p);bone.quaternion.copy(rest[i].q);bone.scale.copy(rest[i].s)});
      magazine.position.copy(magRest);magazine.rotation.set(0,0,0);bolt.position.copy(boltRest);
      if(progress<0)return;
      const out=progress<.18?0:progress<.4?(progress-.18)/.22:progress<.52?1:progress<.72?1-(progress-.52)/.2:0;
      magazine.position.y-=out*.5;magazine.position.z+=out*.09;
      root.updateMatrixWorld(true);
      const reach=THREE.MathUtils.smoothstep(progress,0,.18)*(1-THREE.MathUtils.smoothstep(progress,.72,.92));
      const grip=magazine.getObjectByName('MagazineGripSocket')!;
      const target=root.localToWorld(left.wrist.clone()).lerp(world(grip),reach);
      const rightTarget=root.localToWorld(right.wrist.clone());
      solve(left,target,-1);solve(right,rightTarget,1);
      if(progress>.78&&progress<.9)bolt.position.z+=Math.sin((progress-.78)/.12*Math.PI)*.08;
    }};
}
