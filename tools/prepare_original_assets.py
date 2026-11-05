#!/usr/bin/env python3
"""Build a locally loaded sprite pack from personally extracted StarCraft files.

Supports original .GRP + WPE/PAL/PCX palette, or pre-extracted PNG/APNG.
Does not fetch or distribute Blizzard game data, and never contacts a server.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

ALIASES = {
    "marine": ["marine", "terran_marine"],
    "marine_react": ["marine_react", "marine_surprised"],
    "scv": ["scv", "terran_scv"],
    "siege_tank": ["siege_tank", "siegetank", "tank", "terran_tank", "tankbase"],
    "siege_tank_look": ["siege_tank_look", "tank_look", "tankturr", "tank_turret"],
    "factory": ["factory", "terran_factory"],
    "machine_shop": ["machine_shop", "machineshop", "machine"],
    "armory": ["armory", "terran_armory"],
    "supply_depot": ["supply_depot", "supplydepot", "supply", "depot"],
    "bunker_frame": ["bunker_frame", "bunker", "bunk"],
}
DIMS = {
    "factory": (260, 210), "machine_shop": (158, 144),
    "armory": (185, 165), "supply_depot": (160, 124),
    "bunker_frame": (150, 110), "siege_tank": (160, 100),
    "siege_tank_look": (160, 100), "marine": (68, 95),
    "marine_react": (72, 97), "scv": (110, 90),
}


def norm(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def find_key(path: Path):
    # Prefer exact filename, then the parent directory of extracted frame sequences.
    stem = norm(path.stem)
    stem = re.sub(r'_\d{3,5}$', '', stem)
    parents = [norm(p) for p in path.parts[-4:-1]]
    for key, aliases in ALIASES.items():
        if stem in aliases or stem == key:
            return key
    for parent in parents[::-1]:
        for key, aliases in ALIASES.items():
            if parent in aliases or parent == key:
                return key
    return None


def palette_rgba(path: Path):
    data = path.read_bytes()
    if path.suffix.lower() == '.pcx' and len(data) >= 769 and data[-769] == 12:
        rgb = data[-768:]
        return [(rgb[i], rgb[i + 1], rgb[i + 2], 255) for i in range(0, 768, 3)]
    if len(data) >= 1024:
        return [(data[i], data[i + 1], data[i + 2], 255) for i in range(0, 1024, 4)]
    if len(data) >= 768:
        return [(data[i], data[i + 1], data[i + 2], 255) for i in range(0, 768, 3)]
    raise ValueError('Palette must be 256 RGB/RGBX colors (.wpe, .pal, or .pcx).')


def decode_grp(path: Path, pal, frame_number: int = 0):
    """Decode a classic Brood War GRP compressed RLE frame to an RGBA canvas.

    Offsets in frame headers are absolute file offsets; scanline offsets are
    relative to the beginning of each frame's data.
    """
    data = path.read_bytes()
    if len(data) < 6:
        raise ValueError(f'Invalid GRP (short header): {path}')
    n, canvas_w, canvas_h = struct.unpack_from('<HHH', data)
    if not (1 <= n <= 4096 and 1 <= canvas_w <= 1024 and 1 <= canvas_h <= 1024):
        raise ValueError(f'Invalid GRP dimensions or frame count: {path}')
    if frame_number >= n:
        raise ValueError(f'Frame {frame_number} not present ({n} total)')
    hdr = 6 + 8 * frame_number
    if hdr + 8 > len(data):
        raise ValueError('Invalid GRP frame header')
    ox, oy, fw, fh, offset = struct.unpack_from('<BBBBI', data, hdr)
    if offset >= len(data) or ox + fw > canvas_w or oy + fh > canvas_h:
        raise ValueError('Invalid GRP frame data offset')
    pixels = bytearray(canvas_w * canvas_h * 4)
    # Teal player-color indices 8..15 (RGB preview), used only to display.
    team = [(28, 71, 66), (33, 86, 75), (41, 106, 91), (48, 122, 103),
            (54, 136, 113), (62, 151, 128), (81, 167, 144), (101, 184, 162)]
    for y in range(fh):
        if offset + y * 2 + 2 > len(data):
            raise ValueError('Incomplete GRP scanline table')
        row_offset = struct.unpack_from('<H', data, offset + y * 2)[0]
        pos = offset + row_offset
        x = 0
        while x < fw:
            if pos >= len(data):
                raise ValueError('Truncated GRP RLE data')
            op = data[pos]
            pos += 1
            if op & 0x80:
                skip = op & 0x7f
                if skip == 0:
                    raise ValueError('Invalid zero-length transparent run')
                x += skip
                continue
            if op & 0x40:
                count = op & 0x3f
                if count == 0 or pos >= len(data):
                    raise ValueError('Invalid repeat run')
                indices = bytes([data[pos]]) * count
                pos += 1
            else:
                count = op & 0x3f
                if count == 0 or pos + count > len(data):
                    raise ValueError('Invalid literal run')
                indices = data[pos:pos + count]
                pos += count
            for c in indices:
                if x >= fw:
                    raise ValueError('RLE run exceeds frame width')
                rgba = (*team[c-8], 255) if 8 <= c <= 15 else pal[c]
                dst = ((oy + y) * canvas_w + ox + x) * 4
                pixels[dst:dst + 4] = bytes(rgba)
                x += 1
        if x != fw:
            raise ValueError('Incomplete scanline')
    return canvas_w, canvas_h, bytes(pixels)


def save_png(path: Path, width: int, height: int, pixels: bytes):
    def chunk(typ: bytes, payload: bytes) -> bytes:
        return struct.pack('>I', len(payload)) + typ + payload + struct.pack('>I', zlib.crc32(typ + payload) & 0xffffffff)
    stride = width * 4
    rows = b''.join(b'\0' + pixels[y * stride:(y + 1) * stride] for y in range(height))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b'')
    path.write_bytes(png)


def grp_count(path: Path) -> int:
    data = path.read_bytes()[:6]
    if len(data) != 6:
        raise ValueError(f'Invalid GRP header: {path}')
    count, width, height = struct.unpack('<HHH', data)
    if not (1 <= count <= 4096 and 1 <= width <= 1024 and 1 <= height <= 1024):
        raise ValueError(f'Invalid GRP frame count or size: {path}')
    return count


def prepare(source: Path, out: Path, palette: Path | None, max_frames: int = 192):
    """Convert personally extracted files to an animation-aware local manifest.

    GRP direction frames are NOT automatically played in sequence because BW
    groups directions in sets of 17 and uses iscript to select actual poses.
    The manifest preserves available frames, but defaults to one static facing.
    """
    if not source.is_dir():
        raise ValueError('Source should be a folder of extracted StarCraft unit graphics.')
    if not 1 <= max_frames <= 1024:
        raise ValueError('--max-frames must be between 1 and 1024')
    groups = {}
    for p in sorted(source.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in ('.png', '.apng', '.grp'):
            continue
        key = find_key(p)
        if key:
            groups.setdefault(key, []).append(p)
    if not groups:
        raise ValueError('No recognized unit/building PNG/APNG/GRP found in folder.')
    needs_pal = any(any(p.suffix.lower() == '.grp' for p in files) for files in groups.values())
    if needs_pal and palette is None:
        palettes = [p for p in source.rglob('*') if p.suffix.lower() in ('.wpe', '.pal', '.pcx')]
        palette = palettes[0] if palettes else None
    colors = palette_rgba(palette) if needs_pal and palette is not None else None
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'format': 'original-starcraft-local-pack-v2', 'sprites': {}}
    for key, files in sorted(groups.items()):
        files_apng = sorted(p for p in files if p.suffix.lower() == '.apng')
        files_numbered = sorted((p for p in files if p.suffix.lower() == '.png'
                                 and re.search(r'_\d{3,5}$', norm(p.stem))),
                                key=lambda p: (int(re.search(r'_(\d{3,5})$',norm(p.stem)).group(1)), str(p)))
        files_png = sorted((p for p in files if p.suffix.lower() == '.png'
                            and not re.search(r'_\d{3,5}$', norm(p.stem))))
        files_grp = sorted(p for p in files if p.suffix.lower() == '.grp')
        dw, dh = DIMS.get(key, (120, 96))
        spec = {'width': dw, 'height': dh, 'anchorX': .5, 'anchorY': .84}
        if files_apng or files_png and not files_numbered:
            chosen = (files_apng or files_png)[0]
            name = f'{key}{chosen.suffix.lower()}'
            dest = out / name
            if dest.resolve() != chosen.resolve():
                shutil.copy2(chosen, dest)
            spec['src'] = name
        elif files_numbered or files_grp:
            frame_dir = out / 'frames' / key
            frame_dir.mkdir(parents=True, exist_ok=True)
            if files_numbered:
                selected = files_numbered[:max_frames]
                total = len(files_numbered)
                frames = []
                for i, file in enumerate(selected):
                    name = f'{key}_{i:04d}.png'
                    dest = frame_dir / name
                    if dest.resolve() != file.resolve():
                        shutil.copy2(file, dest)
                    frames.append(f'frames/{key}/{name}')
            else:
                if colors is None:
                    raise ValueError(f'GRP format requires a StarCraft palette (.wpe/.pal/.pcx): {files_grp[0]}')
                total = grp_count(files_grp[0])
                frames = []
                for i in range(min(total, max_frames)):
                    name = f'{key}_{i:04d}.png'
                    w, h, rgba = decode_grp(files_grp[0], colors, frame_number=i)
                    save_png(frame_dir / name, w, h, rgba)
                    frames.append(f'frames/{key}/{name}')
            spec['src'] = frames[0]
            spec['frames'] = frames
            spec['totalFrames'] = total
            spec['fps'] = 6
            # When a unit rotates, the first 17 GRP frames are directions,
            # not 17 frames of an idle animation. Select a stable facing.
            face = 8 if total >= 17 else 0
            face = min(face, len(frames) - 1)
            spec['startFrame'] = face
            spec['states'] = {'idle': [face], 'move': [face], 'work': [face],
                              'look': [face], 'react': [face]}
            spec['directionsPerPose'] = 17 if total >= 17 else None
            if total > len(frames):
                spec['truncated'] = True
        else:
            continue
        manifest['sprites'][key] = spec
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return list(manifest['sprites'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Folder containing your own extracted .grp/.png/.apng files')
    parser.add_argument('--out', type=Path, default=Path('local_assets'), help='Folder for the local-only graphic pack')
    parser.add_argument('--palette', type=Path, help='A palette file (.pal/.wpe/.pcx) from your game')
    parser.add_argument('--max-frames', type=int, default=192, help='Limit output frames per sprite (1-1024, default: 192)')
    args = parser.parse_args()
    try:
        names = prepare(args.source, args.out, args.palette, max_frames=args.max_frames)
    except (OSError, ValueError) as e:
        parser.exit(2, f'Asset conversion failed: {e}\n')
    print(f'Original sprites imported: {", ".join(names)}')
    print(f'Saved locally: {args.out.resolve()} (do not commit original graphics to public GitHub)')


if __name__ == '__main__':
    main()