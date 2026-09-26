import marshal
import hashlib
import struct
import sys
import zlib
from pathlib import Path


def build(root: Path) -> None:
    """Retain the official bootloader and libraries; replace only the entry script."""
    original = root / "live_subtitle.exe"
    binary = original.read_bytes()
    if hashlib.sha256(binary).hexdigest() != "b4c67623f6f12d28b55042f7afb0319ecc9d9c9cef7b0f207e62926053cafd60":
        raise RuntimeError("Re-audit the new upstream release before adapting the portable integration")
    cookie_position = binary.rfind(b"MEI\x0c\x0b\x0a\x0b\x0e")
    magic, package_size, toc_offset, toc_size, python_version, library = struct.unpack("!8sIIII64s", binary[cookie_position:cookie_position + 88])
    if python_version != 311:
        raise RuntimeError("This integration requires the verified official v2.1 Python 3.11 bundle")
    base = cookie_position + 88 - package_size
    position = base + toc_offset
    entries = []
    while position < base + toc_offset + toc_size:
        length, offset, compressed_size, raw_size, compressed, kind = struct.unpack("!IIIIBc", binary[position:position + 18])
        name_bytes = binary[position + 18:position + length]
        name = name_bytes.rstrip(b"\0").decode()
        payload = binary[base + offset:base + offset + compressed_size]
        if name == "live_subv2.1":
            original_code = zlib.decompress(payload) if compressed else payload
            source = (
                "import marshal,os,sys,types\n"
                "UPSTREAM=types.ModuleType('live_subtitle_upstream')\n"
                "sys.modules[UPSTREAM.__name__]=UPSTREAM\n"
                f"exec(marshal.loads({original_code!r}),UPSTREAM.__dict__)\n"
                "hook=os.path.join(os.path.dirname(sys.executable),'app','portable.py')\n"
                "with open(hook,'r',encoding='utf-8-sig') as handle:\n"
                "    exec(compile(handle.read(),hook,'exec'),globals())\n"
            )
            modified = marshal.dumps(compile(source, "portable_entry.py", "exec"))
            raw_size = len(modified)
            compressed = 1
            payload = zlib.compress(modified, 9)
        entries.append((name_bytes, kind, compressed, raw_size, payload))
        position += length
    data = bytearray()
    toc = bytearray()
    for name_bytes, kind, compressed, raw_size, payload in entries:
        toc += struct.pack("!IIIIBc", 18 + len(name_bytes), len(data), len(payload), raw_size, compressed, kind) + name_bytes
        data += payload
    cookie = struct.pack("!8sIIII64s", magic, len(data) + len(toc) + 88, len(data), len(toc), python_version, library)
    (root / "LiveSubtitle.exe").write_bytes(binary[:base] + data + toc + cookie)
    (root / "app" / "upstream" / "live_subv2.1.marshal").write_bytes(original_code)


if __name__ == "__main__":
    build(Path(sys.argv[1]).resolve())
