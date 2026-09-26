import logging
import os
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path


def expand_cabinet(cabinet: Path, destination: Path) -> None:
    """Extract Microsoft CAB data using the existing Windows utility."""
    destination.mkdir(parents=True, exist_ok=True)
    utility = Path(os.environ["SystemRoot"]) / "System32" / "expand.exe"
    subprocess.run([str(utility), "-F:*", str(cabinet), str(destination)], check=True, capture_output=True)


def embedded_cabinets(binary: bytes, destination: Path) -> list[Path]:
    """Locate bounded CAB headers without executing the redistributable."""
    cabinets = []
    position = 0
    while True:
        position = binary.find(b"MSCF", position)
        if position < 0:
            break
        if position + 36 <= len(binary):
            length = struct.unpack_from("<I", binary, position + 8)[0]
            if 36 <= length <= len(binary) - position and binary[position + 24:position + 26] == b"\x03\x01":
                cabinet = destination / f"embedded-{len(cabinets)}.cab"
                cabinet.write_bytes(binary[position:position + length])
                cabinets.append(cabinet)
        position += 4
    if len(cabinets) != 2:
        raise RuntimeError("Unexpected Microsoft bootstrapper CAB layout; re-audit the pinned asset")
    return cabinets


def extract_runtime(source: Path, workspace: Path, destination: Path) -> None:
    """Copy only the Microsoft runtime DLLs and license from signed media."""
    workspace.mkdir(parents=True, exist_ok=True)
    cabinets = embedded_cabinets(source.read_bytes(), workspace)
    ux = workspace / "ux"
    attached = workspace / "attached"
    expand_cabinet(cabinets[0], ux)
    expand_cabinet(cabinets[1], attached)
    manifest = element_tree.parse(ux / "0").getroot()
    payloads = [node for node in manifest.iter() if node.tag.rsplit("}", 1)[-1] == "Payload"]
    runtime_paths = {"packages/vcruntimeminimum_amd64/cab1.cab", "packages/vcruntimeadditional_amd64/cab1.cab"}
    cab_payloads = [node for node in payloads if node.attrib.get("FilePath", "").replace("\\", "/").lower() in runtime_paths]
    if len(cab_payloads) != 2:
        raise RuntimeError("Expected the minimum and additional x64 runtime cabinets")
    extracted = workspace / "runtime"
    for node in cab_payloads:
        source_name = node.attrib["SourcePath"]
        if Path(source_name).name != source_name or "/" in source_name or "\\" in source_name:
            raise RuntimeError("Unexpected CAB source name")
        expand_cabinet(attached / source_name, extracted)
    names = (
        "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
        "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll",
        "vcruntime140.dll", "vcruntime140_1.dll", "vcruntime140_threads.dll", "vcomp140.dll",
    )
    destination.mkdir(parents=True, exist_ok=True)
    for name in names:
        matches = [path for path in extracted.iterdir() if path.name.lower() == name + "_amd64"]
        if len(matches) != 1:
            raise RuntimeError(f"Runtime DLL missing or ambiguous: {name}")
        shutil.copy2(matches[0], destination / name)
    licenses = [node for node in payloads if node.attrib.get("FilePath", "").lower() == "license.rtf"]
    if len(licenses) != 1:
        raise RuntimeError("Microsoft runtime license was not found")
    license_name = licenses[0].attrib["SourcePath"]
    if Path(license_name).name != license_name:
        raise RuntimeError("Unexpected license payload path")
    shutil.copy2(ux / license_name, destination / "Microsoft-runtime-license.rtf")
    logging.info("Extracted %s app-local Microsoft DLLs; no MSI/EXE installer executed", len(names))


def main() -> int:
    """Extract the pinned Microsoft runtime and report failures."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        extract_runtime(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    except Exception:
        logging.exception("Runtime extraction failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
