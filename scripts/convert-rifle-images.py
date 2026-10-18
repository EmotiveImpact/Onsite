"""Transcode embedded WebP to PNG for this Blender build's glTF importer.
Lossless colour-space-preserving format conversion, not painting. Runtime source stays unchanged.
"""
import struct,json,io
from pathlib import Path
from PIL import Image
p=Path('/tmp/onsite-rifle-unpacked.glb');data=p.read_bytes();jl=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+jl]);bo=20+jl+8;binary=bytearray(data[bo:])
for image in g.get('images',[]):
 if image.get('mimeType')!='image/webp':continue
 view=g['bufferViews'][image['bufferView']];raw=bytes(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);im=Image.open(io.BytesIO(raw));out=io.BytesIO();im.save(out,'PNG');png=out.getvalue()
 while len(binary)%4:binary.append(0)
 image['bufferView']=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(png)});binary.extend(png);image['mimeType']='image/png'
for texture in g.get('textures',[]):
 ext=texture.get('extensions',{}).pop('EXT_texture_webp',None)
 if ext:texture['source']=ext['source']
 if not texture.get('extensions'):texture.pop('extensions',None)
for key in ['extensionsRequired','extensionsUsed']:
 if key in g:g[key]=[x for x in g[key]if x!='EXT_texture_webp']
g['buffers'][0]['byteLength']=len(binary)
while len(binary)%4:binary.append(0)
j=json.dumps(g,separators=(',',':')).encode()
while len(j)%4:j+=b' '
p.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
print('Converted',len(g.get('images',[])),'embedded images for Blender')
