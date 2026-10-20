import {readFileSync} from 'node:fs'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import type {RobotAsset} from '../src/wwb/game/robot'

let cached:Promise<RobotAsset>|undefined
/** Real authored skin, joints, pivots and geometry; only browser image decoding is omitted. */
export function operatorFixture(){
 return cached??=(async()=>{
  const source=readFileSync('public/models/onsite-operator.glb'),length=source.readUInt32LE(12)
  const json=JSON.parse(source.subarray(20,20+length).toString())
  delete json.images;delete json.textures
  for(const m of json.materials){
   delete m.normalTexture;delete m.occlusionTexture;delete m.emissiveTexture
   delete m.pbrMetallicRoughness?.baseColorTexture;delete m.pbrMetallicRoughness?.metallicRoughnessTexture
  }
  const encoded=Buffer.from(JSON.stringify(json)),padded=Buffer.alloc(Math.ceil(encoded.length/4)*4,32);encoded.copy(padded)
  const bin=source.subarray(20+length),head=Buffer.alloc(20)
  head.writeUInt32LE(0x46546c67,0);head.writeUInt32LE(2,4);head.writeUInt32LE(20+padded.length+bin.length,8)
  head.writeUInt32LE(padded.length,12);head.writeUInt32LE(0x4e4f534a,16)
  const bytes=Uint8Array.from(Buffer.concat([head,padded,bin]))
  return {scene:(await new GLTFLoader().parseAsync(bytes.buffer,'')).scene,clips:[]}
 })()
}
