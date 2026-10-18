"""Import reviewed CC0 dressing from the pinned local IRONLINE reference."""
import json,hashlib,shutil,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'research/reference-clones/ironline/public/assets'
OUT=ROOT/'public/models/donors';records=json.loads((OUT/'provenance.json').read_text())
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ONSITE-asset-review/1.0'}),timeout=45)as r:return r.read()
for name in ['cardboard_box_01','old_tyre','cement_bag','rusted_wheel_rim_01','wooden_crate_02']:
 info=json.loads(get('https://api.polyhaven.com/info/'+name));src=SRC/f'models/props/{name}/{name}.glb';dst=OUT/(name+'.glb');shutil.copyfile(src,dst)
 rec=dict(file=str(dst.relative_to(ROOT/'public')),bytes=dst.stat().st_size,sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),donor='https://github.com/cktang88/3d-fps',commit='130ac2a5c856401ec36e7d35afcfefe40c5801f4',donorPath=str(src.relative_to(SRC.parent.parent)),creators=info['authors'],licence='CC0-1.0',sources=['https://polyhaven.com/a/'+name,'https://polyhaven.com/license'],checked='2026-10-18',evidence={'originalMetadata':info},modifications='Copied unchanged; placed in Blender and runtime.')
 records=[r for r in records if r['file']!=rec['file']]+[rec];print(name,rec['bytes'],flush=True)
(OUT/'provenance.json').write_text(json.dumps(records,indent=2)+'\n')
license_text=get('https://docs.ambientcg.com/license/').decode()
assert 'CC0' in license_text
out=ROOT/'public/materials/detail';out.mkdir(parents=True,exist_ok=True);maps=[]
for name in ['Ground110','Leaking003']:
 for src in (SRC/'textures'/name).glob('*.webp'):
  dest=out/(name+'-'+src.name);shutil.copyfile(src,dest)
  maps.append(dict(file=str(dest.relative_to(ROOT/'public')),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),bytes=dest.stat().st_size,source='https://ambientcg.com/a/'+name,author='ambientCG / Lennart Demes',license='CC0-1.0',licenseURL='https://docs.ambientcg.com/license/',donorPath=str(src.relative_to(SRC.parent.parent)),donorCommit='130ac2a5c856401ec36e7d35afcfefe40c5801f4',modifications='IRONLINE WebP conversion; copied unchanged.'))
(out/'provenance.json').write_text(json.dumps({'checked':'2026-10-18','assets':maps},indent=2)+'\n');print('CC0 material files',len(maps),flush=True)
