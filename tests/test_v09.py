"""v0.9 sprite conversion tests using entirely synthetic, non-copyright images."""
import json
import struct
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve()
sys.path.insert(0,str(HERE.parents[1]/'tools'))
from prepare_original_assets import prepare


def simple_grp(path, count):
    # 2x1 visible pixels, one compressed repeated-color run per frame.
    header = struct.pack('<HHH',count,2,1)
    frames=[];offset=6+8*count
    for i in range(count):
        frame=struct.pack('<H',2)+bytes([0x42,(i+1)%256]);frames.append((struct.pack('<BBBBI',0,0,2,1,offset),frame));offset+=len(frame)
    path.write_bytes(header+b''.join(h for h,_ in frames)+b''.join(body for _,body in frames))


def test_multi_grp():
    with tempfile.TemporaryDirectory() as d:
        src=Path(d)/'source';src.mkdir();out=Path(d)/'local_assets'
        simple_grp(src/'marine.grp',17)
        (src/'units.wpe').write_bytes(bytes(v for i in range(256) for v in (i, i, i, 0)))
        keys=prepare(src,out,None)
        assert keys==['marine'],keys
        m=json.loads((out/'manifest.json').read_text())['sprites']['marine']
        assert m['totalFrames']==17 and len(m['frames'])==17 and m['startFrame']==8,m
        assert m['states']['idle']==[8]
        assert all((out/f).read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for f in m['frames'])
        print('GRP 17-direction extraction PASS')


def test_truncation():
    with tempfile.TemporaryDirectory() as d:
        src=Path(d)/'src';src.mkdir();out=Path(d)/'local_assets'
        simple_grp(src/'tank.grp',21)
        (src/'units.wpe').write_bytes(bytes(1024))
        prepare(src,out,None,max_frames=12)
        m=json.loads((out/'manifest.json').read_text())['sprites']['siege_tank']
        assert m['truncated'] and m['totalFrames']==21 and len(m['frames'])==12
        assert m['startFrame']==8
        print('frame output cap PASS')


def test_numbered_files_and_compat():
    with tempfile.TemporaryDirectory() as d:
        source=Path(d)/'source'/'marine'/'frames';source.mkdir(parents=True)
        for i in range(5):(source/f'marine_{i:04d}.png').write_bytes(b'valid-enough-for-copy')
        (source.parent.parent/'scv.png').write_bytes(b'fake-binary-content')
        out=Path(d)/'out';keys=prepare(source.parent.parent,out,None)
        m=json.loads((out/'manifest.json').read_text())['sprites']
        assert sorted(keys)==['marine','scv']
        assert len(m['marine']['frames'])==5
        assert (out/m['marine']['frames'][3]).read_bytes()==b'valid-enough-for-copy'
        assert (out/m['scv']['src']).read_bytes()==b'fake-binary-content'
        print('numbered PNG + legacy static PNG PASS')


if __name__=='__main__':
    test_multi_grp();test_truncation();test_numbered_files_and_compat()