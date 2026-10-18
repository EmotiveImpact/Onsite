"""Repack Blender's embedded PNG maps as runtime WebP without retaining duplicate image bytes."""
import struct,json,io,hashlib
from pathlib import Path
from PIL import Image
p=Path('public/models/onsite-carbine.glb');data=p.read_bytes();jl=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+jl]);old=data[28+jl:];replacements={}
colour=set()
for m in g['materials']:
 t=m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
 if t:
  texture=g['textures'][t['index']];colour.add(texture.get('source',texture.get('extensions',{}).get('EXT_texture_webp',{}).get('source')))
for index,image in enumerate(g.get('images',[])):
 view=g['bufferViews'][image['bufferView']];raw=old[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];im=Image.open(io.BytesIO(raw));out=io.BytesIO();im.save(out,'WEBP',quality=90 if index in colour else 94,method=6);replacements[image['bufferView']]=raw if image.get('mimeType')=='image/webp'and index in colour else out.getvalue();image['mimeType']='image/webp'
binary=bytearray()
for i,view in enumerate(g['bufferViews']):
 raw=replacements.get(i,old[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])
 while len(binary)%4:binary.append(0)
 view['byteOffset']=len(binary);view['byteLength']=len(raw);binary.extend(raw)
for texture in g['textures']:
 if 'source'in texture:texture.setdefault('extensions',{})['EXT_texture_webp']={'source':texture.pop('source')}
for key in ['extensionsUsed','extensionsRequired']:
 g.setdefault(key,[])
 if 'EXT_texture_webp'not in g[key]:g[key].append('EXT_texture_webp')
g['buffers'][0]['byteLength']=len(binary)
while len(binary)%4:binary.append(0)
j=json.dumps(g,separators=(',',':')).encode()
while len(j)%4:j+=b' '
p.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
m=Path('public/models/onsite-carbine.json');r=json.loads(m.read_text());r.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),imageEncoding='Colour WebP quality 90; normal and ARM WebP quality 94; PNG maps retained in Blender source.');m.write_text(json.dumps(r,indent=2)+'\n');print('Runtime carbine:',r['bytes'],'bytes')
