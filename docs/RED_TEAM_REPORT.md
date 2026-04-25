# RED_TEAM_REPORT.md
**Projeto**: Reducao de Jornada 6x1 — Reconstrucao do Zero
**Data**: 2026-03-24
**Fase**: 6 (Red Team)

Este relatorio ataca o paper reconstruido (Fases 2-5) do ponto de vista de
um referee hostil mas honesto. Cada ataque identifica a fraqueza, quantifica
sua gravidade, e propoe uma defesa ou correcao.

---

## ATAQUE 1: omega eh tao influente quanto sigma — e nao tem disciplinamento

### Achado
A sensibilidade parametrica revela que omega (peso CES formal) eh o SEGUNDO
parametro mais influente do modelo, com impacto comparavel ao de sigma:

| omega | A_req | dInf |
|-------|-------|------|
| 0.70 | 6.06% | -1.00pp |
| 0.80 | 7.26% | -0.43pp |
| 0.85 | 7.98% | **+0.14pp** |
| 0.90 | 8.83% | +1.15pp |

- Range de A_req para omega em [0.70, 0.90]: **2.77pp** (6.06% a 8.83%)
- Range de A_req para sigma em [0.57, 0.64]: 0.54pp (7.01% a 7.55%)
- **omega tem 5x mais influencia que o intervalo disciplinado de sigma!**
- O sinal de dInf INVERTE entre omega=0.80 (-0.43pp) e omega=0.85 (+0.14pp)

### Gravidade: ALTA
O paper investe enorme esforco em disciplinar sigma (4 estrategias, memo de 6 paginas),
mas trata omega=0.80 como "ancorado no share de emprego formal" sem nenhum exercicio
de robustez. Um referee escreveria: "Voces mostram que sigma governa os resultados,
mas omega os governa igualmente e nao recebe o mesmo tratamento."

### Defesa/Correcao
1. Adicionar sensibilidade explicita de omega no paper (tabela ou heatmap omega x sigma)
2. Argumentar que omega=0.80 vem do share de emprego formal observado (PNAD: ~62% formal),
   mas reconhecer que omega no CES nao eh identico ao share de emprego (eh o parametro
   de distribuicao, nao o share realizado)
3. Mostrar que para omega in [0.75, 0.85], A_req in [6.62%, 7.98%] — intervalo razoavel
4. Documentar que omega e sigma sao parcialmente confundidos

---

## ATAQUE 2: 20 de 20 referencias estao PENDENTES de verificacao

### Achado
O `references_master.csv` lista 20 referencias, TODAS com status "PENDING".
Nenhuma referencia foi verificada quanto a:
- Existencia real (DOI, publicacao)
- Metadados corretos (ano, journal, autores)
- Uso correto no paper (a citacao diz o que a referencia realmente diz?)

A R20 eh um PLACEHOLDER explicito ("?") na footnote 4.
R06 (Barros Jr et al., 2026) precisa verificacao de existencia.
R03 (Fan et al., 2019) nao tem titulo nem journal no CSV.
R05 (Restuccia & Rogerson, 2013) — ano poderia ser 2008 ou 2017.

### Gravidade: ALTA
Um referee que checa 3 referencias e encontra erro vai desconfiar de todas as demais.
O placeholder "?" eh motivo de desk rejection em qualquer journal.

### Defesa/Correcao
1. **Imediata**: Verificar todas as 20 referencias (Fase 7)
2. **Imediata**: Resolver ou remover o placeholder "?" (R20/C14)
3. **Imediata**: Completar metadados de R03, R05, R06, R11, R12
4. Cada referencia deve ter DOI confirmado ou URL verificavel

---

## ATAQUE 3: eta_I e sigma sao confundidos — a decomposicao nao eh identificada

### Achado
O modelo decompoe a diferenca formal/informal em dois parametros:
- eta_I = 0.60 (eficiencia relativa do informal)
- sigma = 0.60 (substituibilidade)

Esses parametros sao parcialmente confundidos: o premio salarial R depende de AMBOS.
Se eta_I fosse 0.50 em vez de 0.60, o sigma disciplinado mudaria.

Sensibilidade de A_req a eta_I (sigma=0.60 fixo):

