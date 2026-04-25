# NR-17 Telemarketing Study — Research Design (revised)

## One-line summary

Worker- and cell-level event-study of the 2007 NR-17 Anexo II reform, which mandated a maximum 6h/day (36h/week) workday for telemarketing operators, using Brazilian administrative labor records (RAIS) from Base dos Dados. Outcomes: contractual hours, hourly wage, employment counts. Design adjusted from firm-level to worker- and cell-level because Base dos Dados does NOT expose establishment IDs (only aggregated identifiers: CBO, CNAE-subclasse, município, UF).

## Design update vs. original plan

The original plan (2026-04-21) was a firm-level Asai-Lopes-Tondini continuous DiD using firm pseudo-IDs in RAIS. On inspection, Base dos Dados' RAIS tables (`microdados_vinculos` and `microdados_estabelecimentos`) do not include any firm-level identifier. Getting firm IDs requires a formal MTE agreement (RAIS identificada). The design is therefore revised to two complementary specifications both implementable with public data:

- **Design A**: worker-level pooled cross-section DiD across CBOs.
- **Design B**: cell-level (CBO × CNAE-subclasse × UF × year) continuous-exposure event-study.

## Why this study

The structural paper `paper/overleaf/main.pdf` predicts that a 44→36h workweek reduction would cause a 7.4% short-run GDP loss, a small drop in informality, and a small endogenous productivity gain. The model is validated directionally against Portugal 1996 (Asai-Lopes-Tondini 2025), but there is no comparable Brazilian causal study. The NR-17 Anexo II reform of 2007 provides:

1. A **nationwide mandatory reduction from 44 to 36 hours** (identical delta to the PEC 8/2025 proposed reform).
2. A **specific occupation (CBO 4223, telemarketing operator)** identifiable in RAIS.
3. A fixed date (Portaria SIT 09/2007, published 30/03/2007, 120-day adaptation → effective ~August 2007).
4. **No compensating cuts** to social contributions (clean identification, as in Asai et al. — unlike the French 35h reform).
5. An early enough window to observe pre- and post-reform years before the 2008 financial crisis contaminates identification.

## Research question

What is the firm-level effect of a mandatory 44→36h workweek reduction on employment, wages, hours, and firm survival?

## Identification

### Design A — Worker-level pooled cross-section DiD

Repeated cross-section of vínculos (worker-year observations) comparing:

- **Treated**: all vínculos in CBO family 4223 (telemarketing operators).
- **Controls (primary)**: CBO 4110 (escriturários em geral) and CBO 4221 (telefonistas), both desk-work service occupations not covered by NR-17 Anexo II.
- **Controls (placebo)**: CBO 4212 (caixas de agências bancárias) — already subject to 6h workday since 1933 (CLT art. 224), so no effect expected.

Specification with CBO × UF × year fixed effects:

$$y_{ikut} = \alpha_k + \lambda_t + \gamma_u + \delta_{ut} + \sum_{k=-4,\, k\neq -1}^{+5} \beta_k \cdot T_i \cdot \mathbb{1}[t = 2007 + k] + X_{ikut}'\theta + \varepsilon_{ikut}$$

where $y_{ikut}$ is the outcome for vínculo $i$ in CBO $k$, UF $u$, year $t$; $T_i = 1$ if $i$ is in CBO 4223; $X$ is a vector of worker/job controls (sex, age, education, establishment size, tipo_vinculo). Clustering at CBO family × UF level.

### Design B — Cell-level continuous-exposure event-study

Aggregate to cells $c = (\text{CNAE-subclasse}, \text{UF})$ × year. For each cell $c$:

