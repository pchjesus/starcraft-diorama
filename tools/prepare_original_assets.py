#!/usr/bin/env python3
"""Convert personally extracted StarCraft 1/Brood War sprites into a local pack.

Input: directory containing original .png/.apng or .grp files, plus an original
.wpe/.pal/.pcx palette for GRP conversion. Never uploads or downloads assets.
"""
from pathlib import Path
import argparse, json, re, shutil, struct, zlib

ALIASES={
  'marine':['marine','terran_marine'],
  'scv':['scv','terran_scv'],
  'siege_tank':['siege_tank','siegetank','tank','tankbase'],
  'siege_tank_look':['siege_tank_look','tank_look','tankturr','tank_turret'],
  'factory':['factory','terran_factory'],
  'machine_shop':['machine_shop','machineshop','machine'],
  'armory':['armory','terran_armory'],
  'supply_depot':['supply_depot','supplydepot','supply','depot'],
  'bunker_frame':['bunker_frame','bunker','bunk'],
}
DIMS={
 'factory':(260,210),'machine_shop':(158,144),'armory':(185,165),
 'supply_depot':(160,124),'bunker_frame':(150,110),
 'siege_tank':(160,100),'siege_tank_look':(160,100),
 'marine':(68,95),'scv':(110,90),
}
def norm(s):
    return re.sub('[^a-z0-9]+','_',s.lower()).strip('_')
def key_for(p):
    names=[norm(p.stem)]+[norm(part) for part in p.parts[-4:-1][::-1]]
    for name in names:
        name=re.sub(r'_\d{3,5}$','',name)
        for key,aliases in ALIASES.items():
            if name in aliases or name==key: return key
    return None
def load_palette(path):
    data=path.read_bytes()
    if path.suffix.lower()=='.pcx' and len(data)>=769 and data[-769]==12:
        data=data[-768:];step=3
    elif len(data)>=1024:step=4
    elif len(data)>=768:step=3
    else:raise ValueError('Palette must contain 256 RGB/RGBX colors.')
    return [tuple(data[i:i+3]) for i in range(0,256*step,step)]
def decode_grp(path,pal):
    data=path.read_bytes()
    if len(data)<14:raise ValueError('GRP file too short.')
    count,w,h=struct.unpack_from('<HHH',data)
    if not(1<=count<=4096 and 1<=w<=1024 and 1<=h<=1024):
        raise ValueError('Invalid GRP dimensions/frame count.')
    ox,oy,fw,fh,off=struct.unpack_from('<BBBBI',data,6)
    if ox+fw>w or oy+fh>h or off>=len(data):
        raise ValueError('Invalid GRP frame offset.')
    pixels=bytearray(w*h*4)
    team=[(28,71,66),(33,86,75),(41,106,91),(48,122,103),
          (54,136,113),(62,151,128),(81,167,144),(101,184,162)]
    for row in range(fh):
        if off+row*2+2>len(data):raise ValueError('Truncated scanline header.')
        at=off+struct.unpack_from('<H',data,off+row*2)[0];x=0
        while x<fw:
            if at>=len(data):raise ValueError('Truncated RLE data.')
            op=data[at];at+=1
            if op&128:
                skip=op&127
                if not skip:raise ValueError('Zero-length transparent run.')
                x+=skip;continue
            if op&64:
                n=op&63
                if not n or at>=len(data):raise ValueError('Invalid repeat run.')
                values=[data[at]]*n;at+=1
            else:
                n=op&63
                if not n or at+n>len(data):raise ValueError('Invalid literal run.')
                values=data[at:at+n];at+=n
            for v in values:
                if x>=fw:raise ValueError('RLE overrun.')
                rgb=team[v-8] if 8<=v<=15 else pal[v]
                idx=((oy+row)*w+ox+x)*4
                pixels[idx:idx+4]=bytes((*rgb,255));x+=1
        if x!=fw:raise ValueError('Incomplete GRP scanline.')
    return w,h,bytes(pixels)
def save_png(path,w,h,pixels):
    def chunk(tag,payload):
        return struct.pack('>I',len(payload))+tag+payload+struct.pack('>I',zlib.crc32(tag+payload)&0xffffffff)
    lines=b''.join(b'\0'+pixels[y*w*4:(y+1)*w*4] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))
                     +chunk(b'IDAT',zlib.compress(lines,9))+chunk(b'IEND',b''))
def build(src,out,palette=None):
    if not src.is_dir():raise ValueError('Please specify an extracted sprite folder.')
    chosen={}
    for p in sorted(src.rglob('*')):
        if p.suffix.lower() not in ['.png','.apng','.grp']:continue
        k=key_for(p)
        if not k:continue
        n=norm(p.stem)
        sequence=bool(re.search(r'_\d{3,5}$',n))
        priority=(0 if p.suffix.lower()=='.apng' else 1 if p.suffix.lower()=='.png' and not sequence else 2 if sequence else 3)
        idx=int(n.split('_')[-1]) if sequence else 0
        if k not in chosen or (priority,idx)<chosen[k][:2]:
            chosen[k]=(priority,idx,p)
    if not chosen:raise ValueError('No recognized StarCraft graphics found.')
    if any(p.suffix.lower()=='.grp' for _,_,p in chosen.values()):
        if not palette:
            palette=next((p for p in src.rglob('*') if p.suffix.lower() in ['.wpe','.pal','.pcx']),None)
        if not palette:raise ValueError('GRP requires a palette (.wpe/.pal/.pcx) from your game.')
        colors=load_palette(palette)
    out.mkdir(parents=True,exist_ok=True)
    manifest={'format':'original-starcraft-local-pack-v1','sprites':{}}
    for k,(_,_,p) in chosen.items():
        dst=out/(k+('.png' if p.suffix.lower()=='.grp' else p.suffix.lower()))
        if p.suffix.lower()=='.grp':
            w,h,pixels=decode_grp(p,colors);save_png(dst,w,h,pixels)
        elif p.resolve()!=dst.resolve():shutil.copy2(p,dst)
        w,h=DIMS[k]
        manifest['sprites'][k]={'src':dst.name,'width':w,'height':h,'anchorX':.5,'anchorY':.84}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return list(manifest['sprites'])
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path)
    ap.add_argument('--out',type=Path,default=Path('local_assets'))
    ap.add_argument('--palette',type=Path)
    a=ap.parse_args()
    try:items=build(a.source,a.out,a.palette)
    except (OSError,ValueError) as e:ap.exit(2,'Conversion failed: '+str(e)+'\n')
    print('Local original sprites imported:',', '.join(items))
    print('Private output:',a.out.resolve())