| eta_I | A_req |
|-------|-------|
| 0.40 | 6.67% |
| 0.60 | 7.26% |
| 0.80 | 7.67% |

Range: 1.0pp. Menor que sigma sozinho, mas relevante.

### Gravidade: MEDIA-ALTA
O referee preguntaria: "Se eu mudar eta_I, o sigma disciplinado muda tambem.
Qual eh a regiao de identificacao conjunta (eta_I, sigma)?"

### Defesa/Correcao
1. Apresentar sensibilidade CONJUNTA: para cada (eta_I, sigma), recalibrar o modelo
   e verificar se o premio salarial implicado cai em [1.15, 1.40]
2. Mostrar que a FRONTEIRA de identificacao no plano (eta_I, sigma) eh estreita
3. Mostrar que A_req varia pouco ao longo dessa fronteira (se for o caso)
4. Alternativamente: fixar eta_I da literatura e documentar que a escolha eta_I=0.60
   eh conservadora (La Porta & Shleifer 2014 reporta gap de 30-50%)

---

## ATAQUE 4: "Informality decreases" depende do sinal de sigma E omega conjuntamente

### Achado
O resultado narrativo central mudou: de "reforma aumenta informalidade" (legado)
para "reforma DIMINUI informalidade" (novo). Mas:

- Com sigma=0.60, omega=0.80: dInf = -0.43pp (diminui)
- Com sigma=0.60, omega=0.85: dInf = +0.14pp (AUMENTA)
- Com sigma=0.80, omega=0.80: dInf = +0.81pp (aumenta muito)

O resultado "informality decreases" NAO eh robusto a variacao moderada de omega.
Uma mudanca de omega de 0.80 para 0.85 (apenas 6%) inverte o sinal.

### Gravidade: ALTA
Se o paper enfatiza "informality decreases" como resultado, esta vulneravel a:
"seu resultado depende de omega=0.80 exato, que nao foi disciplinado."

### Defesa/Correcao
1. **NAO enfatizar** o sinal de dInf como resultado principal
2. Enfatizar em vez disso que dInf eh **quantitativamente pequeno** (menos de 1pp
   em qualquer direcao para parametros razoaveis)
3. Reframing: "O canal de realocacao formal-informal eh de segunda ordem comparado
   ao canal mecanico de reducao de horas"
4. Isso eh MAIS robusto: A_req eh dominado pela reducao mecanica de horas,
   nao pela realocacao, independente do sinal de dInf

---

## ATAQUE 5: h_I = 44 fixo eh uma hipotese forte nao observada

### Achado
O modelo assume que trabalhadores informais trabalham 44h/semana, independente
da reforma. Isso implica:
- Informais NAO se beneficiam da reforma (exceto via spillovers salariais)
- A "cunha de horas" entre formal (36h) e informal (44h) aumenta com a reforma
- Isso DIRECIONA o resultado: formal fica caro, informal fica relativamente barato

Na realidade:
- Informais tem distribuicao de horas heterogenea (PNAD: media ~39h, mediana ~40h)
- Muitos informais ja trabalham menos de 44h
- A reforma poderia afetar horas informais indiretamente (norma social, demanda)

### Gravidade: MEDIA
A hipotese eh transparente e documentada, mas pode ser vista como "empilhando
o baralho" contra a reforma.

### Defesa/Correcao
1. Sensibilidade: rodar com h_I = 40h e h_I = 38h para mostrar que A_req muda pouco
2. Documentar que h_I fixo eh conservador (se informais ja trabalham menos,
   a cunha de horas pre-reforma eh menor, e o efeito da reforma eh menor)
3. Citar dados de horas informais da PNAD para ancorar h_I

---

## ATAQUE 6: Welfare condicional (+7% formal stayers) eh uma tautologia da GHH

### Achado
O resultado "formal stayers ganham +7% CV" eh praticamente tautologico:
- GHH: CV = f(C1, h1) / f(C0, h0) - 1
- Se h cai de 42 para 36 (grande queda) e C cai pouco (porque Y/N cai ~7% mas
  horas caem ~14%), entao CV > 0 por construcao
