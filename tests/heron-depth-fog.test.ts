import test from 'node:test'
import assert from 'node:assert/strict'
import * as THREE from 'three'
import {HERON_DEPTH_FOG,heronFogFactor,heronFogOpticalDepth,installHeronDepthFog} from '../src/onsite/HeronDepthFog.ts'
import {applyWetGround} from '../src/onsite/wetGround.ts'
import {applyHeronSurfaceResponse} from '../src/onsite/heronSurfaceResponse.ts'

test('Near fog preserves street and basement contrast; distant layers remain distinct',()=>{
 for(const eye of [-1.96,-1.38,1.04,1.62,13.62]){
  const floor=eye<0?-3:eye>10?12:0;
  assert(heronFogFactor(10,eye,eye)<=.02,`horizontal at ${eye}m`);
  assert(heronFogFactor(10,eye,floor)<=.02,`floorward at ${eye}m`);
 }
 const factors=[10,40,60,150,300,470].map(d=>heronFogFactor(d));
 assert(factors[1]>.05&&factors[2]<.20,'40–60m retains contrast');
 assert(factors[3]>.40&&factors[3]<.65,'150m retains skyline separation');
 assert(factors.every((n,i)=>i===0||n>factors[i-1]),'far layers progressively dissolve');
 assert(factors[5]<=HERON_DEPTH_FOG.maxOpacity);
 assert(heronFogFactor(150,13.62)<heronFogFactor(150,1.62),'elevated facades sit above ground haze');
});

test('Optical depth matches independent density integration for horizontal, upward and downward rays',()=>{
 // Midpoint quadrature of the density profile independently checks the closed form.
 // These estate-height rays stay within the donor's art-directed attenuation caps.
 const p=HERON_DEPTH_FOG;
 for(const [distance,eye,target]of [[50,1.75,1.75],[10,1.75,11.75],[10,8,-2],[60,1.75,12],[60,8,1.75]]){
  let aerial=0,ground=0;
  const samples=10000;
  for(let i=0;i<samples;i++){
   const height=eye+(target-eye)*(i+.5)/samples;
   aerial+=Math.exp(-(height-p.baseHeight)*p.aerialHeightFalloff)/samples;
   ground+=Math.exp(-(height-p.baseHeight)*p.heightFalloff)/samples;
  }
  const expected=(.007*p.aerialScale*distance*aerial)**2+.007*p.groundScale*distance*ground;
  assert(Math.abs(heronFogOpticalDepth(distance,eye,target)-expected)<1e-9,`${eye} -> ${target}`);
 }
 assert(heronFogOpticalDepth(10,1.75,-8.25)>heronFogOpticalDepth(10,1.75,11.75));
});

test('Horizontal limit, exponent bounds, zero length and long vertical rays stay finite and continuous',()=>{
 const horizontal=heronFogOpticalDepth(50,1.75,1.75);
 for(const delta of [-1e-8,1e-8])assert(Math.abs(heronFogOpticalDepth(50,1.75,1.75+delta)-horizontal)<1e-9);
 for(const falloff of [HERON_DEPTH_FOG.heightFalloff,HERON_DEPTH_FOG.aerialHeightFalloff]){
  for(const limit of [-16,-.001,.001,16]){
   const below=heronFogOpticalDepth(200,1.75,1.75+(limit-1e-9)/falloff);
   const above=heronFogOpticalDepth(200,1.75,1.75+(limit+1e-9)/falloff);
   assert(Math.abs(below-above)/Math.max(1,below)<1e-7,`continuous at ${limit}/${falloff}`);
  }
 }
 for(const [distance,eye,target]of [[0,1.75,1.75],[10000,10000,-10000],[10000,-10000,10000],[10000,10000,10000]]){
  const depth=heronFogOpticalDepth(distance,eye,target),factor=heronFogFactor(distance,eye,target);
  assert(Number.isFinite(depth)&&depth>=0);
  assert(Number.isFinite(factor)&&factor>=0&&factor<=HERON_DEPTH_FOG.maxOpacity);
 }
 assert.equal(heronFogOpticalDepth(0),0);
 assert.equal(heronFogOpticalDepth(100,1.75,-10,0),0);
});

function shaderFor(material:THREE.Material,name:keyof typeof THREE.ShaderLib){
 const lib=THREE.ShaderLib[name];
 const shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:THREE.UniformsUtils.clone(lib.uniforms)} as Parameters<THREE.Material['onBeforeCompile']>[0];
 material.onBeforeCompile(shader,{} as THREE.WebGLRenderer);
 return shader;
}

