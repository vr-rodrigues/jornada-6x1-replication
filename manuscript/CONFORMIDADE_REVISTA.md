# Adequação às diretrizes da revista

Data: 5 de setembro de 2026. Esta conferência se aplica ao pacote `overleaf/jornada_overleaf_pasta_unica_20260905_202821.zip` e aos PDFs atuais de `PAPER`. As diretrizes utilizadas são as transcritas pelo autor na conversa.

Os ajustes de formatação e composição bibliográfica foram implementados. O artigo tem **25 páginas, incluindo referências**; o apêndice tem 26 páginas e deve ser enviado como documento adicional. A folha de rosto tem 2 páginas. Mesmo somando folha de rosto e artigo, são 27 páginas. A narrativa, a literatura citada e os resultados econômicos foram preservados.

## Conferência final

| Diretriz | Implementação e evidência |
|---|---|
| Times New Roman 12 | XeLaTeX e `fontspec`, com a família Times New Roman efetivamente incorporada. Texto corrente, títulos, tabelas, notas, rodapés e legendas em 12 pt LaTeX. A medida de aproximadamente 11,955 pontos no PDF corresponde à conversão entre o ponto TeX e o ponto PDF; não é redução da fonte. |
| Espaçamento de 1,5 | `onehalfspacing` comum aos três documentos. Corrigida também a redução automática para espaço simples que `setspace` aplica a tabelas, figuras e notas de rodapé. Distância usual entre linhas de aproximadamente 17,93 pontos PDF, equivalente a 18 pontos TeX. |
| Margens mínimas de 2,5 cm | Margens superior e laterais de 2,5 cm; inferior de 3 cm para acomodar profundidade de fórmulas e descendentes. Conferência das posições do texto não encontrou invasões do limite de 2,5 cm. Números de página permanecem no rodapé. |
| Numeração | Todas as 25 páginas do artigo, 26 do apêndice e 2 da folha de rosto numeradas. |
| Destaques em itálico | Títulos, hierarquia de seções, sumário, rótulos de legendas, descrições e campos da folha de rosto padronizados. Nenhum trecho textual em negrito nos PDFs finais. |
| Idioma | Português, com título e resumo em inglês preservados. Conjunção das citações localizada para “e”. |
| Limite de 30 páginas | Artigo: 25, incluindo referências. Apêndice separado. Nenhum argumento ou referência foi cortado para reduzir páginas. |
| Chicago autor–data | `biblatex-chicago`, com Biber e localização brasileira. Citações sem vírgula entre sobrenome e ano, títulos de artigos entre aspas, periódicos em itálico, ano sem parênteses na lista e pontuação bibliográfica padronizada. |
| Lista alfabética ao final e somente citados | Artigo: 34 obras citadas e 34 impressas; apêndice: 13 e 13. A união contém 40 obras. Os 21 registros legados não citados permanecem no arquivo bibliográfico, sem aparecer nas listas impressas. |
| URLs com acesso | As 31 referências do artigo e 12 do apêndice que contêm endereço eletrônico/DOI têm data de acesso e a imprimem. URLs e datas saíram de notas livres para campos estruturados, evitando duplicação. |
| Pacote Overleaf | Exatamente três `.tex`, um `.bib` e oito figuras PDF, todos na raiz. Nenhuma dependência de seções, fontes locais, arquivos auxiliares ou diretórios externos. |

Os gráficos mantêm os desenhos, séries, painéis e escalas aprovados. Seus textos passaram a Times New Roman, preservando a escala gráfica. Os símbolos das equações usam fonte matemática própria, com os tamanhos convencionais de índices e expoentes. Isso é distinto dos tamanhos do texto, notas e legendas.

## Arquivos alterados e motivos

- `journal_style.tex` (novo): centraliza Times New Roman, espaçamento, itálicos, legendas, notas, numeração e tratamento dos ambientes flutuantes. O exportador incorpora seu conteúdo nos três `.tex`; ele não vira um quarto arquivo no ZIP.
- `main.tex`, `online_appendix_pt.tex` e `folha_rosto.tex`: preâmbulos compatíveis com XeLaTeX; margens e estilo comuns. Artigo e apêndice usam Chicago autor–data/Biber. A folha de rosto mantém autoria, resumos e declarações.
- `sections/facts.tex`, `calibration.tex`, `validation.tex`, `app_data.tex`, `app_model.tex` e `app_results.tex`: retiradas reduções tipográficas para 10/11 pt. A tabela de parâmetros usa página de flutuante própria para evitar fragmentos isolados de texto. Os demais arquivos de seção tiveram apenas normalização de fim de linha na escrita, quando aplicável.
- `bibliography_clean.bib` e `bibliography_verified.bib`: organização dos endereços e datas de acesso, classificação das notícias como páginas online e correção de acentos e datas por extenso. Permanecem as mesmas obras, autores, anos, resultados e versões citadas.
- `scripts/generate_assets.py`: textos dos gráficos em Times New Roman; tabelas e notas geradas em 12 pt; cabeçalhos da tabela nacional em duas linhas para acomodar o tamanho exigido. Reexecução confirmou que os 19 CSVs numéricos permanecem idênticos byte a byte.
- `build_paper.py`: XeLaTeX e Biber; diretório de compilação isolado em `.build_paper/journal/`; verificações de fonte incorporada, limite de páginas, correspondência entre citações e referências, datas de acesso, glifos ausentes e transbordamento. Os PDFs só são publicados depois de os três documentos passarem.
- `export_overleaf_flat.py`: incorpora o estilo compartilhado, reúne os dois arquivos bibliográficos em `references.bib` e sincroniza a referência à tabela do artigo usando os novos auxiliares de compilação.
- `README.md`, `OVERLEAF_ATUAL.txt`, `BUILD_MANIFEST.json`, `REVISAO_VISUAL.json` e `CONFORMIDADE_REVISTA.json`: instruções e evidências atualizadas.

