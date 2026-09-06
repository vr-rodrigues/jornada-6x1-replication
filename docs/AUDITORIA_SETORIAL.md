# Auditoria da extensão setorial

Esta nota acompanha a reconstrução executada em setembro de 2026. O código e as
entradas anteriores estão no snapshot indicado por `../AUDITORIA_ATUAL.txt`.
Resultados anteriores em `output/sectoral` não são evidência de execução atual.

## Problemas encontrados na implementação original

1. `run_all.py` gerava a figura setorial lendo resultados já existentes, sem
   executar `sector_model.py` nem `run_empirical.py`. Portanto, a execução do
   orquestrador não reprocessava a PNAD nem regenerava os contrafactuais setoriais.
2. `sector_model.py` fixava sigma em 1,15, enquanto `run_empirical.py` usava 1,326;
   ambos fixavam omega em 0,622. O peso tecnológico não era estimado setorialmente
   e não pode ser justificado pela identidade omega = participação formal.
3. A busca de `A_req` já reotimizava o emprego formal para cada multiplicador de
   produtividade. A correção conserva essa propriedade. O código tinha também
   uma primeira chamada redundante usando a distribuição de horas do primeiro
   setor para todos os setores, logo descartada em favor de um solver próprio.
4. As escolhas formal–informal eram feitas em grades; as cunhas eram calibradas
   por bisseções sobre objetivos em degraus. A extensão agora usa o núcleo comum.
5. O denominador do emprego agregado era fixado em 0,59. As participações do CSV
   denominado empírico somavam 1,0001 por arredondamento. A nova implementação
   registra essa soma e normaliza explicitamente apenas diferenças compatíveis
   com arredondamento; o emprego agregado é sempre a soma do emprego dos setores.
6. `dCV_pct` era a variação percentual de `C-v(h)`, não equivalente de consumo.
   As novas saídas separam `dGHH_pct` de `CE_pct`; o nome legado `dCV_pct` é
   mantido somente como alias documentado de GHH para compatibilidade.
7. `decomposition.py` calculava diferenças entre contrafactuais de heterogeneidade,
   sem parcelas aditivas de produto. As parcelas atuais são obtidas de níveis
   intermediários e divididas todas pelo produto inicial: horas físicas,
   eficiência, realocação formal–informal, nessa ordem.
8. `workers_affected.py` usava totais de ocupados escritos diretamente no código
   (7.712, 20.849 e 73.252 milhares), rotulados como saída PNAD. A reconstrução
   só publica contagens absolutas quando o arquivo reprocessado contém os totais
   ponderados e sua proveniência; os demais exercícios informam proporções
   mecânicas. Exposição ao teto não é incidência distributiva nem validação
   comportamental.

## Entradas e hipóteses que não devem ser confundidas

O CSV `SECTORAL_BASELINE_FACTS.csv` contém pesos de horas descritos como estimados
a partir de DIEESE e composição RAIS. Sua atribuição não demonstra observação
direta de horas contratadas. O CSV antigo `SECTORAL_PNAD_EMPIRICAL.csv` também não
passa a ser dado verificado por ser lido novamente: o script que o produzia usava
V4017 como CNPJ, classificava respostas ausentes como ausência de CNPJ e aceitava
silenciosamente outro trimestre. Sua classificação precisa ser refeita com V4019.

Os cenários congelados preservam esses valores para isolar mudanças de código e
os rotulam como entradas legadas de proveniência não verificada. Os cenários
reprocessados exigem um artefato novo de PNAD 2024T4 e seus metadados. Não há
fallback para CSV antigo nem para trimestre diferente.

PNAD fornece pessoas e setor de atividade do trabalho principal, não estoque de
capital por empresa. A extensão mantém como hipótese os pesos de capital
0,0766 / 0,2585 / 0,6649 (agropecuária / indústria, incluindo construção /
serviços), originalmente atribuídos ao VAB regional de 2021. Mesmo que esses pesos
de VAB sejam confirmados, sua igualdade aos pesos de capital continua sendo
hipótese. A=1 em cada setor; o produto setorial resultante não é VAB observado.
As razões de produto por hora em reais do CSV antigo não calibram a produção.