test('Scoped fog composes with surface response/wet ground and preserves default/custom cache identities',()=>{
 const scene=new THREE.Scene(),material=new THREE.MeshStandardMaterial();
 applyHeronSurfaceResponse(material);
 applyWetGround(material,new THREE.Texture());
 const preFogKey=material.customProgramCacheKey();
 scene.add(new THREE.Mesh(new THREE.PlaneGeometry(),material));
 const originalChunks={...THREE.ShaderChunk};
 assert.equal(installHeronDepthFog(scene),1);
 const shader=shaderFor(material,'standard');
 assert(shader.uniforms.onsiteWetMask);
 assert(shader.vertexShader.includes('onsiteWetPosition=(modelMatrix*wetPosition).xyz'));
 assert(shader.fragmentShader.includes('roughnessFactor=mix('));
 assert(shader.fragmentShader.includes('float onsiteFarNormal='));
 assert(shader.fragmentShader.includes('roughnessFactor=max(roughnessFactor,onsiteSoffit*.9)'));
 assert(shader.fragmentShader.includes('heronHeightIntegral'));
 assert.equal(material.customProgramCacheKey(),preFogKey+'|onsite-heron-depth-fog-v1');
 const version=material.version,compile=material.onBeforeCompile;
 assert.equal(installHeronDepthFog(scene),0);
 assert.equal(material.version,version);assert.equal(material.onBeforeCompile,compile);
 assert.deepEqual(THREE.ShaderChunk,originalChunks,'global shader chunks are untouched');

 const otherScene=new THREE.Scene(),other=new THREE.MeshStandardMaterial();
 otherScene.add(new THREE.Mesh(new THREE.BoxGeometry(),other));
 assert(!shaderFor(other,'standard').fragmentShader.includes('heronHeightIntegral'));
 const first=new THREE.MeshBasicMaterial(),second=new THREE.MeshBasicMaterial();
 first.onBeforeCompile=function(shader){shader.uniforms.first={value:1}};
 second.onBeforeCompile=function(shader){shader.uniforms.second={value:2}};
 otherScene.add(new THREE.Mesh(new THREE.BoxGeometry(),[first,second]));
 installHeronDepthFog(otherScene);
 assert.notEqual(first.customProgramCacheKey(),second.customProgramCacheKey(),'earlier hooks cannot share an incorrect cached program');
 let customVersion=1;
 const dynamic=new THREE.MeshBasicMaterial();dynamic.customProgramCacheKey=()=>`dynamic-${customVersion}`;
 otherScene.add(new THREE.Mesh(new THREE.BoxGeometry(),dynamic));installHeronDepthFog(otherScene);
 customVersion++;
 assert.equal(dynamic.customProgramCacheKey(),'dynamic-2|onsite-heron-depth-fog-v1');
});

test('Meshes, instancing, points and sprites use their existing view position; linear Fog stays stock',()=>{
 const scene=new THREE.Scene();
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
 const instances=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial(),2);
 const points=new THREE.Points(new THREE.BufferGeometry(),new THREE.PointsMaterial());
 const sprite=new THREE.Sprite(new THREE.SpriteMaterial());
 const sky=new THREE.Mesh(new THREE.SphereGeometry(),new THREE.MeshBasicMaterial({fog:false}));
 const custom=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.ShaderMaterial({fog:true}));
 const skyCompile=sky.material.onBeforeCompile,customCompile=custom.material.onBeforeCompile;
 scene.add(mesh,instances,points,sprite,sky,custom);
 assert.equal(installHeronDepthFog(scene),4);
 for(const [material,lib]of [[mesh.material,'standard'],[instances.material,'basic'],[points.material,'points'],[sprite.material,'sprite']] as const){
  const shader=shaderFor(material,lib);
  assert(shader.vertexShader.includes('transpose( mat3( viewMatrix ) ) * mvPosition.xyz'));
  assert(shader.vertexShader.includes('#include <fog_vertex>'));
  assert(shader.fragmentShader.includes('#else\n // Preserve Three\'s linear Fog and no-fog behaviour exactly.\n #include <fog_fragment>'));
 }
 assert.equal(sky.material.onBeforeCompile,skyCompile);
 assert.equal(custom.material.onBeforeCompile,customCompile);

 // Independently reconstruct an instanced point through a translated/rotated camera.
 const camera=new THREE.PerspectiveCamera();camera.position.set(8,4,-7);camera.rotation.set(.2,-.6,.1);camera.updateMatrixWorld();
 const instance=new THREE.Matrix4().makeTranslation(-3,6,9);
 const model=new THREE.Matrix4().compose(new THREE.Vector3(20,2,-1),new THREE.Quaternion().setFromEuler(new THREE.Euler(0,.8,0)),new THREE.Vector3(2,2,2));
 const world=new THREE.Vector3(.5,.25,-.75).applyMatrix4(instance).applyMatrix4(model);
 const view=world.clone().applyMatrix4(camera.matrixWorldInverse);
 const reconstructed=view.applyMatrix3(new THREE.Matrix3().setFromMatrix4(camera.matrixWorldInverse).transpose()).add(camera.position);
 assert(reconstructed.distanceTo(world)<1e-12);
});
