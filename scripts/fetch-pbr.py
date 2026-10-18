"""Fetch CC0 Poly Haven maps with a reproducible provenance manifest. No donor archive assets."""
import urllib.request,json,hashlib,concurrent.futures,io
from pathlib import Path
from PIL import Image
OUT=Path('public/materials/pbr');OUT.mkdir(parents=True,exist_ok=True)
sets={'brick':'brick_wall_001','concrete':'concrete_wall_008','asphalt':'asphalt_02','paving':'concrete_floor_worn_001','steel':'corrugated_iron_02'}
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ONSITE-local-asset-review/1.0'}),timeout=60).read()
def run(item):
 role,asset=item;meta=json.loads(get('https://api.polyhaven.com/files/'+asset));record={'role':role,'asset':asset,'page':'https://polyhaven.com/a/'+asset,'license':'CC0-1.0','licenseURL':'https://polyhaven.com/license','maps':{}}
 for channel,key in [('color','Diffuse'),('normal','nor_gl'),('arm','arm')]:
  entry=meta[key]['1k']['jpg'];data=get(entry['url']);im=Image.open(io.BytesIO(data)).convert('RGB');im.thumbnail((1024,1024));path=OUT/f'{role}-{channel}.webp';im.save(path,'WEBP',quality=88,method=6)
  record['maps'][channel]={'url':entry['url'],'sourceSHA256':hashlib.sha256(data).hexdigest(),'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
 return record
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for future in [pool.submit(run,item) for item in sets.items()]:
  try:r=future.result();records.append(r);print(r['role'],'downloaded')
  except Exception as e:print('FAILED',str(e))
(OUT/'provenance.json').write_text(json.dumps({'retrieved':'2026-10-18','normalConvention':'OpenGL +Y','armChannels':'R ambient occlusion, G roughness, B metallic','processing':'JPEG sources converted to WebP quality 88, maximum 1024px; no painted/generated content','sources':records},indent=2)+'\n')
assert len(records)==len(sets)
