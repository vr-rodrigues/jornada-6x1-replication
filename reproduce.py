"""Portable entry point: python reproduce.py --tests --paper.

The numerical runner remains byte-identical to the audited run. This wrapper
supplies the bundled original archive and optionally builds the current paper.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent


def original_archive():
    target = ROOT / '.replication_cache/original_20260905'
    manifest = json.loads((ROOT / 'archive/MANIFEST_SHA256.json').read_text())
    with zipfile.ZipFile(ROOT / 'archive/original_20260905.zip') as archive:
        for name, expected in manifest.items():
            path = (target / name).resolve()
            if not path.is_relative_to(target.resolve()):
                raise ValueError('Archive member outside target directory')
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Original archive checksum mismatch: ' + name)
            if path.exists():
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    raise ValueError('Preserving modified archive member: ' + str(path))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tests', action='store_true')
    parser.add_argument('--paper', action='store_true')
    parser.add_argument('--refresh-data', action='store_true')
    parser.add_argument('--project', default='upa-research')
    parser.add_argument('--manuscript-only', action='store_true',
                        help='Rebuild the current paper from its pinned audited run.')
    args = parser.parse_args()
    if not args.manuscript_only:
        command = [sys.executable, str(ROOT / 'run_all.py'),
                   '--original-archive', str(original_archive())]
        if args.tests:
            command.append('--tests')
        if args.refresh_data:
            command += ['--refresh-data', '--project', args.project]
        if args.paper:
            command.append('--paper')
        subprocess.run(command, cwd=ROOT, check=True)
    if args.paper or args.manuscript_only:
        subprocess.run([sys.executable, 'manuscript/build_paper.py'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
