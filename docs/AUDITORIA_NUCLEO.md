# Auditoria do núcleo quantitativo

Data da execução: 5 de setembro de 2026. Este documento descreve as correções matemáticas e numéricas. As entradas legadas abaixo são preservadas como cenário condicional: a auditoria de PNAD/RAIS e a versão de dados reprocessados são registradas separadamente. Nenhum parâmetro foi escolhido para recuperar resultados do manuscrito.

## Código alterado e compatibilidade

| Arquivo | Alteração |
|---|---|
| `src/model/efficiency.py` | Uma função de eficiência, com modos bilateral e fadiga apenas acima do pico; distribuição genérica de horas validada; erro explícito quando a elasticidade local não identifica curvatura admissível. |
| `src/model/ces_aggregator.py` | Limites corretos em zero, limite Cobb–Douglas estável e marginais CES; unidade semanal/horária/efetiva explícita. |
| `src/model/production.py` | Produto zero quando o insumo agregado é zero; remoção do piso artificial de trabalho na produção; validação de domínio. |
| `src/model/firm_problem.py` | Solução contínua da FOC com concavidade, limites direcionais e comparação de objetivos nas fronteiras; avaliação de composição fixa; restrição de recursos explícita. |
| `src/model/calibration.py` | Cunhas obtidas da FOC no momento-alvo sob normalização declarada; não retornar limites arbitrários quando um momento não pode ser ajustado. |
| `src/model/groups.py` | Conversão de participação no emprego formal para total; leitura das participações e informalidade dos targets; âncora externa opcional da eficiência. |
| `src/model/areq_solver.py` | Raiz com bracket verificado, reotimização em cada produtividade preservada, compensação assinada e composição congelada adicional. |
| `src/model/decomposition.py` | Decomposição exata em níveis intermediários com denominador comum. |
| `src/model/welfare.py` | Separação entre variação do composto GHH e equivalente de consumo. |
| `src/model/simulation.py` | Motor comum nacional/setorial; diagnósticos completos; capital fixo e unidade de bem-estar declarados. |
| `tests/test_model.py` | Testes de matemática e contabilidade substituem regressões que impunham os valores antigos. |
| `tests/test_wage_bridge.py` | Testes independentes da ponte por folha de remuneração, marginais e calibração condicional de omega. |

Os argumentos posicionais originais foram mantidos. `grid` é aceito por compatibilidade, mas não discretiza a escolha. Novas opções aparecem ao final: `efficiency_mode`, `hours_bins`, `share_basis`, `resource_costs`, `kappa_override`, conforme a função. `dCV_pct` permanece **alias depreciado da variação GHH**, nunca deve ser rotulado como CE. A função `compensating_variation`, por sua vez, passa a devolver CE corretamente normalizado; o cálculo explícito do composto está em `ghh_change`.

## Participações e contabilidade de emprego

Se `sF_g` é a participação do grupo nos empregos formais e `i_g` é sua informalidade, então:

```text
sN_g = [sF_g / (1 - i_g)] / sum_j[sF_j / (1 - i_j)]
NF_g = N_total * sN_g * (1 - i_g)
NI_g = N_total * sN_g * i_g
i_aggregate = sum_g NI_g / N_total
```

Para 59%/41% de participação formal e informalidade de 50%/20%, as participações no emprego total são **69,7193501% / 30,2806499%** e a informalidade agregada é **40,9158050%**. Recuperar 59% da massa formal é um teste de contabilidade; esse exemplo não comprova qualquer estimativa RAIS ou PNAD.

O modo explícito `share_basis='total'` existe apenas para diagnóstico da interpretação antiga. O padrão é `'formal'`. `omega` é peso tecnológico CES e não é igualado à participação formal.

## Tecnologia, eficiência e escolha contínua

```text
e_bilateral(h) = exp[-kappa * (h - h_star)^2]
e_flat_below(h) = exp[-kappa * max(h - h_star, 0)^2]
qF = sum_b theta_b * min(h_b, cap) * e(min(h_b, cap))
qI = hI * e(hI)
LF = NF * qF
LI = eta_I * NI * qI
rho = (sigma - 1) / sigma
L = [omega * LF^rho + (1 - omega) * LI^rho]^(1/rho)
Y = A * K^alpha * L^(1 - alpha)
```

O pico é da eficiência **por hora**, não automaticamente do produto total. A elasticidade `E_Q` usada para fixar kappa é a elasticidade local de `h*e(h)`; não é a elasticidade de Y agregado, que também depende de Cobb–Douglas, CES e composição. Os valores 0,6 e 40h continuam hipóteses de transporte de evidência externa, não estimativas brasileiras identificadas pelo modelo.

A calibração local é `kappa = (1 - E_Q)/(2*h_ref*(h_ref-h_star))`. Para fadiga somente acima do pico, a curvatura não é identificada localmente abaixo do pico por E_Q diferente de 1. Nesses casos, o código falha explicitamente ou usa `kappa_override`/target `H_REF_EFFICIENCY` declarado pelo experimento. É possível preservar como hipótese a âncora legada de 42,244h, separada de uma nova distribuição empírica cuja média seja inferior a 40h.

