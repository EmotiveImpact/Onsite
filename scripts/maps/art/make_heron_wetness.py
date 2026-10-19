"""Original deterministic wetness mask and broken lamp streak; no downloaded pixels.

The mask repeats over 11 metres. This is authored surface variation, not a height scan.
Run from the repo root: python3 scripts/maps/art/make_heron_wetness.py
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'public/materials/heron/decals'
rng = np.random.default_rng(741)
n = 512
y, x = np.mgrid[0:n, 0:n] / n
field = np.zeros((n, n))
for frequency, amplitude in [(1, .35), (2, .23), (4, .15), (8, .06), (16, .025), (32, .012)]:
    for _ in range(4):
        kx, ky = rng.integers(-frequency, frequency + 1, 2)
        if kx == ky == 0:
            kx = 1
        field += amplitude * np.cos(2*np.pi*(kx*x+ky*y) + rng.random()*2*np.pi)/4
field = np.clip(.5 + field*1.75, 0, 1)
OUT.mkdir(parents=True, exist_ok=True)
Image.fromarray((field*255).astype('uint8')).save(OUT/'wetness-mask.webp', lossless=True)
# Transparent warm reflection with fine horizontal breaks, rather than a smooth orange oval.
u, v = (x-.5)*2, (y-.5)*2
envelope = np.exp(-u*u*7) * np.maximum(0, 1-v*v)**1.9
ripple = .35+.65*(.5+.5*np.sin(y*510+np.sin(x*37)*3))**2
alpha = np.clip(envelope*ripple*(.65+.35*field)*180, 0, 255)
rgba = np.zeros((n,n,4), dtype='uint8')
rgba[:,:,:3] = [255,183,100]
rgba[:,:,3] = alpha.astype('uint8')
Image.fromarray(rgba).save(OUT/'lamp-streak.webp', lossless=True)
manifest = {'provenance':'Original ONSITE procedural NumPy/Pillow work, seed 741. No external image source.',
            'script':'scripts/maps/art/make_heron_wetness.py', 'maskCoverageMetres':11,
            'files':{name:{'bytes':(OUT/name).stat().st_size,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()}
                     for name in ['wetness-mask.webp','lamp-streak.webp']}}
(OUT/'wetness-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