A extensão usa um grupo por setor e participações no emprego total. Ela não
transporta a divisão RAIS por tamanho de estabelecimento para a PNAD nem identifica
heterogeneidade simultânea por porte e setor. Os resultados setoriais não são uma
decomposição exata do modelo nacional de dois portes.

## Escopo das equações e conclusões a retirar

A produção total é a soma de três tecnologias com capital predeterminado e
emprego total fixo por setor. Não há insumo-produto, mobilidade entre setores,
mercado de bens com preços relativos, acumulação de capital ou escolha de
investimento. Logo, o modelo não entrega ajuste endógeno de capital, prazo de
três a cinco anos ou redução de um a dois pontos percentuais de `A_req` por esse
canal. Esses números aparecem em `sec_model.tex`, `sec_results.tex` e
`sec_conclusion.tex` e precisam ser retirados ou apoiados por um modelo adicional.

Também não há rendas individuais, regras de distribuição de lucros e transferências,
negociação salarial nem transições identificadas de trabalhadores. O bem-estar
representativo, o produto por setor e as proporções expostas ao teto não sustentam
perdas de 28,57% para trabalhadores que se tornam informais ou ganhos de 1,41%
para os que permanecem formais. Essas incidências em `sec_welfare_conditional.tex`
e `tab_welfare_incidence_by_type_autogen.tex` dependem de hipóteses adicionais e
não são resultados das equações implementadas.

Devem ser regenerados os números setoriais do corpo e apêndice: intervalos de
`A_req` de 1,3–1,8% (40h) e 6,91–8,05% (36h); aumentos de informalidade de
2,88 / 2,73 / 2,10 pp; participação de serviços no produto de 71,0%; contribuição
de 4,8 pp em perda agregada de 7,2%; efeito inferior a 0,2 pp da isenção da
agropecuária; ranking entre setores; tabelas, figuras e conclusões correspondentes.
Nenhum desses valores deve ser mantido por ajuste compensatório dos parâmetros.

## Reconstrução efetivamente disponível e execução atual

O reprocessamento usou o arquivo oficial IBGE `PNADC_042024_20250815.zip`,
recuperado em 05/09/2026, e os pesos V1028. A tentativa de usar BigQuery ficou
bloqueada por autenticação/acesso; a substituição de canal foi registrada como
`verified_official_fallback`. Não houve substituição de trimestre. O JSON em
`data_intermediate/reprocessed/pnad_targets.json` contém as fontes, as versões,
as somas ponderadas e os controles de ausentes.

Os novos momentos de informalidade são 75,749599% na agropecuária,
40,258146% na indústria e construção e 34,211220% nos serviços. Os 19.279,833
ocupados sem atividade classificada representam 0,01893299% do total nacional.
O modelo de três setores os exclui explicitamente: sua cobertura é
99,98106701% e suas participações de emprego são condicionadas à atividade
classificada. Não se atribui essa exclusão a arredondamento, nem se afirma que
a agregação de três setores recompõe exatamente o universo nacional.

O exercício principal com dados reprocessados preserva a distribuição completa
das horas habituais observadas no baseline. A operação `min(h,H0)` usa
`H0=max(suporte observado)` apenas para ser a identidade; esse número **não é
um teto legal**. Nos cenários, aplica-se `min(h,40)` ou `min(h,36)`. Interpretar
esse corte nas horas habituais como efeito de uma mudança legal é uma hipótese,
pois horas habituais, efetivas e contratadas são conceitos diferentes. O
topcode de 44h é uma especificação alternativa identificada nos parâmetros,
não uma transformação silenciosa dos dados principais.

A curvatura permanece ancorada externamente em 42,244h e E_Q=0,6. As funções
de eficiência são extrapoladas para as horas curtas e longas existentes na PNAD;
esses efeitos não foram estimados na amostra brasileira. As sensibilidades
variam E_Q, pico, distribuição e CES para mostrar a importância dessas escolhas.
N=0,59 é a normalização congelada de escala do exercício e não uma nova estimativa
da taxa de ocupação. Cada JSON registra as entradas efetivas usadas.

