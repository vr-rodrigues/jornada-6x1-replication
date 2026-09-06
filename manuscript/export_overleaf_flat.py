"""Export exactly three complete TeX files, one BibTeX file and eight PDFs."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import zipfile


def export(output: Path | None = None) -> Path:
    paper = Path(__file__).resolve().parent
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = (output or paper/'overleaf'/f'jornada_overleaf_pasta_unica_{stamp}.zip').resolve()
    if output.exists():
        raise FileExistsError(f'Preserving previous export: {output}')
    build = json.loads((paper/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    assets = json.loads((paper/'generated/ASSET_MANIFEST.json').read_text(encoding='utf-8'))
    used = {}

    def read(rel):
        path = (paper/rel).resolve()
        if not path.is_relative_to(paper):
            raise ValueError(f'Input outside manuscript: {rel}')
        rel = path.relative_to(paper).as_posix()
        data = path.read_bytes()
        expected = (assets['outputs_sha256'].get(rel.removeprefix('generated/'))
                    if rel.startswith('generated/') else build['source_sha256'].get(rel))
        actual = hashlib.sha256(data).hexdigest()
        if expected is None or actual != expected:
            raise ValueError(f'Input differs from verified manuscript: {rel}')
        used[rel] = actual
        return data

    def expand(rel, parents=()):
        if rel in parents:
            raise ValueError(f'Recursive input: {rel}')
        text = read(rel).decode('utf-8-sig').replace('\r\n', '\n')
        def insert(match):
            child = match.group(1)
            if not Path(child).suffix:
                child += '.tex'
            # Preserve TeX's token boundary in constructs such as
            # \noindent\input{abstract}, which must not become \noindentEste.
            return ' ' + expand(child, (*parents, rel))
        # Consume the enclosing line ending, avoiding an extra paragraph when
        # an input starts immediately after a command such as \noindent.
        return re.sub(r'\\input\{([^}]+)\}[ \t]*\n?', insert, text)

    payload = {}
    names = {'main.tex': 'main.tex', 'folha_rosto.tex': 'folha_rosto.tex',
             'online_appendix_pt.tex': 'appendix.tex'}
    for source, target in names.items():
        text = expand(source)
        text = re.sub(r'(\\includegraphics(?:\[[^\]]*\])?\{)generated/', r'\1', text)
        text = text.replace('\\graphicspath{{generated/}{./}}', '\\graphicspath{{./}}')
        text = text.replace('\\addbibresource{bibliography_clean.bib}\n\\addbibresource{bibliography_verified.bib}',
                            '\\addbibresource{references.bib}')
        if source == 'online_appendix_pt.tex':
            # Keep the two links to the current main table without requiring
            # another .tex/.aux file or a custom Overleaf compilation rule.
            aux = (paper/build['build_directory']/'main.aux').read_text(encoding='utf-8')
            labels = [line for line in aux.splitlines()
                      if line.startswith('\\newlabel{tab:mainresults}')]
            if len(labels) != 1 or not labels[0].endswith('{}}'):
                raise ValueError('Cannot export the verified main-table label')
            label = labels[0].replace('{tab:mainresults}', '{main-tab:mainresults}', 1)
            label = label[:-3] + '{main.pdf}}'
            portable = ('% Referencia ao artigo sincronizada nesta exportacao. Se renumerar\n'
                        '% a tabela de resultados no main, atualize esta linha tambem.\n'
                        '\\makeatletter\n' + label + '\n\\makeatother')
            text = text.replace('\\usepackage{xr-hyper}\n', '')
            declaration = '\\externaldocument[main-]{' + build['build_directory'] + '/main}[main.pdf]'
            if text.count(declaration) != 1:
                raise ValueError('Expected exactly one external reference declaration')
            text = text.replace(declaration, portable)
        if re.search(r'\\(?:input|include|externaldocument)\{', text):
            raise ValueError(f'Unexpanded local dependency: {target}')
        payload[target] = text.encode('utf-8')

    bibliography = '\n\n'.join(read(name).decode('utf-8-sig').strip()
        for name in ('bibliography_clean.bib', 'bibliography_verified.bib')) + '\n'
    keys = re.findall(r'(?mi)^@\w+\s*\{\s*([^,\s]+)\s*,', bibliography)
    if len(keys) != len(set(k.casefold() for k in keys)):
        raise ValueError('Duplicate bibliography keys')
    payload['references.bib'] = bibliography.encode('utf-8')
    for path in sorted((paper/'generated').glob('*.pdf')):
        payload[path.name] = read(path.relative_to(paper).as_posix())
    assert len(payload) == 12
    assert sum(name.endswith('.tex') for name in payload) == 3
    assert sum(name.endswith('.bib') for name in payload) == 1
    assert sum(name.endswith('.pdf') for name in payload) == 8
    assert not any('/' in name or '\\' in name for name in payload)
    for name, data in payload.items():
        if name.endswith('.tex'):
            for figure in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', data.decode('utf-8')):
                if figure not in payload:
                    raise ValueError(f'Missing figure: {figure}')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            archive.writestr(name, data)
    report = {'archive': str(output), 'bytes': output.stat().st_size,
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'compiler': 'XeLaTeX', 'bibliography_backend': 'Biber',
        'file_count': len(payload), 'files': sorted(payload),
        'source_sha256': used,
        'archive_files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()},
        'bibliography_entries': len(keys),
        'adaptations': ['All sections and tables inlined', 'Figure paths in project root',
            'Two bibliographies concatenated without duplicate keys',
            'Current external table label embedded in appendix; no auxiliary dependencies']}
    output.with_suffix('.manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('archive', 'bytes', 'file_count', 'files')}, ensure_ascii=False, indent=2))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    export(parser.parse_args().output)
