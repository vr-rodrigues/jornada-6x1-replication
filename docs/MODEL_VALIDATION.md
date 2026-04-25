# MODEL_VALIDATION.md
**Data**: 2026-03-24
**Fase**: 4 (Reconstrucao do Modelo)

---

## 1. Estrutura Modular

O modelo foi decomposto em 9 modulos independentes em `src/model/`:

| Modulo | Responsabilidade | Dependencias |
|--------|-----------------|--------------|
| `production.py` | Cobb-Douglas Y=AK^a L^(1-a), MPL | nenhuma |
| `ces_aggregator.py` | CES L=[wLF^p+(1-w)LI^p]^(1/p), wage premium | nenhuma |
| `efficiency.py` | e(h)=exp{-k(h-h*)^2}, kappa, horas hetero | nenhuma |
| `firm_problem.py` | Otimizacao da firma (grid search NF) | production, ces, efficiency |
| `calibration.py` | Biseccao de wedge, pi_m, psi | firm_problem |
| `areq_solver.py` | A_req por biseccao | firm_problem |
| `welfare.py` | GHH composite, DeltaCV | nenhuma |
| `groups.py` | Construcao de grupos (Pequenas/Grandes) | efficiency, firm_problem, calibration |
| `simulation.py` | Loop completo: baseline -> reforma -> A_req -> welfare | todos |

## 2. Testes Unitarios

20 testes em 6 classes, todos passando (0.4s):

### TestBaselineReproducesTargets (4 testes)
- `test_kappa_value`: kappa = 2.110e-03 (match legado)
- `test_efficiency_symmetry`: e(36) = e(44) (simetria em torno de h*=40)
- `test_full_pipeline_legacy`: sigma=0.80 → A_req=8.42%, dY=-8.66%, dCV=-4.29%
- `test_full_pipeline_new_sigma`: sigma=0.60 → A_req~7.26%, dInf < 0

### TestAreqMonotonicity (1 teste)
- A_req(44) < A_req(40) < A_req(36) < A_req(30) — confirmado

### TestSigmaSubSensitivity (2 testes)
- A_req(0.50) < A_req(0.60) < A_req(0.80) < A_req(1.50) — confirmado
- sigma in [0.57, 0.64] → A_req in faixa esperada

### TestHoursDistributionMapping (4 testes)
- theta soma 1.0
- avg_hours(cap=44) = 42.244 (correto)
- avg_hours(cap=36) = 36.0 (todos capped)
- avg_hours(cap=40) = 39.66 (bin 44 capped a 40)
- eff_hours < avg_hours quando bins desviam de h*

### TestWelfareObject (5 testes)
- GHH composite > 0 para parametros razoaveis
- CV = 0 quando baseline = reforma
- CV < 0 quando consumo cai (horas fixas)
- CV > 0 quando horas caem bastante (consumo fixo)
- psi roundtrip: w → psi → w (exato)

### TestSmallVsLargeFirmsHeterogeneity (3 testes)
- Pequenas: inf ~ 50%; Grandes: inf ~ 20%
- wedge_Pequenas > wedge_Grandes
- inf_agg entre inf_Pequenas e inf_Grandes

## 3. Validacao Cruzada

### sigma=0.80 (legado)
| Metrica | Modular | calibrate_all.py | Legacy | Match |
|---------|---------|-------------------|--------|-------|
| kappa | 2.110e-03 | 2.110e-03 | 2.111e-03 | OK |
| A_req | 8.42% | 8.42% | 8.42% | OK |
| dY | -8.66% | -8.66% | -8.66% | OK |
| dCV | -4.29% | -4.29% | -4.29% | OK |

### sigma=0.60 (novo baseline, Fase 3)
| Metrica | Modular | Esperado (SMM) |
|---------|---------|----------------|
| A_req | ~7.26% | 7.26% |
| dInf | < 0 | -0.43pp |
| dCV | ~-2.5% | -2.54% |

## 4. Cobertura

- **Primitivos**: production, CES, efficiency — testados diretamente
- **Solvers**: biseccao de wedge, pi_m, A_req — testados via pipeline completo
- **Welfare**: GHH composite, CV — testados com edge cases
- **Heterogeneidade**: grupos Pequenas/Grandes calibrados e verificados
- **Sensibilidade**: sigma grid [0.50, 1.50] — monotonicidade confirmada

## 5. O Que NAO Esta Coberto

- Convergencia numerica da biseccao (N_iter suficiente para tolerancia < 1e-5)
- Performance com grids muito finos (>10000 pontos)
- Comportamento com parametros extremos (sigma < 0.3 ou > 5.0)
- Welfare com sigma_ghh != 1.0 (log utility assumed)

Esses gaps sao aceitaveis para um working paper. Sensibilidade ampla (Fase 6) cobrira parametros extremos.
