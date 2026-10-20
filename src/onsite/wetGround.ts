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

export const wetGroundNames=new Set(['hr_asphalt','hr_paving','hr_pavers_red','hr_court','hr_concrete_cast']);

/** One shared 512px mask, in world metres: damp aggregate between shallow pools.
 * PBR sky/specular response only; this does not pretend to reflect scene objects. */
export function applyWetGround(material:THREE.MeshStandardMaterial,mask:THREE.Texture){
 material.envMapIntensity=material.name==='hr_concrete_cast'?1.2:1.7;
 const previous=material.onBeforeCompile,cache=material.customProgramCacheKey();
 material.onBeforeCompile=function(shader,renderer){
  previous.call(this,shader,renderer);
  shader.uniforms.onsiteWetMask={value:mask};
  shader.vertexShader='varying vec3 onsiteWetPosition;\nvarying vec3 onsiteWetNormal;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>',`#include <project_vertex>
   vec4 wetPosition=vec4(transformed,1.0);
   #ifdef USE_INSTANCING
    wetPosition=instanceMatrix*wetPosition;
   #endif
   onsiteWetPosition=(modelMatrix*wetPosition).xyz;
   onsiteWetNormal=inverseTransformDirection(transformedNormal,viewMatrix);`);
  shader.fragmentShader='uniform sampler2D onsiteWetMask;\nvarying vec3 onsiteWetPosition;\nvarying vec3 onsiteWetNormal;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
   float wetMask=texture2D(onsiteWetMask,onsiteWetPosition.xz/11.0).r;
   float wetPool=smoothstep(.38,.72,wetMask)*smoothstep(.65,.98,normalize(onsiteWetNormal).y);
   roughnessFactor=mix(max(roughnessFactor,.42),.11,wetPool);
   diffuseColor.rgb*=mix(.92,.68,wetPool);`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
   normal=normalize(mix(normal,nonPerturbedNormal,wetPool*.84));`);
 };
 material.customProgramCacheKey=()=>cache+'|onsite-wet-ground-v2';
}