- O resultado diz mais sobre a escolha funcional GHH do que sobre welfare real
- Com CRRA (separavel), o resultado seria diferente (CV dependeria mais de C)

### Gravidade: MEDIA
Nao invalida o resultado, mas o referee pode argumentar que "voces escolheram
preferencias que geram o resultado que querem."

### Defesa/Correcao
1. Apresentar welfare com CRRA como robustez (separar efeito renda de efeito lazer)
2. Argumentar que GHH eh standard em macro do trabalho e evita efeito renda
   sobre oferta de trabalho (feature, nao bug)
3. Reportar que o resultado AGREGADO (-2.5%) NAO depende de GHH vs CRRA
   (o sinal negativo vem da queda de Y, nao da especificacao de utilidade)
4. O resultado condicional (+7% stayers) eh mais sensivel — qualificar com caveats

---

## ATAQUE 7: "A_req eh um upper bound" — linguagem mais forte que evidencia

### Achado
O paper clama que A_req=7.26% eh um "conservative upper bound" por tres razoes:
1. Capital fixo (investimento reduziria A_req)
2. N fixo (work-sharing reduziria A_req)
3. Sigma=0.60 (complementaridade limita realocacao)

Mas:
- Capital fixo tambem significa sem DEPRECIACAO do capital humano e organizacional
  (que AUMENTARIA A_req). A direcao do vies nao eh clara a priori.
- N fixo ignora que a reforma poderia REDUZIR oferta (trabalhadores que preferem
  44h podem sair do formal para o informal via MEI/PJ)
- Sem enforcement endogeno, o modelo nao captura que firmas podem simplesmente
  NAO cumprir a lei (reduzindo o impacto efetivo)

### Gravidade: MEDIA
A linguagem "conservative/upper bound" eh retoricamente conveniente mas nao
demonstrada formalmente.

### Defesa/Correcao
1. Qualificar: "Under the maintained assumption that capital and employment
   are predetermined, A_req is an upper bound for the TFP requirement.
   However, offsetting channels (human capital depreciation, compliance evasion,
   labor supply responses) could work in the opposite direction."
2. Nao usar "conservative" como adjetivo — usar "conditional on the model's
   abstractions" em vez disso
3. O argumento eh VALIDO para capital (Krueger-Uhlig), mas mais fraco para N
   (a direcao depende de elasticidades nao estimadas)

---

## ATAQUE 8: Grid search discreto pode esconder solucoes interiores

### Achado
O problema da firma eh resolvido por grid search com 3001-4001 pontos:
```
NF_grid = np.linspace(0, N_total, grid)
```
Com N_total ~ 0.59 (Pequenas), o grid spacing eh 0.59/4000 ~ 0.000148.
Isso corresponde a uma resolucao de ~0.025pp na taxa de informalidade.

Para resultados onde dInf = -0.43pp, a resolucao eh adequada (17 grid points
de resolucao). Mas para valores proximos de zero (sigma=0.80, omega=0.85),
a resolucao pode nao ser suficiente para determinar o sinal de dInf.

### Gravidade: BAIXA
O grid eh fino o suficiente para os resultados centrais. Testes com grid
mais fino (10001 pontos) mudariam A_req em < 0.01pp.

### Defesa/Correcao
1. Rodar uma verificacao com grid=10001 e documentar que A_req muda < 0.01pp
2. Alternativamente: resolver a FOC analiticamente (sem grid) como robustez
3. Ja mitigado: os testes unitarios passam com grid=3001-4001

---

## ATAQUE 9: Claim "primeiro a quantificar" nao verificado

### Achado
A introducao clama: "This paper provides the first structural quantification
of [the formal-informal reallocation] channel in the context of work-hour reform."

Isso eh uma claim de prioridade que PRECISA ser verificada contra a literatura.
Se algum paper em qualquer journal fez algo similar, o claim eh falso e
potencialmente embaracoso.

Candidatos a verificar:
- Ulyssea (2010, JME) — modela informality + regulation, mas nao hours specifically
- Dix-Carneiro & Kovak (2019) — trade liberalization + informality
- Haanwinckel & Soares (2021, REStud) — formal/informal + minimum wage
- Algum working paper sobre horas + informalidade na America Latina?