A firma escolhe `NF in [0,N]`, com `NI=N-NF`, para maximizar:

```text
J(NF) = Y(NF, N-NF) - tau*NF - pi*NI^2/2
        - gamma*(NF-NF_prev)^2/2

J'(NF) = MP_NF - MP_NI - tau + pi*NI - gamma*(NF-NF_prev)
```

Os marginais são semanais por trabalhador adicional, mantendo a outra modalidade fixa. Para sigma>0, 0<alpha<1 e custos convexos não negativos, a tecnologia composta é côncava. A FOC interior e as desigualdades de fronteira são, portanto, suficientes para um máximo global.

A implementação usa Brent na derivada e compara o objetivo final aos dois extremos. Para uma fronteira inferior exige `J'(0+)<=0`; para a superior, `J'(N-)>=0`. Com CES misto, A>0 e alpha>0, os limites são +infinito/-infinito; uma solução finita é interior. Para A=0 e pesos CES puros, os limites específicos são calculados. Se uma solução interior estiver tão próxima de uma fronteira que a precisão numérica não permita certificar a FOC, o código acusa erro, em vez de declarar uma fronteira ótima por arredondamento.

As soluções devolvem `foc_residual`, `kkt_violation`, `boundary` e objetivos nos extremos. Os testes incluem minimização escalar independente, valores de uma grade de comparação, derivadas por diferenças finitas e casos de fronteira.

## Normalização de tau e pi

Uma taxa de informalidade por grupo identifica apenas uma combinação de custos no ponto inicial. Definindo `D=MP_NF-MP_NI` no emprego-alvo e `NF_prev=NF_target`:

```text
tau - pi*NI_target = D
tau >= 0, pi >= 0, tau*pi = 0

if D >= 0: tau = D, pi = 0
if D <  0: tau = 0, pi = -D/NI_target
```

A complementaridade é uma **normalização**, não identificação empírica separada. No cenário congelado, bilateral, sigma=1,326 e omega=0,622, ela produz tau_pequenas=2,4595596051, pi_pequenas=0; tau_grandes=0, pi_grandes=63,0702735245. A mudança da participação total altera a escala de N e, consequentemente, o coeficiente quadrático. Isso não é uma estimativa observada de fiscalização ou informalidade.

## Compensação de produto

A equação resolvida é:

```text
sum_g Y_g(A_g * a, cap, NF_g*(a)) = Y_baseline
A_req_pct = 100 * (a - 1)
```

A reotimização de composição **já existia** no solver anterior e foi preservada dentro de cada avaliação de a. O bracket agora é verificado e ampliado adaptativamente, e o resultado é aceito somente se o produto final restaura o alvo com erro relativo inferior a 1e-9.

`A_req_frozen_pct` congela a composição efetivamente obtida no baseline. Como Y é linear em A para essa composição, a raiz é diretamente `Y_target/Y_frozen_at_A1`. Ambas as compensações se referem a produto bruto, não consumo líquido dos custos.

A_req é assinada: se o cenário elevar produto, a restauração exata pode exigir redução de A. O campo adicional `nonnegative_gain_pct` distingue a necessidade de ganho não negativo. Capital e emprego total são fixos; não há equação de acumulação/investimento ou incidência distributiva neste exercício.

## Decomposição exata

A ordem declarada é **horas físicas → eficiência → realocação formal–informal**:

1. Y0: produto do baseline.
2. YH: novas horas por faixa, mantendo a eficiência antiga de cada faixa e NF/NI antigos.
3. YE: novas horas e nova eficiência, mantendo NF/NI antigos.
4. Y1: novas horas, nova eficiência e NF/NI reotimizados.

```text
hours_pct        = 100*(YH-Y0)/Y0
efficiency_pct   = 100*(YE-YH)/Y0
reallocation_pct = 100*(Y1-YE)/Y0
total_pct        = 100*(Y1-Y0)/Y0
```

As parcelas somam exatamente à variação total, a tolerância numérica. A alocação das interações depende da ordem; não há alegação de decomposição única. Identidades dos pesos de horas são testes de mapeamento contábil, não validação comportamental.

## Recursos, GHH e CE

No padrão preservado e agora declarado, tau*NF e pi*NI²/2 são pagamentos privados transferidos integralmente ao domicílio representativo. O custo de ajuste é um recurso destruído:

```text
C + adjustment = Y
```

A opção explícita `resource_costs=True` destrói também os custos formais e informais:

```text
C + adjustment + tau*NF + pi*NI^2/2 = Y
```

A mudança de interpretação de recursos não altera a função objetivo privada nem NF; altera C e bem-estar. A modelagem de transferências não identifica quem paga/recebe individualmente.

O consumo agregado é convertido para consumo por trabalhador. h é a média de horas físicas do domicílio representativo, conforme a especificação original; não se está identificando a distribuição do bem-estar por tipos nem calculando média de utilidades individuais com horas heterogêneas.

