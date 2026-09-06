# Replicação corrigida: jornada, produtividade e informalidade

O executor recalcula as versões original arquivada, código corrigido com entradas congeladas, ponte formal-informal recalibrada, RAIS verificada e PNAD2024T4 reprocessada. Resultados nacionais e setoriais cobrem40h/36h, eficiência bilateral e fadiga apenas acima do pico, com produto, A_req reotimizado/congelado, informalidade, GHH, CE e decomposição em níveis.

## Comando de reprodução

Instale as dependências uma vez:

```powershell
python -m pip install -r requirements-replication.lock.txt
```

Na pasta deste README:

```powershell
python run_all.py --refresh-data --tests --paper
```

Na pasta pai originalmente aberta no Codex:

```powershell
python replication_package/run_all.py --refresh-data --tests --paper
```

`--refresh-data` tenta a Base dos Dados/BigQuery no projeto `upa-research`, com dry-run e limite de bytes. Nesta execução, a autenticação/permissão de jobs foi bloqueada; o fallback explícito baixou/processou os microdados oficiais IBGE2024T4 e a planilha oficial MTE RAIS2022. O manifesto registra a rota, fontes, versão e hashes. Outro projeto autorizado pode ser informado com `--project ID`. O coletor não altera a configuração global do gcloud.

Sem `--refresh-data`, o pipeline usa somente os agregados reprocessados cuja proveniência foi arquivada. Para reler os brutos oficiais preservados sem repetir a autenticação bloqueada:

```powershell
python src/data_raw/reprocess_verified_inputs.py --official-only
python run_all.py --tests --paper
```

Para recompor os agregados a partir das células agregadas verificadas (não outputs do modelo), use `--from-cache` no coletor. A rota BigQuery exclusiva é `python src/data_raw/reprocess_verified_inputs.py --project ID`, sem permitir fallback; requer credenciais com permissão no projeto autorizado e acesso às tabelas.

## Saídas e rastreabilidade

Cada execução cria `output/runs/<timestamp>/` e recusa sobrescrever um diretório existente. `output/LATEST_RUN.json` aponta para a última execução concluída. Ali estão:

- `COMPARATIVO_RESULTADOS.csv`: versões e mudanças separadas, incluindo controle de agregação, horas observadas e hipótese de baseline limitado a44h.
- `RESULTADOS_SETORIAIS.csv`: três setores/agregado, omega congelado e ponte recalibrada por folhas setoriais.
- `CALIBRATED_PARAMETERS.csv`, `national_*/RESULTS_FULL.json` e `INPUTS.json`: parâmetros, raízes, níveis, alocações e FOCs.
- `sensitivity/`: CES com pontos interiores, eficiência/pico/horas, ponte de empregados privados, recursos/transferências e sensibilidades setoriais.
- `figures/`, `tables/`, `paper/APENDICE_NUMERICO_CORRIGIDO.pdf` (`--paper`).
- `RUN_MANIFEST.json`, `logs/` e `RELATORIO_CORRECOES.md`: hashes, comandos, versões, erros e testes.

As cópias principais dos CSVs e o relatório estão também na raiz do pacote. O apêndice novo é gerado com ReportLab; não exige LaTeX. Os manuscritos/PDFs originais permanecem preservados, pois suas narrativas e afirmações exigem revisão substantiva listada em `docs/NUMEROS_MANUSCRITO_A_REVISAR.md` e CSV. Não se copiam figuras novas para um manuscrito com números antigos.

## Original arquivado

A localização do snapshot original está em `../AUDITORIA_ATUAL.txt`. Pode ser fornecida por `--original-archive CAMINHO` ao transportar o projeto. A pasta contém `snapshot/`, manifesto SHA256, diff das alterações locais, logs e `baseline_run/` executado com output inicialmente vazio. O baseline original falha na figura setorial porque seu executor exige um CSV de output que não gera. Os20 testes antigos passam; PDFs antigos não foram contados como recém-compilados. O comparativo original é recalculado em um processo separado usando o código arquivado.

Os dados brutos/intermediários/finais originais nunca são sobrescritos. Dados novos ficam em `data_raw/reprocessed/`, `data_intermediate/reprocessed/` e `data_final/reprocessed/`. A planilha de momentos reprocessados descreve observações; as entradas efetivas do modelo, inclusive N e K normalizados, estão no diretório da execução.

## Interpretação

- A contabilidade59/41% formal, com informalidades50/20%, implica40,915805%; não é estimativa brasileira.
- A PNAD real2024T4 implica38,6000872%; o CNPJ é V4019.
- RAIS2022:39,3886374% dos vínculos ativos em estabelecimentos1-49; vínculos não são pessoas e estabelecimentos não são empresas consolidadas.
- Horas da PNAD são habituais/efetivas, não contratadas. O baseline empírico preserva a distribuição habitual bruta; impor um teto sobre ela é uma hipótese explícita. Topcode44 é variante separada.
- Sigma permanece1,326 nas versões principais. Omega é tecnológico, calibrado condicionalmente à ponte de remuneração; não é participação formal. A ponte ampla inclui renda de conta própria/empregadores e não é salário puro.
- GHH e CE usam denominadores distintos. A_req reotimiza composição a cada tentativa e também reporta composição congelada. A_req assinado pode ser negativo quando o modelo projeta ganho de produto; nesse caso o ganho positivo necessário é zero.
- C+ajuste=Y no caso principal: tau/pi são transferências. Custos como recursos têm cenário separado. Não há incidência distributiva nem ajuste endógeno de capital identificados.
- A grade de sensibilidade não é conjunto identificado, e identidades de horas não são validação comportamental.

Leia `RELATORIO_CORRECOES.md` e os documentos `AUDITORIA_DADOS`, `AUDITORIA_NUCLEO`, `AUDITORIA_SETORIAL` para definições, fontes e limites.

## Testes e geradores individuais

```powershell
python -m unittest discover -s tests -v
python src/calibration/calibrate_all.py --output-dir output/minha_calibracao
python src/calibration/calibrate_flatbelow.py --output-dir output/minha_calibracao_flat
python src/calibration/solve_sigma_for_R.py --output output/minha_ponte.json
```

Os geradores antigos de figuras/tabelas que continham versões duplicadas do modelo agora exigem `--run-dir output/runs/ID` e escrevem novos assets. O núcleo científico único está em `src/model/`; o modelo setorial chama esse núcleo.