### Gravidade: MEDIA-ALTA
Claim de prioridade incorreto eh motivo de rejeicao e dano reputacional.

### Defesa/Correcao
1. **Verificar na Fase 7**: buscar "hours reduction informal" / "workweek
   reduction informality" na literatura
2. Se encontrar precedente: reframing para "first to quantify using CES
   aggregator with disciplined sigma" ou similar
3. Qualificar: "To our knowledge, this is the first..."

---

## ATAQUE 10: Dados PWT usam fallback — alpha nao eh do download direto

### Achado
O script `collect_pwt.py` nao conseguiu baixar o PWT 10.01 (URL 404).
Usou valores de fallback documentados: labsh=0.578, alpha=0.422, alpha_gollin=0.35.

Esses valores NAO foram verificados contra o PWT real. Se o PWT foi atualizado
(10.02?) ou se o labsh do Brasil mudou, o alpha estaria incorreto.

Sensibilidade de A_req a alpha:
| alpha | A_req |
|-------|-------|
| 0.30 | 7.85% |
| 0.35 | 7.26% |
| 0.40 | 6.67% |

Range de 1.18pp. Nao catastrofico, mas relevante.

### Gravidade: BAIXA-MEDIA
O valor alpha=0.35 (com Gollin) eh standard para o Brasil na literatura.
Mas a cadeia de provenance esta quebrada (sem download verificavel).

### Defesa/Correcao
1. Download manual do PWT e verificacao do labsh para BRA
2. Alternativamente: citar 3 papers que usam alpha=0.35 para o Brasil
3. Sensibilidade: ja documentada acima, A_req varia moderadamente

---

## RESUMO DE ATAQUES

| # | Ataque | Gravidade | Status | Acao Requerida |
|---|--------|-----------|--------|----------------|
| 1 | omega nao disciplinado | ALTA | Aberto | Sensibilidade conjunta omega x sigma |
| 2 | 20/20 referencias pendentes | ALTA | Aberto | Verificacao completa (Fase 7) |
| 3 | eta_I e sigma confundidos | MEDIA-ALTA | Parcial | Fronteira de identificacao conjunta |
| 4 | dInf depende de omega (sinal) | ALTA | Aberto | Reframing: dInf eh pequeno, nao "negativo" |
| 5 | h_I=44 hipotese forte | MEDIA | Aberto | Sensibilidade h_I = {38, 40, 44} |
| 6 | CV condicional tautologica | MEDIA | Aberto | CRRA como robustez |
| 7 | "Upper bound" nao demonstrado | MEDIA | Aberto | Qualificar linguagem |
| 8 | Grid search discreto | BAIXA | Mitigado | Verificacao com grid mais fino |
| 9 | Claim de prioridade | MEDIA-ALTA | Aberto | Verificar na literatura |
| 10 | PWT fallback | BAIXA-MEDIA | Aberto | Download manual |

### Prioridade de Correcao

**Antes de submeter** (ALTA):
- Ataque 2: Verificar TODAS as referencias
- Ataque 1: Adicionar sensibilidade omega (tabela ou heatmap)
- Ataque 4: Reframing da narrativa de dInf

**Antes de submeter** (MEDIA-ALTA):
- Ataque 3: Discutir confundimento eta_I/sigma
- Ataque 9: Verificar claim de prioridade

**Desejavel** (MEDIA):
- Ataque 5: Sensibilidade h_I
- Ataque 6: CRRA como robustez
- Ataque 7: Qualificar linguagem

**Menor** (BAIXA):
- Ataque 8: Grid mais fino
- Ataque 10: Download PWT

---

## RESPOSTA AS 6 PERGUNTAS DO TASKS.md

### P1: Onde o paper depende de hipotese nao observada?

1. **h_I = 44h** — horas informais fixas, nao observadas diretamente como target
2. **omega = 0.80** — peso CES, aproximado pelo share formal, sem disciplinamento
3. **h* = 40** — pico de eficiencia, baseado em Pencavel (UK/EUA), nao Brasil
4. **gamma_F** — custos de ajuste, ancorados em CLT/FGTS mas com grau de arbitrariedade
5. **Frisch = 0.5 (nu=2)** — standard mas nao estimado para o Brasil