Há dois exercícios empíricos distintos: omega=0,622 mantido como hipótese e
omega recalibrado, para cada função de eficiência, à razão nacional de
remuneração horária 1,6224434531. A ponte soma as folhas produtivas e as horas
físicas de todas as firmas antes de calcular as razões. As cunhas são
recalibradas em cada avaliação. A igualdade entre remuneração e produto
marginal bruto é uma hipótese adicional, e essa calibração não identifica
simultaneamente tecnologia, cunhas e incidência salarial.

`sector_model.py`, `run_empirical.py`, `decomposition.py`, `sensitivity.py` e
`red_team_tests.py` usam o mesmo núcleo nacional. Nenhum deles mantém solver
setorial por grade nem bisseção própria de restauração do produto.
`inputs.py` valida a versão e a proveniência; `workers_affected.py` calcula
apenas exposição mecânica e exige totais ponderados para publicar contagens.
`sector_assets.py` gera PNG, PDF e SVG exclusivamente de linhas recém-executadas.

O teste `tests/test_sectoral_corrected.py` contém 12 verificações: contabilidade
e calibração por setor; distribuição própria de horas; KKT e fronteiras;
reotimização dentro de A_req; produto restaurado nas duas composições;
decomposição aditiva; CE; restrição de recursos; arredondamentos; ausência
de dados sem fallback; exposição sem contagens inventadas; suporte real de horas.
As sensibilidades contêm 37 casos e 592 linhas por versão de entradas, incluindo
uma grade CES 3×3×3 com vértices, faces e pontos interiores. A ponte salarial não
restringe essa grade: ela é uma sensibilidade, não um conjunto identificado.

Comandos independentes (o orquestrador corrigido integra essas etapas):

```powershell
py -3.12 src/sectoral/model/sector_model.py --input-kind frozen --output-dir output/corrected/sectoral_frozen
py -3.12 src/sectoral/model/run_empirical.py --output-dir output/corrected/sectoral_reprocessed
py -3.12 src/sectoral/model/sensitivity.py --input-kind reprocessed --data-dir data_intermediate/reprocessed --output-dir output/corrected/sectoral_reprocessed
py -3.12 -m unittest discover -s tests -p test_sectoral_corrected.py -v
```

As saídas contêm `SECTOR_RESULTS.csv`, `SECTOR_RESULTS_FULL.json`,
`SECTOR_PARAMETERS.json`, `SECTOR_DECOMPOSITION.csv`,
`SECTOR_HOURS_EXPOSURE.csv` e, na sensibilidade,
`SECTOR_SENSITIVITY.csv` e `SECTOR_SENSITIVITY_METADATA.json`.
Os resultados fixos e com a ponte recalibrada têm diretórios distintos.

Na execução integrada `20260905_004745_446495`, que preserva horas habituais
observadas e recalibra a ponte horária, omega=0,676034374 na função bilateral
e 0,677092195 na função de fadiga apenas acima do pico. Para 40h, A_req setorial
é respectivamente -1,1240%, 0,8456% e -0,0877% (bilateral), e -1,1127%,
0,8394% e -0,0851% (fadiga), na ordem agropecuária, indústria, serviços.
Para 36h, os valores são 5,4506%, 8,0205%, 6,4889% (bilateral) e
3,7838%, 6,1934%, 4,7104% (fadiga). A_req agregado dos três setores é
0,0458% / 6,7613% na função bilateral e 0,0453% / 4,9771% na função
de fadiga para 40h / 36h. A forte revisão dos valores de 40h depende da
extrapolação da curva de eficiência para a cauda de jornadas longas observadas;
não é uma estimativa causal de ganho de produtividade da reforma.

A_req é a mudança **com sinal** que restaura exatamente o produto: valores
negativos significam que o contrafactual já eleva o produto sob as hipóteses
da curva de eficiência, permitindo reduzir A para restaurar o nível inicial.
Nesse caso, a compensação adicional não negativa requerida seria zero.
Resultados pontuais devem ser lidos junto com as sensibilidades e a alternativa
de topcode de 44h, sem interpretar uma delas como parâmetro identificado.