```text
v(h) = psi*h^(1+nu)/(1+nu)
GHH = C-v(h)
dGHH_pct = 100*(GHH1-GHH0)/GHH0
CE_pct = 100*[C1-C0-v(h1)+v(h0)]/C0
```

O teste de CE verifica diretamente `GHH(C0*(1+CE),h0)=GHH(C1,h1)`. Denominadores inválidos não são substituídos por um pequeno número positivo. psi é uma normalização da condição representativa `psi*h^nu=w_hourly`, com nu=2 e remuneração horária média imputada pela parcela de trabalho no produto inicial.

## Resultados do núcleo com entradas congeladas

Execução nova nesta auditoria: `run_simulation(targets,sigma_sub=1.326,omega=.622,...)`. As entradas legadas foram mantidas, mas a contabilidade dos grupos foi corrigida. Esta tabela não incorpora nova ponte de remunerações nem dados reprocessados.

| Eficiência | Teto | dY (%) | A_req (%) | A_req congelada (%) | Informalidade final (%) | dGHH (%) | CE (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bilateral | 40h | -2,012868 | 1,923198 | 1,868131 | 41,451152 | 0,233822 | 0,183161 |
| Bilateral | 36h | -8,070837 | 8,176827 | 7,945313 | 43,141251 | -4,061067 | -3,181169 |
| Só acima do pico | 40h | -2,008443 | 1,918736 | 1,863750 | 41,450163 | 0,239549 | 0,187647 |
| Só acima do pico | 36h | -6,630582 | 6,621991 | 6,433753 | 42,729182 | -2,168696 | -1,698812 |

O baseline tem informalidade de 40,915805% em ambos os modos. A proximidade de um A_req corrigido ao valor antigo não é evidência de parâmetros ajustados para recuperar resultados.

## Revisão independente da ponte de remuneração

`src/calibration/wage_bridge.py` calcula o produto marginal em cada grupo antes de agregar. Para remuneração semanal por trabalhador:

```text
WF_g = MP_LF_g * qF_g
WI_g = MP_LI_g * eta_I_g*qI_g
PF = sum_g NF_g * WF_g
PI = sum_g NI_g * WI_g
R_weekly = (PF/sum_g NF_g) / (PI/sum_g NI_g)
R_hourly = (PF/sum_g NF_g*hFavg_g) / (PI/sum_g NI_g*hI_g)
```

A identidade de Euler `PF_g+PI_g=(1-alpha_g)*Y_g` vale e foi testada. Fazer CES dos LF/LI nacionais e calcular uma única razão não é equivalente a agregar folhas de firmas heterogêneas, como também verificado por teste.

A ponte **horária é uma razão de massas de remuneração sobre totais de horas**. Não é a razão de médias individuais `E[renda/horas]`. Um alvo PNAD deve corresponder ao mesmo estimando, ponderação e universo de renda/horas válidas. Rendimentos mensais podem ser divididos pelo mesmo fator mensal/semanal em ambas as modalidades; o fator comum cancela na razão.

O cenário congelado implica R_semanal=1,6300605633 e R_horário=1,6978189751. Mantendo sigma=1,326 e usando o alvo **hipotético** R_horário=1,40, a raiz condicional é omega=0,5761673523 no modo bilateral e 0,5760195129 no modo acima do pico. Não é omega=participação formal e não identifica conjuntamente sigma, omega, eta e custos. A equiparação entre produto marginal bruto e remuneração observada exige uma hipótese competitiva adicional; a escolha privada com N fixo não contém, por si só, equação salarial ou incidência.

A revisão de `corrected_pipeline.py` confirmou que cenários numéricos, calibração da ponte e alteração dos dados são rotulados separadamente; sigma permanece 1,326 nas comparações centrais. A grade de sensibilidade inclui pontos interiores e registra restrição horária suposta em [1,15;1,55], sem chamar a caixa de conjunto identificado.

## Testes executados

Comando: `python -m unittest discover -s tests -v`.

Na revisão do núcleo e da ponte, passaram 46 testes: 27 do núcleo, 9 da ponte e 10 setoriais já integrados. Incluem:

- contabilidade formal/total, recuperação exata das taxas-alvo e leitura de novos targets;
- limites CES, continuidade Cobb–Douglas e calibração por derivada numérica;
- dois modos de eficiência e distribuições genéricas;
- concavidade operacional, FOC, fronteiras e comparação com minimização independente;
- reotimização ao longo da raiz e compensação com composição congelada;
- restauração de produto, soma da decomposição e restrição de recursos;
- CE por igualdade do composto, distinção entre denominadores e remuneração semanal/horária;
- folhas por firma, Euler e raiz condicional de omega mantendo sigma fixo.

Os resultados antigos permanecem no snapshot arquivado pelo processo principal. Não há teste que force o novo código a reproduzir os antigos valores de A_req, GHH ou produto.

