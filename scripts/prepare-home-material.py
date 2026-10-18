"""Encode the retained ONSITE stock-brick colour source for runtime; no image painting."""
from pathlib import Path
import hashlib,json
from PIL import Image
root=Path(__file__).resolve().parents[1]
source=root/'assets/textures/source-30/01-london-stock-brick-color.png'
out=root/'public/materials/homes';out.mkdir(exist_ok=True)
target=out/'stock-color.webp';Image.open(source).save(target,'WEBP',quality=90,method=6)
(out/'provenance.json').write_text(json.dumps({'source':str(source.relative_to(root)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'runtime':str(target.relative_to(root)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'processing':'Original retained generated colour image, WebP encoding only. No normal/height/roughness scan claim. Runtime uses constant roughness and geometric occlusion.','coverageMetres':1.05},indent=2)+'\n')
