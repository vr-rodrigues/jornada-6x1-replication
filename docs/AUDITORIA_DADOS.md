# Auditoria e reconstrução das entradas empíricas

Execução em 5 de setembro de 2026. Os arquivos antigos de `data_raw/`,
`data_intermediate/` e `data_final/calibration_targets.csv` foram preservados.
Os novos arquivos estão exclusivamente em subdiretórios `reprocessed/`.

## Resultado e rota de coleta

A PNAD Contínua **2024T4 foi reprocessada de microdados reais**. O arquivo
oficial `PNADC_042024_20250815.zip`, 209.873.314 bytes, contém
`PNADC_042024.txt`; todas as 469.334 linhas foram verificadas como ano2024,
trimestre4. Não houve substituição por 2024T3, 2023T4 ou trimestre recente.

A Base dos Dados via BigQuery foi a primeira rota tentada. A CLI da conta
pessoal exigiu reautenticação. As Application Default Credentials disponíveis
permitiam consultar metadados, mas **não** criar jobs em `upa-research`
(403 `bigquery.jobs.create`). A leitura alternativa de linhas também foi
negada pela política de acesso por linha da tabela. Nenhum job de dados
foi executado/cobrado e o projeto corporativo disponível não foi usado para
consultas. SQLs, schemas e erro estão em
`data_intermediate/reprocessed/provenance/`; `manifest.json` declara
`official_ibge_mte_fallback`. A existência de schema obtido do BQ não é
evidência de que os resultados foram consultados no BQ.

Para prosseguir de maneira verificável, a opção explícita
`--allow-official-fallback` usou o IBGE para PNAD e o MTE para a tabela RAIS.
Os hashes SHA256, URLs, tamanhos e datas estão nos arquivos `*.source.json`.
Nenhum resultado antigo do pacote é usado como substituto de uma consulta.

```powershell
python src/data_raw/reprocess_verified_inputs.py --project upa-research --allow-official-fallback
python src/data_clean/clean_and_merge.py
```

`--from-cache` recompõe os momentos pelas células agregadas arquivadas
nesta execução, preservando a identificação da fonte oficial; não lê
resultados do modelo como entrada. `--official-only` reexecuta o
processamento do arquivo oficial já arquivado,
sem repetir uma autenticação sabidamente bloqueada. Para fazer a rota BQ,
é necessário reautenticar a conta pessoal e suas Application Default
Credentials para um projeto autorizado; o coletor não altera a configuração
global do gcloud. Toda consulta BQ tem dry-run, filtro de ano e trimestre,
teto de20GB por job e gravação de bytes estimados/processados/cobrados.
O teto não é estimativa de gasto: nesta execução o total cobrado foi zero.

## Dicionário, universo e pesos da PNAD