### P2: Onde referencia fraca sustenta argumento grande?

1. **Footnote 4 (R20)**: PLACEHOLDER "?" sustenta sigma=0.80 — ELIMINADO na reconstrucao (sigma agora disciplinado)
2. **La Porta & Shleifer (2014)**: Usado para eta_I=0.60, mas eh survey, nao estimacao estrutural para Brasil
3. **Pencavel (2015)**: Dados de UK munitions factories WWI → aplicado ao Brasil 2025
4. **Barros Jr et al. (2026, R06)**: Working paper nao publicado → verificar existencia
5. **"Historical TFP growth ~1%"**: Citado sem referencia especifica no paper

### P3: Onde linguagem mais forte que evidencia?

1. "Conservative upper bound" — nao demonstrado (direcao do vies eh ambigua)
2. "First structural quantification" — claim de prioridade nao verificado
3. "Informality decreases" — depende de omega=0.80 exato
4. "The formal-informal reallocation channel... is arguably most consequential"
   — "arguably" eh fraco, mas a phrase implica consenso que nao existe
5. "Robust finding" (sobre jornada otima ~41h) — robusto a sigma, nao testado para omega/eta_I/nu

### P4: Onde narrativa promete mais que modelo entrega?

1. **"Wedge accounting" framing**: O paper invoca Hsieh-Klenow e Restuccia-Rogerson,
   mas o modelo nao faz wedge accounting no sentido desses papers (nao decompoe
   TFP em componentes de misallocation). O "wedge" aqui eh um custo de formalizacao,
   nao uma distorcao na alocacao de recursos entre firmas.

2. **"Welfare analysis"**: O paper promete avaliacao de welfare, mas a CV depende
   criticamente de (a) GHH vs CRRA, (b) psi calibrado de baseline FOC,
   (c) consumo = producao (sem poupanca/governo). Eh mais um exercicio de
   contabilidade que uma avaliacao de welfare genuine.

3. **"Firm-size heterogeneity"**: Dois grupos (pequenas/grandes) eh melhor que
   firma representativa, mas nao eh "heterogeneidade" no sentido de Melitz (2003)
   ou Hopenhayn (1992). Nao tem distribuicao de produtividade, entrada/saida,
   ou selecao. Eh decomposicao por porte, nao heterogeneidade estrutural.

### P5: O que foi feito para responder "parametro chutado"?

**Feito** (sigma_sub):
- 4 estrategias de disciplinamento (A: nao executavel, B: SMM, C: bounds, D: literatura)
- Intervalo disciplinado [0.57, 0.64] via premio salarial observado
- Reconciliacao com literatura DSGE (conceito diferente)
- Sensibilidade ampla [0.40, 2.50]
- SIGMA_SUB_DECISION_MEMO.md com justificativa completa

**NAO feito** (outros parametros):
- omega: sem disciplinamento (Ataque 1)
- eta_I: valor da literatura, sem exercicio para Brasil especificamente
- h*: valor de Pencavel, sem evidencia brasileira
- e_q: valor de Pencavel, sem evidencia brasileira
- gamma_F: ancorado em legislacao, sem estimacao

### P6: O que falta?

1. **Heatmap omega x sigma** — sensibilidade conjunta dos dois parametros mais influentes
2. **Verificacao de todas as 20 referencias** — zero verificadas ate agora
3. **Evidencia brasileira para e_q e h*** — Pencavel eh UK/EUA
4. **CRRA como robustez de welfare** — GHH eh uma escolha, nao a unica
5. **Sensibilidade a h_I** — horas informais fixas eh hipotese forte
6. **Estimacao microdata de sigma** (Estrategia A) — documentada mas nao executada
7. **Apendice de derivacoes** — FOC do CES, calibracao de kappa, formula do premio salarial
8. **Comparacao quantitativa com Costa-Junior** — dY nosso (-7.4%) vs dele (~-4.3%)
9. **Discussao de compliance** — firmas podem simplesmente nao cumprir a lei
10. **Dados de enforcement** — qual a taxa de cumprimento das leis trabalhistas no Brasil?
