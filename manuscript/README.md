# Manuscrito atual

Esta pasta contém o artigo em português, o apêndice online, a folha de rosto identificada e os fontes usados para gerá-los. A versão científica usa a referência formal de 44h e a execução fixada `../output/runs/20260905_005724_846373`.

Da raiz do repositório:

```sh
python reproduce.py --manuscript-only
```

Somente edição de texto, com figuras verificadas existentes:

```sh
python manuscript/build_paper.py --skip-assets
```

Para produzir um novo pacote plano do Overleaf:

```sh
python manuscript/export_overleaf_flat.py
```

Selecione XeLaTeX e Biber. O ZIP contém somente main.tex, appendix.tex, folha_rosto.tex, references.bib e oito figuras em PDF. O arquivo OVERLEAF_ATUAL.txt indica a exportação desta publicação. As seções são incorporadas pelo exportador.

O artigo é anônimo e tem 25 páginas. O apêndice é anônimo e separado. A folha de rosto identifica os autores e inclui a declaração de uso de IA revisada. Figuras, tabelas e parâmetros finais estão em generated/; scripts/ contém seus geradores. Os relatórios de revisão preservam o histórico das decisões editoriais e científicas. Registros históricos podem citar caminhos da máquina original; os comandos acima são portáveis.
