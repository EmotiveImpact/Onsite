import {BufferGeometry,Matrix3,Matrix4,Vector3} from 'three'

/** Make the grass blade's upper surface front-facing, without changing the source asset.
 * Call only for GRASS_CLUMP_A–D or WEED_TUFT_B's hr_grass_blade primitive.
 * The clone keeps UVs, normals, colours and triangle vertices;
 * already-upward triangles stay unchanged, including after an authored asset correction.
 * `local` maps the mesh's stored/quantised coordinates to its Y-up asset-root space.
 */
export function correctGrassWinding(source:BufferGeometry,local:Matrix4):BufferGeometry {
 return correctUpperFaces(source,local)
}

/** Correct the known foliage-builder winding errors without touching upright weed cards.
 * A/C rosette strips have authored up > .99; their crossed cards are around .919.
 * Check every transformed corner normal so mixed primitives retain their exact card indices.
 * Unrelated assets/materials retain the original geometry object. No source asset is mutated.
 */
export function correctFoliageWinding(source:BufferGeometry,local:Matrix4,asset:string,materialName:string):BufferGeometry {
 const material=materialName.replace(/\.\d+$/,'')
 if(material==='hr_grass_blade'&&(/^GRASS_CLUMP_[ABCD]$/.test(asset)||asset==='WEED_TUFT_B'))return correctGrassWinding(source,local)
 if(material==='hr_weed'&&(asset==='WEED_TUFT_A'||asset==='WEED_TUFT_C'))return correctUpperFaces(source,local,.98)
 return source
}

function correctUpperFaces(source:BufferGeometry,local:Matrix4,minNormalUp?:number):BufferGeometry {
 const geometry=source.clone(),index=geometry.index,p=geometry.getAttribute('position')
 if(!index||!p)return geometry
 const a=new Vector3(),b=new Vector3(),c=new Vector3(),face=new Vector3()
 const n=geometry.getAttribute('normal'),normalMatrix=new Matrix3().getNormalMatrix(local),normal=new Vector3()
 if(minNormalUp!==undefined&&!n)return geometry
 let changed=false
 for(let i=0;i+2<index.count;i+=3){
  const ia=index.getX(i),ib=index.getX(i+1),ic=index.getX(i+2)
  if(minNormalUp!==undefined&&![ia,ib,ic].every(id=>normal.fromBufferAttribute(n,id).applyNormalMatrix(normalMatrix).y>minNormalUp))continue
  a.fromBufferAttribute(p,ia).applyMatrix4(local)
  b.fromBufferAttribute(p,ib).applyMatrix4(local)
  c.fromBufferAttribute(p,ic).applyMatrix4(local)
  face.crossVectors(b.sub(a),c.sub(a))
  if(face.y<0){index.setX(i+1,ic);index.setX(i+2,ib);changed=true}
 }
 if(changed)index.needsUpdate=true
 return geometry
}
