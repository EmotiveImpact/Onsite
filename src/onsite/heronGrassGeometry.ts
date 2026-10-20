import {BufferGeometry,Matrix4,Vector3} from 'three'

/** Make the grass blade's upper surface front-facing, without changing the source asset.
 * Call only for GRASS_CLUMP_A–D. The clone keeps UVs, normals, colours and triangle vertices;
 * already-upward triangles stay unchanged, including after an authored asset correction.
 * `local` maps the mesh's stored/quantised coordinates to its Y-up asset-root space.
 */
export function correctGrassWinding(source:BufferGeometry,local:Matrix4):BufferGeometry {
 const geometry=source.clone(),index=geometry.index,p=geometry.getAttribute('position')
 if(!index||!p)return geometry
 const a=new Vector3(),b=new Vector3(),c=new Vector3(),face=new Vector3()
 let changed=false
 for(let i=0;i+2<index.count;i+=3){
  const ia=index.getX(i),ib=index.getX(i+1),ic=index.getX(i+2)
  a.fromBufferAttribute(p,ia).applyMatrix4(local)
  b.fromBufferAttribute(p,ib).applyMatrix4(local)
  c.fromBufferAttribute(p,ic).applyMatrix4(local)
  face.crossVectors(b.sub(a),c.sub(a))
  if(face.y<0){index.setX(i+1,ic);index.setX(i+2,ib);changed=true}
 }
 if(changed)index.needsUpdate=true
 return geometry
}
