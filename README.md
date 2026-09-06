# Jornada de trabalho, produtividade e informalidade

Pacote de replicação do artigo **“Jornada de trabalho, produtividade e informalidade: uma avaliação quantitativa para o Brasil”**, de Victor Rangel e Fernando Barros Jr. Atualização de setembro de 2026.

## Manuscrito atual

- [Artigo em português](manuscript/main.pdf), 25 páginas, anônimo.
- [Apêndice online](manuscript/online_appendix_pt.pdf), 26 páginas, anônimo.
- [Folha de rosto](manuscript/folha_rosto.pdf), identificada e separada.
- [Fontes, figuras e tabelas atuais](manuscript/).
- O pacote plano do Overleaf é indicado em `manuscript/OVERLEAF_ATUAL.txt`: três `.tex`, uma bibliografia `.bib` e oito figuras PDF, todos na raiz. Compile com **XeLaTeX e Biber**.

O artigo usa explicitamente a referência formal limitada a 44h (`reprocessed_topcoded44`) e mantém a distribuição habitual integral como sensibilidade. Trata-se de uma hipótese de mensuração/comparação, não de horas contratadas observadas. Com sigma 1,326, a compensação de PTF é 1,53–1,57% para 40h e 6,52–8,38% para 36h. A Figura 4 apresenta o pacote de transição em dois painéis: 44→40h acima e 44→36h abaixo.

As pastas `paper/` e as figuras/tabelas soltas antigas em `output/` são históricas. Não são a versão atual do artigo.

## Reprodução

Requer Python 3.12 e as dependências registradas:

```sh
python -m pip install -r requirements-replication.lock.txt
python reproduce.py --tests --paper
```

O comando extrai e verifica a cópia arquivada do original, recalcula as comparações e sensibilidades nacionais/setoriais com os agregados empíricos verificados, executa os testes, gera o apêndice numérico e reconstrói as figuras e os três PDFs do manuscrito. O compilador do manuscrito requer XeLaTeX, Biber, Times New Roman e os pacotes LaTeX dos preâmbulos. Os arquivos de auditoria registram as versões utilizadas. A compilação recusa referências não resolvidas, estouro de layout e artigo acima de 30 páginas.

Para executar somente os resultados e testes, sem LaTeX:

```sh
python reproduce.py --tests
```

Para reconstruir somente o manuscrito a partir da execução auditada fixada:

```sh
python reproduce.py --manuscript-only
```

Cada execução econômica cria `output/runs/<timestamp>/`. O manuscrito fica ligado à execução auditada `20260905_005724_846373`, com hashes verificados, para que uma nova execução não substitua silenciosamente a base editorial. Seus geradores recalculam as curvas, os exercícios adicionais de base 44h e os painéis da Figura 4. O comparativo e os resultados setoriais na raiz são atualizados pela execução econômica; a seleção e os resultados finais do artigo estão em `manuscript/generated/`.

## Dados e proveniência

- PNAD Contínua 2024T4: microdados oficiais `PNADC_042024_20250815.zip`, versão de 15/08/2025. CNPJ: V4019. Horas habituais e efetivas são diferenciadas; horas contratadas não são observadas.
- RAIS 2022: planilha oficial MTE, vínculos ativos em 31/12 por tamanho de estabelecimento.
- PTF brasileira: Penn World Table 11.0, série FRED RTFPNABRA632NRUG, arquivada em `data_raw/fred/`.
- Agregados, células ponderadas, dicionário, consultas e manifestos: `data_intermediate/reprocessed/`; entradas finais: `data_final/reprocessed/`.

O ZIP bruto da PNAD tem cerca de 210 MB e permanece fora do Git. Seu URL oficial, tamanho e SHA256 estão em `data_intermediate/reprocessed/provenance/PNADC_042024_20250815.zip.source.json`. O coletor permite baixar e reprocessar essa versão sem substituir o trimestre:

```sh
python src/data_raw/reprocess_verified_inputs.py --official-only
python reproduce.py --tests --paper
```

A rota Base dos Dados/BigQuery é explícita. Para outro projeto de cobrança autorizado:

```sh
python reproduce.py --refresh-data --project SEU_PROJETO --tests --paper
```

Na auditoria original, a permissão de jobs BigQuery estava indisponível; utilizou-se o fallback oficial IBGE/MTE, documentado. A opção `--from-cache` do coletor recompõe os agregados a partir das células verificadas, sem reutilizar resultados do modelo como dados.

## Correções e comparação

- [Relatório de correções](RELATORIO_CORRECOES.md).
- [Comparativo original/código corrigido/dados reprocessados](COMPARATIVO_RESULTADOS.csv).
- [Resultados setoriais](RESULTADOS_SETORIAIS.csv).
- [Auditoria dos dados](docs/AUDITORIA_DADOS.md), [núcleo](docs/AUDITORIA_NUCLEO.md) e [setores](docs/AUDITORIA_SETORIAL.md).
- [Revisão do artigo](manuscript/REVISAO_PAPER.md) e [fidelidade à narrativa original](manuscript/FIDELIDADE_NARRATIVA.md).
- [Notas desta publicação](docs/ATUALIZACAO_GITHUB_20260905.md).

O teste contábil 59/41% formal com informalidades 50/20% implica 40,9158%; não é estimativa empírica. A escolha formal–informal é contínua. A_req reotimiza composição e também informa compensação com composição congelada. GHH e equivalente de consumo são medidas distintas. A decomposição usa níveis intermediários e denominador comum. Pesos tecnológicos, participações formais e remuneração horária não são igualados automaticamente.

## Original preservado

`archive/original_20260905.zip` e `archive/MANIFEST_SHA256.json` preservam códigos, parâmetros, dados disponíveis, resultados anteriores e logs do baseline executado antes das correções, incluindo as alterações locais existentes naquela data. O wrapper verifica os bytes e extrai em `.replication_cache/`, sem sobrescrever arquivos modificados. A falha do executor original na figura setorial está documentada; não é apresentada como execução completa bem-sucedida. O histórico Git anterior também permanece acessível.

Os arquivos de auditoria antigos podem registrar caminhos absolutos da máquina original. São registros históricos; os comandos atuais usam caminhos relativos ao repositório.
