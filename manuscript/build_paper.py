#!/usr/bin/env python
"""Generate verified assets and compile the article, appendix and title page.

From this directory or any other: python PAPER/build_paper.py
Requires Python numerical dependencies and a LaTeX installation with XeLaTeX
and Biber (biblatex-chicago), and Times New Roman installed. The replication run is pinned in scripts/generate_assets.py.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

PAPER = Path(__file__).resolve().parent
BUILD = PAPER / '.build_paper/journal'
LOGS = BUILD / 'commands'
DOCUMENTS = ('main', 'online_appendix_pt', 'folha_rosto')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def executable(name):
    path = shutil.which(name)
    if path:
        return path
    candidate = Path(os.environ.get('APPDATA', '')) / 'TinyTeX/bin/windows' / (name + '.exe')
    if candidate.is_file():
        return str(candidate)
    raise RuntimeError(f'{name} unavailable; install TeX Live / TinyTeX and put it on PATH.')


def execute(command, label):
    print(label, flush=True)
    result = subprocess.run(command, cwd=PAPER, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    (LOGS / (label + '.log')).write_text(result.stdout, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{label} failed (exit {result.returncode}); see {LOGS / (label + ".log")}\n{result.stdout[-4500:]}')
    return result.stdout


def numerical_python(requested=None):
    """Find an existing scientific runtime, recording every dependency probe.

    The desktop's bundled Python may omit SciPy. No environment is installed
    or modified: prefer this interpreter, then existing user installations.
    An explicit --assets-python is strict and never silently substituted.
    """
    candidates = [requested] if requested else [sys.executable]
    if not requested:
        if os.name == 'nt':
            local = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Python'
            candidates += [str(p) for p in sorted(local.glob('Python*/python.exe'), reverse=True)]
        candidates += [shutil.which('python3'), shutil.which('python')]
    probes = []
    for candidate in dict.fromkeys(c for c in candidates if c):
        probe = subprocess.run([candidate, '-c',
            'import numpy,pandas,matplotlib,scipy; print(numpy.__version__,pandas.__version__,matplotlib.__version__,scipy.__version__)'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace')
        probes.append({'python': candidate, 'exit_code': probe.returncode, 'output': probe.stdout.strip()})
        if probe.returncode == 0:
            (LOGS / 'python_dependencies.json').write_text(json.dumps(probes, indent=2), encoding='utf-8')
            print(f'Figure runtime: {candidate}', flush=True)
            return candidate
    (LOGS / 'python_dependencies.json').write_text(json.dumps(probes, indent=2), encoding='utf-8')
    raise RuntimeError('No Python with numpy, pandas, matplotlib and scipy found; use --assets-python PATH.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-assets', action='store_true', help='Editorial compilation using current generated assets.')
    parser.add_argument('--assets-python', help='Python interpreter with numpy, pandas, matplotlib and scipy.')
    args = parser.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    commands = []
    if not args.skip_assets:
        asset_command = [numerical_python(args.assets_python), 'scripts/generate_assets.py']
        commands.append(asset_command)
        execute(asset_command, 'generate_assets')
    assets = json.loads((PAPER / 'generated/ASSET_MANIFEST.json').read_text(encoding='utf-8'))
    for name, expected in assets['outputs_sha256'].items():
        if digest(PAPER / 'generated' / name) != expected:
            raise RuntimeError(f'Generated asset changed outside generator: {name}')
    xelatex, biber = executable('xelatex'), executable('biber')
    checks = {}
    for document in DOCUMENTS:
        command = [xelatex, '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
                   '-output-directory=.build_paper/journal', document + '.tex']
        commands.append(command)
        execute(command, document + '_pass1')
        if document != 'folha_rosto':
            bibcmd = [biber, '--input-directory=.build_paper/journal', '--output-directory=.build_paper/journal', document]
            commands.append(bibcmd)
            execute(bibcmd, document + '_biber')
        execute(command, document + '_pass2')
        final = execute(command, document + '_pass3')
        for extra_pass in range(4, 7):
            if 'Rerun to get' not in final and 'Rerun to get outlines right' not in final:
                break
            final = execute(command, document + f'_pass{extra_pass}')
        if 'Rerun to get' in final:
            raise RuntimeError(f'{document}: references did not stabilize after six passes')
        bad = re.findall(r'(?:Citation|Reference) .+ undefined|There were undefined (?:references|citations)|multiply defined', final)
        if bad:
            raise RuntimeError(f'{document}: unresolved LaTeX references: {bad}')
        from pypdf import PdfReader
        reader = PdfReader(BUILD / (document + '.pdf'))
        extracted = '\n'.join(page.extract_text() or '' for page in reader.pages)
        if '\ufffd' in extracted or '??' in extracted:
            raise RuntimeError(f'{document}: invalid character or unresolved placeholder in PDF')
        warnings = re.findall(r'Overfull \\[hv]box[^\n]*', final)
        if warnings or 'Missing character:' in final or 'Float too large' in final:
            raise RuntimeError(f'{document}: layout overflow or missing glyph; see final compilation log')
        if document == 'main' and len(reader.pages) > 30:
            raise RuntimeError('The article exceeds the journal limit of 30 pages')
        body_fonts = sorted({str(font.get_object().get('/BaseFont', ''))
            for page in reader.pages
            for font in page['/Resources'].get('/Font', {}).get_object().values()})
        if not any('TimesNewRomanPSMT' in name for name in body_fonts):
            raise RuntimeError(f'{document}: Times New Roman not embedded')
        bibliography_check = None
        if document != 'folha_rosto':
            cited = {node.text for node in ET.parse(BUILD / (document + '.bcf')).iter()
                     if node.tag.endswith('}citekey')}
            bbl = (BUILD / (document + '.bbl')).read_text(encoding='utf-8')
            printed = re.findall(r'\\entry\{([^}]+)\}', bbl)
            if set(printed) != cited or len(printed) != len(cited):
                raise RuntimeError(f'{document}: cited/printed bibliography mismatch')
            missing_dates = []
            for block in re.split(r'(?=\\entry\{)', bbl)[1:]:
                if ('\\verb{urlraw}' in block or '\\verb{doi}' in block) and '\\field{urlyear}' not in block:
                    missing_dates.append(re.match(r'\\entry\{([^}]+)\}', block)[1])
            if missing_dates:
                raise RuntimeError(f'{document}: missing access dates: {missing_dates}')
            bibliography_check = {'cited_and_printed': len(cited), 'missing_access_dates': missing_dates}
        checks[document] = {'pages': len(reader.pages), 'unresolved_references': bad,
                            'overfull_boxes': warnings, 'text_characters': len(extracted),
                            'embedded_fonts': body_fonts, 'bibliography': bibliography_check}
        (BUILD / (document + '_extracted.txt')).write_text(extracted, encoding='utf-8')
    # Publish local PDFs only after all three compile and pass consistency checks.
    for document in DOCUMENTS:
        shutil.copy2(BUILD / (document + '.pdf'), PAPER / (document + '.pdf'))
    sources = list(PAPER.glob('*.tex')) + list(PAPER.glob('*.bib')) + list((PAPER / 'sections').glob('*.tex'))
    sources += list(PAPER.glob('*.py')) + list((PAPER / 'scripts').glob('*.py'))
    manifest = {'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                'python': sys.version, 'platform': platform.platform(), 'commands': commands,
                'xelatex_version': subprocess.check_output([xelatex, '--version'], text=True).splitlines()[0],
                'biber_version': subprocess.check_output([biber, '--version'], text=True).splitlines()[0],
                'build_directory': BUILD.relative_to(PAPER).as_posix(),
                'replication_run': assets['replication_run'], 'checks': checks,
                'assets_manifest_sha256': digest(PAPER / 'generated/ASSET_MANIFEST.json'),
                'source_sha256': {p.relative_to(PAPER).as_posix(): digest(p) for p in sources},
                'pdf_sha256': {d + '.pdf': digest(PAPER / (d + '.pdf')) for d in DOCUMENTS}}
    (PAPER / 'BUILD_MANIFEST.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(checks, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
