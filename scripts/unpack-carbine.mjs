// Offline preparation only. Install pinned tooling outside the game:
// npm install --prefix /tmp/onsite-asset-tools --no-audit --no-fund @gltf-transform/core@4.2.1 @gltf-transform/extensions@4.2.1 @gltf-transform/functions@4.2.1 meshoptimizer@0.25.0
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
const require=createRequire('/tmp/onsite-asset-tools/package.json');
const {NodeIO}=require('@gltf-transform/core');
const {ALL_EXTENSIONS}=require('@gltf-transform/extensions');
const {dequantize}=require('@gltf-transform/functions');
const {MeshoptDecoder}=require('meshoptimizer');
await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(resolve('public/models/donors/m4a1-hands.glb'));await doc.transform(dequantize());
for(const ext of doc.getRoot().listExtensionsUsed())if(ext.extensionName==='EXT_meshopt_compression')ext.dispose();
await io.write('/tmp/onsite-rifle-unpacked.glb',doc);
