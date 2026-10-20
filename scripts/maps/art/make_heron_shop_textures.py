"""Prepare the project's own ChatGPT shop images for the existing material pipeline.

Source images remain untouched. Only resize/encode; provenance and hashes are recorded.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'docs/maps/heron-reach-32/art/generated/shops'
OUT=ROOT/'public/materials/heron/shops'
OUT.mkdir(parents=True,exist_ok=True)
files=[]
for name in ['corner-shop-interior','launderette-interior']:
    src=SRC/(name+'.png');dst=OUT/(name+'.webp')
    Image.open(src).convert('RGB').resize((1024,512),Image.Resampling.LANCZOS).save(dst,quality=88)
    files.append({'source':str(src.relative_to(ROOT)),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runtime':str(dst.relative_to(ROOT)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size,'size':[1024,512]})
(OUT/'manifest.json').write_text(json.dumps({'provenance':'ChatGPT images generated for ONSITE, supplied in this repository at dd803c9. No external photography or downloaded asset.','processing':'Resize to 1024 x 512 and WebP quality 88; no new painted content.','files':files},indent=2)+'\n')
