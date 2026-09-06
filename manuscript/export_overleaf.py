"""Export the current manuscript sources and typesetting assets to Overleaf.

Does not run the economic model or modify the manuscript. Only the external
reference path in the distributed appendix is adapted to the portable build.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


LATEXMKRC = r'''# Portable external references: appendix -> main manuscript.
# Pattern documented by Overleaf; additionally track included source files.
# https://www.overleaf.com/learn/how-to/Cross_referencing_with_the_xr_package_in_Overleaf
$pdf_mode = 1;
add_cus_dep('tex', 'aux', 0, 'jornada_external_refs');

sub jornada_external_refs {
    my $stem = $_[0];
    return 0 if $stem eq $root_filename;
    die "Unexpected external document: $stem\n" unless $stem =~ m{^(\./)?main$};
    my $status = system('latexmk', '-norc', '-pdf', '-interaction=nonstopmode',
                        '-halt-on-error', '-outdir=xref-build', '-jobname=main',
                        'main.tex');
    return $status if $status;
    copy('xref-build/main.aux', 'main.aux') or die "Cannot copy main references: $!";
    rdb_add_generated('xref-build/main.aux');
    # Editing a section, table, figure or bibliography also updates the labels.
    rdb_ensure_files_here(glob('sections/*.tex'), glob('generated/*.tex'),
                         glob('generated/*.pdf'), glob('*.bib'), 'chicago.bst');
    return 0;
}
'''

README = '''# Pacote para Overleaf

Este ZIP contém a versão atual do artigo, apêndice e folha de rosto, incluindo
a Figura 4 com painel A (44→40h) acima do painel B (44→36h).

## Importar

1. No Overleaf, escolha **New Project → Upload Project** e selecione este ZIP.
2. Em **Settings → Compiler**, use **pdfLaTeX** e **TeX Live 2025**.
3. Selecione **main.tex** como **Main document** e recompile.

O arquivo principal já fica na raiz do ZIP. As figuras são PDFs prontos para
inclusão; a compilação não requer Python, acesso aos microdados ou execução do
modelo. [Documentação de importação do Overleaf](https://docs.overleaf.com/managing-projects-and-files/uploading-a-project).

## Artigo, apêndice e folha de rosto

- `main.tex`: texto principal, 26 páginas na compilação local verificada.
- `online_appendix_pt.tex`: apêndice, 23 páginas; selecione-o como Main document
  para gerar seu PDF.
- `folha_rosto.tex`: folha de rosto com autoria, 2 páginas; selecione-o como
  Main document para compilá-lo.

O arquivo `latexmkrc` gera automaticamente as referências ao artigo quando o
apêndice é compilado, inclusive se ele for compilado primeiro. Ele acompanha
alterações nos arquivos de seções, tabelas, figuras e bibliografias. A única
adaptação no texto-fonte exportado é trocar `.build_paper/main` por `main` na
declaração `externaldocument` do apêndice. O conteúdo do manuscrito é preservado.
[Referências entre documentos no Overleaf](https://www.overleaf.com/learn/how-to/Cross_referencing_with_the_xr_package_in_Overleaf).

Para usar os links do apêndice ao artigo fora do Overleaf, baixe os dois PDFs,
nomeie o artigo `main.pdf` e mantenha ambos na mesma pasta.

## Editar

- `sections/`: redação do artigo e do apêndice.
- `generated/*.tex`: tabelas utilizadas nos documentos.
- `generated/*.pdf`: oito figuras, incluindo a Figura 4 em dois painéis.
- `bibliography_clean.bib` e `bibliography_verified.bib`: referências.
- `chicago.bst`: estilo bibliográfico usado nesta versão.
- `MANIFESTO_OVERLEAF.json`: hashes dos arquivos e identificação da exportação.

O pacote contém as figuras atuais e as fontes de composição do artigo.
Os códigos que recalculam as figuras a partir do modelo permanecem no projeto
de replicação e na pasta PAPER original.

Compilação local alternativa, com TeX Live e latexmk:

```sh
latexmk -pdf main.tex
latexmk -pdf online_appendix_pt.tex
latexmk -pdf folha_rosto.tex
```

Arquivos auxiliares antigos, PDFs finais já compilados e figuras de versões
anteriores não são enviados; cada documento será compilado com os fontes e
as figuras deste pacote.
'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export(output: Path | None = None) -> Path:
    paper = Path(__file__).resolve().parent
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = output or paper / 'overleaf' / f'jornada_trabalho_overleaf_{stamp}.zip'
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f'Preserving existing archive: {output}')
    source_paths = [paper / name for name in ('main.tex', 'online_appendix_pt.tex',
        'folha_rosto.tex', 'bibliography_clean.bib', 'bibliography_verified.bib')]
    source_paths += sorted((paper / 'sections').glob('*.tex'))
    source_paths += sorted((paper / 'generated').glob('*.tex'))
    source_paths += sorted((paper / 'generated').glob('*.pdf'))
    assets = json.loads((paper / 'generated/ASSET_MANIFEST.json').read_text(encoding='utf-8'))
    build = json.loads((paper / 'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    entries, originals = {}, {}
    for path in source_paths:
        rel = path.relative_to(paper).as_posix()
        data = path.read_bytes()
        expected = (assets['outputs_sha256'].get(path.relative_to(paper / 'generated').as_posix())
                    if path.is_relative_to(paper / 'generated') else build['source_sha256'].get(rel))
        if expected is None or digest(data) != expected:
            raise ValueError(f'Source differs from the verified build: {rel}')
        originals[rel] = digest(data)
        if rel == 'online_appendix_pt.tex':
            old = b'\\externaldocument[main-]{.build_paper/main}[main.pdf]'
            new = b'\\externaldocument[main-]{main}[main.pdf]'
            if data.count(old) != 1:
                raise ValueError('Expected one external manuscript reference')
            data = data.replace(old, new)
        entries[rel] = data
    kpsewhich = shutil.which('kpsewhich')
    if not kpsewhich:
        fallback = Path(os.environ.get('APPDATA', '')) / 'TinyTeX/bin/windows/kpsewhich.exe'
        if fallback.is_file():
            kpsewhich = str(fallback)
    if not kpsewhich:
        raise RuntimeError('kpsewhich is needed to include the verified Chicago style')
    style = Path(subprocess.check_output([kpsewhich, 'chicago.bst'], text=True).strip())
    entries['chicago.bst'] = style.read_bytes()
    entries['latexmkrc'] = LATEXMKRC.encode('utf-8')
    entries['README_OVERLEAF.md'] = README.encode('utf-8')
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(),
        'compiler': 'pdfLaTeX', 'tex_live': '2025', 'main_document': 'main.tex',
        'replication_run': assets['replication_run'],
        'source_build_manifest_sha256': digest((paper / 'BUILD_MANIFEST.json').read_bytes()),
        'source_files_sha256': originals,
        'adaptations': {'online_appendix_pt.tex': 'externaldocument path .build_paper/main -> main'},
        'files_sha256': {k: digest(v) for k, v in sorted(entries.items())}}
    entries['MANIFESTO_OVERLEAF.json'] = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel, data in sorted(entries.items()):
            archive.writestr(rel, data)
    print(json.dumps({'zip': str(output), 'files': len(entries), 'bytes': output.stat().st_size,
                      'sha256': digest(output.read_bytes())}, ensure_ascii=False, indent=2))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    export(parser.parse_args().output)