$$E_c = \frac{\text{# CBO 4223 vínculos in } c \text{ in 2006}}{\text{total vínculos in } c \text{ in 2006}}$$

Event-study:

$$y_{ct} = \alpha_c + \lambda_t + \sum_{k=-4,\, k\neq -1}^{+5} \beta_k \cdot E_c \cdot \mathbb{1}[t = 2007 + k] + \varepsilon_{ct}$$

where $y_{ct}$ is cell-level mean hours, mean wage, or ln total employment. Variation is across sectors and regions in their pre-reform exposure to NR-17.

### Identifying assumption (both designs)

Parallel trends: conditional on fixed effects, treated and control units would have followed similar trajectories without NR-17. Testable via pre-2007 coefficients $\beta_k$ for $k = -4, -3, -2$.

## Outcomes (firm-year panel)

Primary:
- $\ln(N_{ft})$: total employment
- $\ln(W_{ft})$: average hourly wage (monthly salary / contractual hours / 4.33)
- $\ln(H_{ft})$: average contractual hours per worker
- $\ln(\text{Wage bill}_{ft})$: total monthly wage bill

Secondary:
- Firm survival indicator (next year)
- Share of CBO 4223 (treatment intensity changes post-reform)
- Worker flows: hires, separations

## Data

**Primary source**: RAIS microdados (pseudonymized vínculo level) via Base dos Dados, table `br_me_rais.microdados_vinculos`. Pseudonymous stable firm IDs (`id_estabelecimento`) enable panel construction.

**Window**: 2003-2012 (4 pre-reform, 5 post-reform; truncate at 2012 to limit 2008 crisis contamination for the crucial 2007-2008 identification).

**Sample**:
- Firms with at least one CBO 4223 worker in at least one year 2003-2012, OR
- Firms in CNAE 8220 in any year.
- Minimum 5 workers to ensure meaningful firm-level aggregates.

**Robustness samples**:
- Firms in adjacent CNAEs (8211 - atividades de serviços combinados; 8299 - outras atividades de serviços) with some CBO 4223 presence.

## Threats to identification and mitigations

| Threat | Mitigation |
|---|---|
| 2008 financial crisis | Focus on 2007-2008 effect; extend to 2012 only as robustness |
| CNAE 1.0 → 2.0 transition in 2007 | Identify treatment via CBO (stable), not CNAE |
| Collective bargaining pre-2007 already shortening hours | Measure 2006 baseline hours; firms already at 36h are effectively untreated (heterogeneous intensity) |
| Enforcement heterogeneity by firm size | Analyze by size strata |
| Pausas and ergonomics confound | Report as the compound "NR-17 package"; note limitation |
| Terceirização / CNPJ changes | Track pseudonymous firm IDs; report firm-exit / new-firm separately |

## What we do NOT get (vs full Asai replication)

- **Output / productivity (sales) per firm**: requires IBGE PIA identified linkage, not available. Mitigation: report wage-per-hour and wage-bill-per-hour-total as proxies for marginal product of labor under competitive assumption.
- **Linkage to worker demographics**: pseudonymized worker ID prevents merging with external sources.

These are acceptable losses for a first firm-level Brazilian causal estimate.

## Deliverables (Sprint 1)

1. Panel construction (`build_panel.py`): RAIS query via `basedosdados`, firm-year aggregation, exposure variable construction.
2. Descriptive statistics (`descriptives.py`): size of sector, geographic distribution, pre-reform trends.
3. Event-study estimation (`event_study.py`): TWFE with firm clustering, dynamic coefficients, robustness checks.
4. Output: table + figures + memo.

## Timeline

- Day 1 (today): Setup + test query + panel construction starts.
- Day 2: Panel complete + descriptives.
- Day 3: Event-study main spec + robustness.
- Day 4: Writeup + integration decision (paper extension vs standalone WP).

## References

- Asai, K., Lopes, M., & Tondini, A. (2025). Firm-Level Effects of Reductions in Working Hours.
- Callaway, B., & Sant'Anna, P. (2021). Difference-in-Differences with Multiple Time Periods. JoE.
- Borusyak, K., Jaravel, X., & Spiess, J. (2024). Revisiting Event Study Designs. ReStud.
- Gonzaga, G., Menezes-Filho, N., & Camargo, J. (2003). Redução da Jornada de 48 para 44 Horas. RBE.
- NR-17 Anexo II, Portaria SIT 09/2007 (Diário Oficial da União, 30/03/2007).
