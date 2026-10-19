"""Hash the reproducible blueprint package and create an ignored transfer archive."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/maps/heron-reach-32/blueprints'
files=sorted(p for p in OUT.iterdir()if p.is_file()and p.name!='PACKAGE.json')
files += [ROOT/'assets/blender/maps/heron-reach-32-B01-guides.blend',OUT.parent/'map.json',OUT.parent/'validation.json',
          ROOT/'docs/concepts/onsite-london-fps.png',ROOT/'docs/concepts/MODELLING-NOTES.md',
          ROOT/'docs/concepts/TEXTURE-PACK-30.md']
files += sorted((ROOT/'scripts/maps').glob('*heron_blueprint*'))
spec=json.loads((OUT/'build-spec.json').read_text())
for name,key in [('coordination-check.json','buildSpecSha256'),('blender-guide-check.json','buildSpecSha256')]:
    record=json.loads((OUT/name).read_text())
    assert record[key]==hashlib.sha256((OUT/'build-spec.json').read_bytes()).hexdigest(),name+' is stale'
assert hashlib.sha256((OUT.parent/'map.json').read_bytes()).hexdigest()==spec['sourceSha256']
draw=json.loads((OUT/'drawing-check.json').read_text())
assert draw['pdfPages']==draw['pageSelections']==17
manifest=dict(issue='B01',status='Proposed game-environment build package; not a runtime level',
              files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in files])
(OUT/'PACKAGE.json').write_text(json.dumps(manifest,indent=2)+'\n')
dest=ROOT/'test-results/blueprints/ONSITE-HERON-REACH-B01-HANDOFF.zip'
dest.parent.mkdir(exist_ok=True,parents=True)
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    archive.writestr('START-HERE.md',
        '# ONSITE / Heron Reach B01\n\n'
        'Start with docs/maps/heron-reach-32/blueprints/CLAUDE-BUILD-BRIEF.md.\n'
        'Open the 17-sheet PDF in the same folder. The editable Blender guide is\n'
        'assets/blender/maps/heron-reach-32-B01-guides.blend.\n\n'
        'This archive preserves repository-relative paths. It contains the design\n'
        'package, its source scripts, metric map and original London visual reference.\n'
        'It is not the full Onsite runtime. Use the existing project checkout to\n'
        'integrate; preserve any newer Claude/game work. No final art or 32-player\n'
        'runtime readiness is implied. Read the guide omissions and validation limits.\n')
    for p in files+[OUT/'PACKAGE.json']:archive.write(p,str(p.relative_to(ROOT)))
with zipfile.ZipFile(dest)as archive:
    assert archive.testzip()is None
    for item in manifest['files']:
        assert hashlib.sha256(archive.read(item['path'])).hexdigest()==item['sha256']
print(json.dumps(dict(archive=str(dest.relative_to(ROOT)),bytes=dest.stat().st_size,
                     sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),files=len(files),integrity='all manifest hashes verified'),indent=2))
