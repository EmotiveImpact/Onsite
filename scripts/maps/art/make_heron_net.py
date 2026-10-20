"""Original seamless cord net, without repeating feather silhouettes. Pillow only."""
from pathlib import Path
import math, json, hashlib
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
size = 512
image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
for horizontal in [False, True]:
    for strand in range(-1, 9):
        points = []
        for t in range(-4, size+5, 2):
            bend = 2.4 * math.sin(t*math.tau/size + strand*math.pi/4)
            p = (t, strand*64+bend)
            points.append(p if horizontal else p[::-1])
        draw.line(points, fill=(17, 21, 19, 110), width=5)
        draw.line(points, fill=(42, 47, 43, 235), width=3)
        draw.line(points, fill=(61, 66, 59, 180), width=1)
output = ROOT/'public/materials/heron/decals/pigeon-net-clean.webp'
image.save(output, lossless=True, method=6)
manifest = {
    'provenance': 'Original ONSITE procedural cord net. No external image or edited source artwork.',
    'generator': 'scripts/maps/art/make_heron_net.py',
    'pixels': [size, size], 'cellsPerTile': 8,
    'purpose': 'Replaces repeated feather silhouettes in runtime netting; previous artwork and Blender source retained.',
    'output': str(output.relative_to(ROOT)), 'bytes': output.stat().st_size,
    'sha256': hashlib.sha256(output.read_bytes()).hexdigest()
}
output.with_name('net-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