Os arquivos produzidos em `generated/` foram regenerados pelo código. Nenhum código do modelo nem dado bruto foi modificado nesta adequação editorial.

## Datas de acesso e endereços verificados

As consultas já documentadas em 28 de abril de 2026 foram preservadas. As consultas completadas nesta revisão têm data de 5 de setembro de 2026. Para DOI, o registro distingue consulta ao resolvedor de leitura integral do artigo; não afirma acesso ao texto completo de trabalhos restritos. O arquivo `.build_paper/journal/reference_access_checks.json` guarda os resultados dessas verificações.

Os DOI de Fernandes (1991) e Hirata e Machado (2010) retornaram HTTP 404 no resolvedor durante a conferência. As páginas oficiais de [Estudos Econômicos](https://revistas.usp.br/ee/pt_BR/article/view/158304) e [Economia Aplicada](https://revistas.usp.br/ecoa/pt_BR/article/view/1058) confirmam os mesmos identificadores e os metadados bibliográficos. Por isso, a lista impressa usa os endereços dos periódicos; os DOI permanecem preservados nos metadados, com supressão somente de sua impressão nessas duas entradas.

A fonte bibliográfica adotada é [biblatex-chicago](https://ctan.org/pkg/biblatex-chicago), com localização brasileira e ajustes à pontuação e aos destaques pedidos pela revista. O padrão de referência consultado é o [guia Chicago autor–data](https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-2.html).

## Reprodução e verificação

A partir da pasta que contém `PAPER`:

```powershell
python PAPER/build_paper.py
```

Esse comando regenera os ativos a partir da execução econômica fixada e compila os três documentos. A geração numérica foi executada nesta revisão; as iterações posteriores, exclusivamente tipográficas, usaram `python PAPER/build_paper.py --skip-assets`, com conferência dos hashes dos ativos.

Para exportar novamente:

```powershell
python PAPER/export_overleaf_flat.py
```

No Overleaf, selecione **XeLaTeX** e `main.tex` como documento principal. Biber é executado automaticamente. Para compilar o material complementar, selecione `appendix.tex`; para a folha de rosto, `folha_rosto.tex`. A [documentação do Overleaf](https://www.overleaf.com/learn/latex/XeLaTeX) confirma a disponibilidade de Times New Roman com esse compilador. Não são necessários arquivos de fonte adicionais no ZIP.

A exportação final foi extraída em diretório novo e compilada independentemente. Os três documentos passaram sem citações/referências indefinidas, glifos ausentes ou caixas transbordando. As **53 páginas** dessa compilação têm texto e renderização Poppler idênticos aos PDFs locais revisados. O arquivo `.verification.json` ao lado do ZIP documenta essa comparação. A renderização e a revisão visual estão registradas em `REVISAO_VISUAL.json` e `.build_paper/journal/qa_delivery/`.

## Preservação da versão anterior

Antes de editar, foi criada a cópia `../PAPER_antes_normas_revista_20260905_195624`, indicada por `../PAPER_NORMAS_REVISTA_BACKUP.txt`. Seus **170 arquivos** foram novamente conferidos contra o manifesto SHA256 e permanecem inalterados. As cópias e exportações anteriores também foram mantidas.

A comparação confirmou preservação de conteúdo nos **13 arquivos de seções**, descontando apenas comandos de tamanho e posicionamento, e igualdade binária dos **19 CSVs de resultados**. As evidências estão em `.build_paper/journal/preservation_checks.json`. A Figura 4 continua com 44→40h em cima e 44→36h embaixo, usando “redução do custo de formalização”; agora aparece na página 20 do artigo.

Esta etapa adapta a apresentação às diretrizes. As hipóteses e limitações econômicas e empíricas já explicitadas no texto e no apêndice permanecem válidas e visíveis.
