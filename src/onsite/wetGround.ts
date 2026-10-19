import * as THREE from 'three'
import type {Solid} from './level'

/** Read existing support geometry without adding collision or changing navigation. */
export function surfaceBelow(x:number,y:number,z:number,surfaces:readonly Solid[]):number|null {
 let floor:number|null=null;
 for(const s of surfaces){
  const top=s.y+s.h/2;
  if(top>y-.35||Math.abs(x-s.x)>s.w/2||Math.abs(z-s.z)>s.d/2)continue;
  if(floor===null||top>floor)floor=top;
 }
 return floor;
}

export const wetGroundNames=new Set(['hr_asphalt','hr_paving','hr_pavers_red','hr_court']);

/** One shared 512px mask, in world metres: damp aggregate between shallow pools.
 * PBR sky/specular response only; this does not pretend to reflect scene objects. */
export function applyWetGround(material:THREE.MeshStandardMaterial,mask:THREE.Texture){
 material.envMapIntensity=2.1;
 material.onBeforeCompile=shader=>{
  shader.uniforms.onsiteWetMask={value:mask};
  shader.vertexShader='varying vec3 onsiteWetPosition;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>',`#include <project_vertex>
   vec4 wetPosition=vec4(transformed,1.0);
   #ifdef USE_INSTANCING
    wetPosition=instanceMatrix*wetPosition;
   #endif
   onsiteWetPosition=(modelMatrix*wetPosition).xyz;`);
  shader.fragmentShader='uniform sampler2D onsiteWetMask;\nvarying vec3 onsiteWetPosition;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
   float wetMask=texture2D(onsiteWetMask,onsiteWetPosition.xz/11.0).r;
   float wetPool=smoothstep(.38,.72,wetMask);
   roughnessFactor=mix(max(roughnessFactor,.37),.075,wetPool);
   diffuseColor.rgb*=mix(.92,.68,wetPool);`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
   normal=normalize(mix(normal,nonPerturbedNormal,wetPool*.84));`);
 };
 material.customProgramCacheKey=()=>'onsite-wet-ground-v1';
}
