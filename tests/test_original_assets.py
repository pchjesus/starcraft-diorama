"""Offline tests for original sprite converter (standard-library only)."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import struct
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "prepare_original_assets.py"
spec = spec_from_file_location("converter", SCRIPT)
module = module_from_spec(spec)
spec.loader.exec_module(module)

def test_grp():
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/"extracted"
        src.mkdir()
        frame=bytes([4,0,6,0,0x44,1,1,2,0x81,0x42,2])
        (src/"marine.grp").write_bytes(struct.pack("<HHH",1,4,2)+struct.pack("<BBBBI",0,0,4,2,14)+frame)
        (src/"units.wpe").write_bytes(bytes(c for i in range(256) for c in (i,i,0,0)))
        out=Path(tmp)/"local_assets"
        assert module.build(src,out)==["marine"]
        assert (out/"marine.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert json.loads((out/"manifest.json").read_text())["sprites"]["marine"]["src"]=="marine.png"
        print("GRP -> PNG: PASS")

def test_png_folder():
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/"terran"/"marine"/"frames"
        src.mkdir(parents=True)
        (src/"marine_0000.png").write_bytes(b"synthetic-test-image")
        out=Path(tmp)/"local_assets"
        assert module.build(Path(tmp)/"terran",out)==["marine"]
        assert (out/"marine.png").read_bytes()==b"synthetic-test-image"
        print("PNG frame name -> pack: PASS")

if __name__=="__main__":
    test_grp()
    test_png_folder()
