"""Transcode the architecture PBR library to KTX2, retaining every WebP fallback.

GLTFPACK=/path/to/native/gltfpack python3 scripts/maps/art/compress_heron_textures.py
Requires native gltfpack 0.22 with BasisU (the npm/WASM build cannot compress textures).
Existing generated/credited texture provenance stays in TEXTURES.md; this only changes encoding.
"""
from pathlib import Path
from PIL import Image
import base64, hashlib, json, os, struct, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[3]
PUBLIC=ROOT/'public'
OUT=PUBLIC/'materials/heron/ktx2'
PACK=os.environ.get('GLTFPACK','gltfpack')
LIB=json.loads((PUBLIC/'materials/heron/runtime-materials.json').read_text())
roles={}
for entry in LIB.values():
    for prop,role in [('map','colour'),('emissiveMap','colour'),('normalMap','normal'),('ormMap','orm')]:
        if entry.get(prop):
            url=entry[prop]
            if url in roles and roles[url]!=role:raise ValueError('Conflicting colour spaces: '+url)
            roles[url]=role
OUT.mkdir(parents=True,exist_ok=True)

def sha(data):return hashlib.sha256(data).hexdigest()
def read_glb(path):
    b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0]
    return json.loads(b[20:20+n]),b[28+n:]

entries={}
with tempfile.TemporaryDirectory(prefix='onsite-ktx-') as tmp:
    tmp=Path(tmp)
    # One tiny source mesh exercises gltfpack's proper colour/normal/ORM handling.
    blob=struct.pack('<24f',0,0,0,1,0,0,0,1,0, 0,0,1,0,0,1,0,0,1, 0,0,1,0,0,1)
    for role in ['colour','normal','orm']:
        urls=sorted(u for u,r in roles.items() if r==role)
        j={'asset':{'version':'2.0'},'buffers':[{'uri':'data:application/octet-stream;base64,'+base64.b64encode(blob).decode(),'byteLength':len(blob)}],
           'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':36},{'buffer':0,'byteOffset':72,'byteLength':24}],
           'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':[1,1,0]},
                        {'bufferView':1,'componentType':5126,'count':3,'type':'VEC3'},
                        {'bufferView':2,'componentType':5126,'count':3,'type':'VEC2'}],
           'images':[],'textures':[],'materials':[],'meshes':[],'nodes':[], 'scenes':[{'nodes':list(range(len(urls)))}],'scene':0}
        by_name={}
        for i,url in enumerate(urls):
            source=PUBLIC/url.lstrip('/'); data=source.read_bytes()
            name=source.stem+'-'+sha(url.encode())[:8]
            im=Image.open(source); im.save(tmp/(name+'.png'))
            w,h=im.size
            entries[url]={'url':'/materials/heron/ktx2/'+name+'.ktx2','role':role,'width':w,'height':h,'sourceWidth':w,'sourceHeight':h,
                          'sourceSHA256':sha(data),'sourceBytes':len(data),'rgba8MipBytes':sum(max(1,w>>k)*max(1,h>>k)*4 for k in range(max(w,h).bit_length()))}
            by_name[name]=url
            j['images'].append({'uri':name+'.png','name':name});j['textures'].append({'source':i})
            mat={'name':name,'pbrMetallicRoughness':{'metallicFactor':0,'roughnessFactor':1}}
            if role=='colour':mat['pbrMetallicRoughness']['baseColorTexture']={'index':i}
            elif role=='normal':mat['normalTexture']={'index':i}
            else:mat['pbrMetallicRoughness'].update(metallicFactor=1,metallicRoughnessTexture={'index':i});mat['occlusionTexture']={'index':i}
            j['materials'].append(mat)
            j['meshes'].append({'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'material':i}]})
            j['nodes'].append({'mesh':i,'name':name,'translation':[i*2,0,0]})
        src=tmp/(role+'.gltf');dst=tmp/(role+'.glb');src.write_text(json.dumps(j))
        subprocess.run([PACK,'-i',str(src),'-o',str(dst),'-tc','-tq','8','-tj','2','-kn','-km']+(['-tu'] if role=='normal' else []),check=True)
        result,binary=read_glb(dst)
        for im in result['images']:
            if im.get('mimeType')!='image/ktx2':raise ValueError('Encoder did not produce KTX2: '+str(im))
            url=by_name[im['name']];entry=entries[url];view=result['bufferViews'][im['bufferView']]
            start=view.get('byteOffset',0);data=binary[start:start+view['byteLength']]
            if data[:12]!=b'\xabKTX 20\xbb\r\n\x1a\n':raise ValueError('Invalid KTX2')
            target=PUBLIC/entry['url'].lstrip('/');target.write_bytes(data)
            # gltfpack rounds non-multiple-of-four images to compression block dimensions.
            entry.update(width=struct.unpack_from('<I',data,20)[0],height=struct.unpack_from('<I',data,24)[0],bytes=len(data),sha256=sha(data),encoding='UASTC + Zstd' if role=='normal' else 'ETC1S / BasisLZ')
        print(role,len(urls),'textures',flush=True)

manifest={'provenance':'Encoding-only derivatives of the existing ONSITE architecture PBR library; source provenance in docs/maps/heron-reach-32/art/TEXTURES.md. Original WebPs preserved.',
          'encoder':'meshoptimizer gltfpack v0.22 native, MIT; Basis Universal, Apache-2.0',
          'encoderRelease':'https://github.com/zeux/meshoptimizer/releases/tag/v0.22',
          'encoderSHA256':sha(Path(PACK).read_bytes()) if Path(PACK).is_file() else None,
          'entries':entries}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('TOTAL',len(entries),'textures;',sum(e['sourceBytes'] for e in entries.values()),'WebP bytes ->',sum(e['bytes'] for e in entries.values()),'KTX2 bytes')
