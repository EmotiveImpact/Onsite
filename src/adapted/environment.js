/** Adapted from WWB src/game/arena.ts (4cf34e8), MIT © 2026 Jeevesh Singale.
 * Static geometry batching + chain-link canvas. London dimensions/materials are ONSITE.
 * No upstream bundled images/models. Full notice: public/licenses/WWB-MIT.txt.
 */
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
export function batchStatic(scene,meshes){
  const pending=new Map();
  for(const mesh of meshes){
    mesh.updateMatrix();const g=(mesh.geometry.index?mesh.geometry.toNonIndexed():mesh.geometry.clone()).applyMatrix4(mesh.matrix);
    for(const name of Object.keys(g.attributes))if(!['position','normal','uv'].includes(name))g.deleteAttribute(name);
    const list=pending.get(mesh.material)??[];list.push(g);pending.set(mesh.material,list);scene.remove(mesh);mesh.geometry.dispose();
  }
  for(const [material,list]of pending){
    const merged=mergeGeometries(list,false);if(!merged)continue;merged.computeBoundingSphere();
    const mesh=new THREE.Mesh(merged,material);mesh.castShadow=true;mesh.receiveShadow=true;mesh.matrixAutoUpdate=false;scene.add(mesh);
    list.forEach(g=>g.dispose());
  }
}
export function chainLinkTexture(){
  const c=document.createElement('canvas');c.width=c.height=64;
  const g=c.getContext('2d');g.clearRect(0,0,64,64);g.strokeStyle='rgba(255,255,255,1)';g.lineWidth=2;
  g.beginPath();g.moveTo(0,32);g.lineTo(32,0);g.lineTo(64,32);g.lineTo(32,64);g.closePath();g.stroke();
  const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;
}
