"""Import the individually credited assets, never a donor's whole public tree.
Pinned IRONLINE derivatives; re-check original authors' public metadata and retain hashes.
"""
import hashlib, json, shutil, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/reference-clones/ironline'
SHA = '130ac2a5c856401ec36e7d35afcfefe40c5801f4'
OUT = ROOT / 'public/models/donors'
OUT.mkdir(parents=True, exist_ok=True)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'ONSITE-local-asset-review/1.0'})) as r:
        return json.load(r)

records = []
def copy(rel, name, creators, licence, sources, evidence):
    src = SOURCE / 'public/assets' / rel
    dest = OUT / name
    shutil.copyfile(src, dest)
    records.append(dict(file=str(dest.relative_to(ROOT / 'public')), bytes=dest.stat().st_size,
        sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), donor='https://github.com/cktang88/3d-fps',
        commit=SHA, donorPath='public/assets/' + rel, creators=creators, licence=licence,
        sources=sources, checked='2026-10-18', evidence=evidence,
        modifications='Upstream simplified/re-posed/WebP derivative; copied unchanged. Runtime placement/tint only.'))

for name in ['covered_car', 'rollershutter_door', 'metal_trash_can', 'trashbag', 'exterior_aircon_unit',
             'concrete_road_barrier_02', 'street_lamp_01']:
    info = get('https://api.polyhaven.com/info/' + name)
    copy(f'models/props/{name}/{name}.glb', name + '.glb', info['authors'], 'CC0-1.0',
         ['https://polyhaven.com/a/' + name, 'https://polyhaven.com/license'],
         {'originalMetadata': info, 'donorCredits': 'README.md#credits--licences; World / Props'})

ids = ['40d8ef818c7549a896371cbb1f64fec6', '9452ce4cddde4110a4fd73e555a8e412', '94be8385c402474cacd39bc096c6ca14']
metadata = [get('https://api.sketchfab.com/v3/models/' + uid) for uid in ids]
assert all(m['license']['slug'] == 'by' for m in metadata)
copy('models/fp/m4a1.glb', 'm4a1-hands.glb', [m['user']['displayName'] for m in metadata], 'CC-BY-4.0',
     ['https://sketchfab.com/3d-models/' + uid for uid in ids] + ['https://creativecommons.org/licenses/by/4.0/'],
     {'originalMetadata': [{k:m[k] for k in ['uid', 'name', 'license', 'user']} for m in metadata],
      'donorCredits': 'README.md#credits--licences; First-person weapons. Static grip_vgrip pose only; NO Fab motion JSON or reload clips imported.'})
for image in ['arms_basecolor.webp', 'arms_normal.webp']:
    copy('models/fp/'+image, image, ['DJMaesen / bumstrum'], 'CC-BY-4.0',
         ['https://sketchfab.com/3d-models/9452ce4cddde4110a4fd73e555a8e412', 'https://creativecommons.org/licenses/by/4.0/'],
         {'donorCredits':'README.md#credits--licences; external arm texture referenced by m4a1.glb'})
info = get('https://api.polyhaven.com/info/bambanani_sunset')
copy('hdr/bambanani_sunset_2k.hdr', 'bambanani_sunset_2k.hdr', info['authors'], 'CC0-1.0',
     ['https://polyhaven.com/a/bambanani_sunset', 'https://polyhaven.com/license'], {'originalMetadata':info})
(OUT/'provenance.json').write_text(json.dumps(records, indent=2)+'\n')
print('Imported', len(records), 'assets;', sum(r['bytes'] for r in records), 'bytes')
