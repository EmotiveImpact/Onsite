"""Original periodic PBR surfaces authored for ONSITE. Not conversions of concept art.
Requires numpy and Pillow. Colour is sRGB; normal (+Y/OpenGL) and roughness are data.
"""
from pathlib import Path
import numpy as np
from PIL import Image
import json,hashlib
OUT=Path(__file__).resolve().parents[1]/'public/materials';OUT.mkdir(parents=True,exist_ok=True)
N=512
Y,X=np.mgrid[0:N,0:N]/(N-1)
rng=np.random.default_rng(71)
# Periodic Fourier noise has identical values and derivatives on opposing boundaries.
def noise(freqs):
    a=np.zeros((N,N))
    for f in freqs:
        for j in range(3):
            k=int(rng.integers(1,f+1));l=int(rng.integers(1,f+1));phase=rng.uniform(0,2*np.pi)
            a+=np.sin(2*np.pi*(k*X+l*Y)+phase)/len(freqs)/3
    return a
fine=noise([40,70,100]);coarse=noise([2,4,8]);mid=noise([12,20,30])
def smooth(a):return np.clip(a,0,1)**2*(3-2*np.clip(a,0,1))
manifest=[]
for name in ['brick','stock','concrete','asphalt','paving','steel']:
    height=np.zeros((N,N));rough=np.ones((N,N))*.8
    if name in ['brick','stock']:
        row=np.floor(Y*16);bx=(X*4+(row%2)*.5)%1;by=(Y*16)%1
        edge=np.minimum(np.minimum(bx,1-bx)*.5,np.minimum(by,1-by)*.125)
        raised=smooth((edge-.005)/.008)
        color=np.array([.34,.17,.105]) if name=='brick' else np.array([.49,.39,.25])
        variation=.08*np.sin(2*np.pi*(np.floor(X*4+(row%2)*.5)%4)/4+row*1.7)
        base=color[None,None,:]+(variation+coarse*.055+fine*.07)[...,None]
        mortar=np.array([.35,.34,.31])+fine[...,None]*.035
        base=base*raised[...,None]+mortar*(1-raised[...,None]);height=raised*.006+fine*.001+mid*.0005;rough=.84+fine*.1
    elif name=='concrete':
        base=np.array([.43,.44,.43])+(coarse*.05+fine*.06)[...,None];height=fine*.0015+mid*.001;rough=.85+fine*.1
    elif name=='asphalt':
        base=np.array([.13,.145,.16])+(fine*.08+mid*.025)[...,None];height=fine*.002+mid*.0008;rough=.66+coarse*.12+fine*.12
    elif name=='paving':
        bx=(X*4)%1;by=(Y*4)%1;edge=np.minimum(np.minimum(bx,1-bx),np.minimum(by,1-by))
        raised=smooth((edge-.006)/.014);base=np.array([.40,.415,.42])+(coarse*.035+fine*.055)[...,None];base*=.6+.4*raised[...,None];height=raised*.004+fine*.001;rough=.8+fine*.1
    else:
        base=np.array([.065,.08,.095])+(fine*.012+coarse*.01)[...,None];height=fine*.00015;rough=.45+coarse*.06+fine*.035
    # Close periodic edges explicitly, including discrete brick row selection.
    for a in [height,rough,base]:a[-1]=a[0];a[:,-1]=a[:,0]
    du=(np.roll(height,-1,1)-np.roll(height,1,1))*N/4
    dv=(np.roll(height,-1,0)-np.roll(height,1,0))*N/4
    normal=np.dstack((-du,dv,np.ones_like(du)));normal/=np.linalg.norm(normal,axis=2)[...,None];normal=normal*.5+.5
    normal[-1]=normal[0];normal[:,-1]=normal[:,0]
    maps={}
    for kind,a in [('color',base),('normal',normal),('roughness',rough)]:
        pixels=np.round(np.clip(a,0,1)*255).astype('uint8');path=OUT/f'{name}-{kind}.png';Image.fromarray(pixels).save(path,optimize=True)
        assert np.array_equal(pixels[0],pixels[-1]) and np.array_equal(pixels[:,0],pixels[:,-1])
        maps[kind]={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest.append({'id':name,'size':[N,N],'coverage_metres':[2,2],'metalness':0,'normal_convention':'OpenGL +Y','maps':maps})
(OUT/'manifest.json').write_text(json.dumps({'source':'Original procedural surfaces: scripts/build-materials.py','materials':manifest},indent=2)+'\n')
print('6 PBR materials, 18 maps; exact opposing-edge equality verified; total bytes',sum(p.stat().st_size for p in OUT.glob('*.png')))