Fonte principal: [microdados oficiais 2024](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/2024/).
O layout e as categorias vêm de
[Dicionario_e_input_20221031.zip](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/Documentacao/Dicionario_e_input_20221031.zip),
com cópia local do XLS e do input SAS. O layout tem data anterior ao
microdado; a versão do microdado é20250815, não20221031.
O [questionário oficial, página11](https://www.ibge.gov.br/biblioteca/visualizacao/instrumentos_de_coleta/doc5676.pdf)
também confirma as perguntas17 e19.

* Universo: pessoas com14 anos ou mais (`V2009>=14`) ocupadas na semana
  de referência (`VD4002=1`), todo o Brasil. Cada pessoa é contada uma vez;
  atividade, formalidade, horas e rendimento referem-se ao trabalho principal.
* Peso: `V1028`, peso trimestral com correção de não entrevista e calibração
  pela projeção de população. Não se usam `V1027`, pesos unitários ou média
  simples dos estados/setores. Há385.717 pessoas14+ na amostra; população
  estimada total212.313.960,00; população14+173.429.638,00.
* `V4019`: CNPJ,1=sim,2=não; brancos são não aplicável/ausente, nunca
  automaticamente “não”. Essa pergunta é usada para empregadores e conta
  própria (`VD4009`8 e9). Fora desse universo, não se exige CNPJ.
* `V4017` pergunta se existe sócio trabalhando no negócio. Usá-la como CNPJ
  confunde outra característica com registro legal.
* Informais: `VD4009`2 (empregado privado sem carteira),4 (doméstico sem
  carteira),10 (familiar auxiliar),8/9 sem CNPJ. Formais:1,3,5,6,7 e8/9
  com CNPJ. Empregados públicos sem carteira são incluídos no complemento
  da definição estatística de informalidade aqui adotada; isso não é uma
  afirmação sobre regularidade de cada contrato.
* Categorias desconhecidas/CNPJ ausente em8/9 recebem classificação
  desconhecida; o JSON reporta denominador conhecido e limites inferior e
  superior sobre todos os ocupados. Nesta amostra não houve classificação
  desconhecida nem peso não positivo/ausente entre ocupados.

Resultado: **101.831.958,51 ocupados; informalidade38,6000872%**.
No mesmo microdado e com os mesmos pesos, substituir indevidamente CNPJ
por V4017 produziria44,1741162%. Essa comparação isola o erro de variável:
8.951.234,06 pessoas ponderadas mudam de classificação; a mudança líquida
de informalidade é menor porque há erros nos dois sentidos.

Os estimadores publicados são pontuais. Não foram calculados erros-padrão
com estratos/UPAs; portanto os arquivos não sustentam precisão amostral,
intervalos de confiança ou identificação de parâmetros estruturais.

## Horas, rendimentos e agregação

O dicionário define `V4039` como horas habituais no trabalho principal
(1 a120) e `V4039C` como horas efetivas na semana de referência (0 a120).
Horas efetivas zero são válidas. `VD4031`/`VD4035` distinguem todos os
trabalhos. A PNAD utilizada **não mede horas contratadas**.

| Medida, trabalho principal | Total | Formal | Informal |
|---|---:|---:|---:|
| Horas habituais |39,13169|41,42440|35,48475|
| Horas efetivas |37,85473|39,98102|34,47250|

Há nenhuma hora habitual/efetiva ausente entre os ocupados nesta amostra.
A distribuição formal completa, por cada valor observado de horas, está no
JSON. Os bins<=36,37–40,>40 são também publicados, mas representá-los por
36/40/44 é uma hipótese adicional. **17,9732755%** dos formais declaram
mais de44 horas habituais. Limitar esses registros a44 reduz a média formal
para39,94664. Aplicar um teto legal a horas habituais é uma aproximação de
política e exige sensibilidade própria; não transforma essas horas em
contratuais nem demonstra descumprimento legal.

Rendimentos são `VD4016`, rendimento mensal **habitual nominal do trabalho
principal**, para observações com renda positiva e horas habituais válidas.
Folha e horas usam exatamente a mesma amostra e pesos em cada grupo.
Converte-se mês para semana por12/52; um deflator comum no mesmo corte
temporal cancela na razão formal/informal. Não foram misturados rendimento
efetivo, rendimento de todos os trabalhos ou trimestres diferentes.

| Ponte descritiva formal/informal | Todos os ocupados pagos | Só empregados privados1/2 |
|---|---:|---:|
| (Folha formal/horas formais)/(folha informal/horas informais) |1,62244345|1,16432452|
| Médias de rendimento semanal por trabalhador |1,88009971|1,31828159|
| Médias individuais de rendimento por hora |1,58409450|1,17495026|

A primeira coluna inclui rendimentos mistos de empregadores e conta
própria, além de salários. A segunda restringe o universo a empregados
privados. Ambas são momentos descritivos, com composição observável
distinta, e não identificam automaticamente uma razão de produtos marginais
ou produtividade causal. A ponte estrutural precisa declarar qual usa.
O peso tecnológico CES não é observado diretamente nessa tabela.

Foram excluídos da ponte ampla28.603,38 formais e1.381.710,15 informais
ponderados por renda ausente/não positiva. São5.006 registros de renda
ausente na amostra ocupada, incluindo universos sem remuneração. Os JSONs
expõem as massas incluídas/excluídas e numeradores de renda/horas.

## Setores e porte: universos que não devem ser confundidos

A CNAE Domiciliar2.0 do trabalho principal (`V4013`, cinco dígitos) define
agricultura nas divisões01–03, indústria/construção05–43 e serviços45–99.
Os casos não classificáveis são preservados como `unclassified`.

| Setor | Ocupados ponderados | Informalidade |
|---|---:|---:|
| Agricultura |7.712.335,89|75,74960%|
| Indústria, incluindo construção |20.848.824,06|40,25815%|
| Serviços |73.251.518,73|34,21122%|
| Não classificado |19.279,83|60,02732%|

As participações nacionais incluem o residual. Um modelo de três setores
que o exclua deve reescalar seus pesos usando apenas os classificados e
registrar a exclusão de aproximadamente0,01893% dos ocupados.

PNAD `V4018` tem1–5,6–10,11–50,51+ pessoas no negócio/empresa;
`V40183` detalha11–50. O coletor registra grupos<=49,=50,>=51 e desconhecido
quando a resposta exata permite. O universo da pergunta não abrange de
forma comparável todos os trabalhadores públicos/domésticos. Esses grupos
não fornecem automaticamente informalidade por porte de estabelecimento
RAIS nem participações de empresas consolidadas.

## RAIS: resolução de59% versus13%+19%

A fonte primária é o [Sumário Executivo RAIS2022, tabela6, página9](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2022/sumario-executivo_rais_2022-1-1.pdf),
corroborada pela [planilha oficial](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2022/4-tabelas_rais-2022.xlsx),
aba`TABELA2`, célulasC87:D95. A planilha foi baixada e lida nesta execução;
os números não foram arbitrados entre os dois valores antigos.

Ativos em31/12/2022:52.790.864 **vínculos**, não pessoas distintas.
O porte é do **estabelecimento**, não da empresa consolidada.
A soma1–49 é4.747.386+4.494.655+5.166.304+6.385.257=
20.793.602, ou **39,3886374%**;50+ representa60,6113626%.
As subcategorias1–9 somam17,507%;10–49 somam21,882%, aproximadamente.
Assim, nem59% nem32% correspondem à tabela oficial e ao universo alegado.

O script antigo`collect_rais.py` gerava números constantes e lhes atribuía
fonte RAIS/SEBRAE, sem coletar a tabela. Foi preservado na cópia original;
foi substituído por um encaminhamento ao coletor canônico verificável. As taxas50%/20% por porte e
cunhas0,12/0,03 não são observações RAIS. O novo CSV as marca como
hipóteses estruturais congeladas. RAIS não observa a informalidade.

A [nota técnica MTE](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2022/nota-tecnica-rais-2022.pdf)
documenta a quebra de série em2022 com a migração do Grupo3 ao eSocial.
Não se devem comparar mecanicamente níveis de2021 e2022.
Também não se deve multiplicar participações RAIS de vínculos por taxas
PNAD de pessoas de universos diferentes. A calibração nacional empírica
de um único grupo evita inventar essa ponte entre portes.

## DIEESE: atribuição não verificada

A referência antiga cita apenas a homepage e um “Anuário do Sistema
Público de Emprego, Trabalho e Renda2024, tabela7”. Não fornece URL de
documento, página identificável ou arquivo bruto. A pesquisa do título,
ano, tabela e percentuais não localizou fonte primária que sustente
0,085/0,269/0,646. **Não se afirma que a fonte inexiste**; sua atribuição
permanece não verificável nesta execução.

Há publicações verificáveis diferentes, como a
[Nota Técnica286, de2025](https://www.dieese.org.br/notatecnica/2025/notaTec286Jornada.pdf)
e o [Boletim Emprego em Pauta32, de2026, sobre RAIS2024](https://www.dieese.org.br/boletimempregoempauta/2026/boletimEmpregoPauta32.pdf).
Ano de publicação, ano do dado e universo celetista/todos os vínculos não
são intercambiáveis. Nenhuma delas foi usada para certificar retroativamente
os pesos antigos. Pesos legados ficam como hipóteses e a distribuição PNAD
reprocessada é descrita como habitual, com as ressalvas acima.

## Arquivos e validação

`src/data_raw/reprocess_verified_inputs.py` é o coletor e agregador canônico;
`src/sectoral/data/pnad_sectoral_microdata.R` o invoca para evitar lógica
divergente e remove o fallback silencioso de trimestre. O merger
`src/data_clean/clean_and_merge.py` agora exige entradas verificadas,
grava somente`data_final/reprocessed/calibration_targets.csv` e distingue
observação de hipótese. Os pontos de entrada antigos `collect_rais.py` e
`collect_sectoral_data.py` encaminham ao mesmo coletor verificável.

Os testes`tests/test_verified_empirical.py` verificam categorias/CNPJ,
ausentes sem imputação, trimestre, soma dos setores, distribuição de horas,
reconstrução da ponte pelos numeradores/denominadores e RAIS pelos vínculos.
Igualdades de médias/bins são verificações de contabilidade de dados, **não
validação comportamental** do modelo.
