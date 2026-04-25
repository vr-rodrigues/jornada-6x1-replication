# DATA_PROVENANCE_BOOK.md
**Projeto**: Reducao de Jornada 6x1 — Reconstrucao do Zero
**Data**: 2026-04-23 (revisao pos-audit3)
**Status**: Fase 2 concluida, parametros atualizados pos-audit3 (omega, eta_I, MNR R)

---

## 1. Fontes de Dados

### 1.1 PNAD Continua Trimestral (IBGE/SIDRA)
- **Instituicao**: Instituto Brasileiro de Geografia e Estatistica (IBGE)
- **Pesquisa**: Pesquisa Nacional por Amostra de Domicilios Continua
- **API**: https://apisidra.ibge.gov.br
- **Tabelas utilizadas**: 4093, 4097, 6374, 6413
- **Script de coleta**: `src/data_raw/collect_pnad.py`
- **Arquivo intermediario**: `data_intermediate/pnad_targets.json`
- **SHA-256**: `f3ef59b66835b72d4d17c58b233d2a945ac78e5fc13a5de062aaeba8670b6e95`
- **Data de coleta**: 2026-03-24 (arquivo reestampado 2026-04-23 apos expansao)

### 1.2 Penn World Table 10.01
- **Instituicao**: University of Groningen (GGDC)
- **Referencia**: Feenstra, Inklaar, Timmer (2015, AER)
- **URL**: https://www.rug.nl/ggdc/productivity/pwt/
- **Script de coleta**: `src/data_raw/collect_pwt.py`
- **Arquivo intermediario**: `data_intermediate/pwt_targets.json`
- **SHA-256**: `4627e31a2a367034c1e31e5d07a6d65f2bb43d9342b7b0f51610b389a2fa6da7`
- **Data de coleta**: 2026-03-24
- **Nota**: Download do xlsx falhou (URL alterada); valores de fallback documentados usados

### 1.3 RAIS 2022 (Ministerio do Trabalho)
- **Instituicao**: Ministerio do Trabalho e Emprego
- **Base**: Relacao Anual de Informacoes Sociais
- **Script**: `src/data_raw/collect_rais.py`
- **Arquivo intermediario**: `data_intermediate/rais_targets.json`
- **SHA-256**: `fd9a1c44888f1fe03b2cc1252b48a2e0f3bbfe97663877d510fd574055f61747`
- **Nota**: Dados nao disponiveis via API publica. Valores documentados de relatorios RAIS/SEBRAE.

---

## 2. Targets de Calibracao

### INF_AGG — Taxa de informalidade agregada
- **Valor**: 37.8% (media 4 trimestres 2025)
- **Fonte**: PNAD Continua, Tabela 4093, variavel 12466
- **Trimestres**: Q1=38.0%, Q2=37.8%, Q3=37.8%, Q4=37.6%
- **Nota**: Paper original usa ~39%. Diferenca reflete atualizacao para dados 2025.

### INF_SMALL — Informalidade firmas pequenas (<=49 emp.)
- **Valor**: 50%
- **Fonte**: PNAD Continua / RAIS cross-reference
- **Nota**: Estimativa baseada em posicao na ocupacao x tamanho do empreendimento

### INF_LARGE — Informalidade firmas grandes (50+ emp.)
- **Valor**: 20%
- **Fonte**: PNAD Continua / RAIS cross-reference

### SHARE_SMALL — Share pequenas no emprego formal
- **Valor**: 59%
- **Fonte**: RAIS 2022
- **Nota**: Emprego formal apenas (vinculos ativos em 31/12)

### SHARE_LARGE — Share grandes no emprego formal
- **Valor**: 41%
- **Fonte**: RAIS 2022

### ALPHA — Capital share
- **Valor**: 0.35 (Gollin-adjusted)
- **PWT raw**: labsh = 0.578, alpha_raw = 0.422
- **Ajuste Gollin**: Corrige renda do trabalho autonomo (2/3 eh trabalho)
- **Referencia**: Gollin (2002, JPE), PWT 10.01

### THETA — Distribuicao de horas formais
- **Valores**: {36h: 0.085, 40h: 0.269, 44h: 0.646}
- **Fonte**: DIEESE Tabela 7 / PNAD Continua
- **Mapeamento**: <=39h -> 36h bin, 40h -> 40h bin, >=41h -> 44h bin

### ETA_I — Eficiencia relativa do trabalho informal
- **Valor**: 0.15 (revisao 2026-04-23)
- **Valor anterior**: 0.60 (retirado apos audit3)
- **Fonte**: La Porta & Shleifer (2014, JEP) — mediana de VAB/empregado informal / formal
- **Nota**: Representa a mediana cross-country de produtividade relativa informal/formal;
  substituiu o valor 0.60 (sem suporte direto em LPS ou Ulyssea) indicado no audit3.

### E_Q — Elasticidade produto-horas
- **Valor**: 0.60
- **Fonte**: Pencavel (2015, Economic Journal)
- **Significado**: Elasticidade de h*e(h) em relacao a h, avaliada em h_ref=42.24
- **Calibra**: kappa = (1-e_q) / (2*h_ref*(h_ref-h_star)) = 2.110e-03

### GAMMA_F — Custo de ajuste de formalizacao
- **Pequenas**: 0.12
- **Grandes**: 0.03
- **Fonte**: Legislacao CLT/FGTS + calibracao
- **Nota**: Custo MARGINAL efetivo, nao custo bruto total (~68-72%)

---

## 3. Parametros Calibrados

### kappa = 2.110e-03
- **Metodo**: Derivacao analitica de e_q
- **Formula**: kappa = (1 - 0.60) / (2 * 42.244 * 2.244)
- **Verificacao**: e(36)=0.9668, e(40)=1.0000, e(44)=0.9668
- **Match legado**: OK (legado: 2.111e-03, diferenca < 0.1%)

### tau_S (wedge pequenas) = 4.888
- **Metodo**: Bisecao
- **Target**: informalidade = 50%
- **Verificacao**: inf_actual = 50.03%

### tau_L (wedge grandes) = 0.007
- **Metodo**: Bisecao
- **Target**: informalidade = 20%
- **pi_m necessario**: 73.46 (para garantir wedge >= 0)
- **Verificacao**: inf_actual = 19.98%

### psi = 6.709e-05
- **Metodo**: FOC GHH
- **Formula**: psi = w_hourly / h_avg^nu = 0.1235 / 42.91^2
- **Inputs**: w_hourly = (1-alpha)*Y/(N*h), h_avg = 42.91

---

## 4. Resultados Principais (Reimplementados)

| Metrica | Valor | Match Legado |
|---------|-------|-------------|
| A_req (44->36h) | 8.42% | OK (8.42%) |
| dY | -8.66% | OK (-8.66%) |
| dInf | +0.81pp | OK (+0.81pp) |
| dY/h | +0.28% | OK (+0.28%) |
| dCV | -4.29% | Matches welfare_by_target_hours.csv |

### Resolucao da inconsistencia de dCV
- **Legacy consolidated_report.txt**: dCV = -0.77% (de run_paper.py)
- **Legacy welfare_by_target_hours.csv**: dCV = -4.29% (de recalibrado_br.py main)
- **Reimplementacao**: dCV = -4.29%
- **Causa**: `run_paper.py` usava referencia diferente para psi e consumo baseline
- **Conclusao**: -4.29% eh o valor correto. O consolidated_report.txt tinha um bug.

---

## 5. Pipeline de Reproducao

```
src/data_raw/collect_pnad.py  --> data_intermediate/pnad_targets.json
src/data_raw/collect_pwt.py   --> data_intermediate/pwt_targets.json
src/data_raw/collect_rais.py  --> data_intermediate/rais_targets.json
                                        |
src/data_clean/clean_and_merge.py       |
                                        v
                              data_final/calibration_targets.csv
                                        |
src/calibration/calibrate_all.py        |
                                        v
                              data_final/PARAMETER_MASTER_TABLE.csv
                              output/validation/calibration_results.json
```

Para reproduzir:
```bash
py -3 src/data_raw/collect_pnad.py
py -3 src/data_raw/collect_pwt.py
py -3 src/data_raw/collect_rais.py
py -3 src/data_clean/clean_and_merge.py
py -3 src/calibration/calibrate_all.py
```

---

## 6. Graus de Liberdade

| Item | Contagem |
|------|----------|
| Parametros calibrados internamente | 5 (kappa, tau_S, tau_L, pi_m_S/L, psi) |
| Parametros externos | 7 (alpha, eta_I, e_q, omega, sigma_sub, gamma_F_S, gamma_F_L) |
| Targets/momentos usados | 5 (inf_S, inf_L, e_q -> kappa, w_hourly -> psi, share -> N) |
| Graus de liberdade livres | 0 (sistema exatamente identificado) |

**Nota**: omega e sigma_sub sao atualmente tratados como externos/fixos.
Fase 3 tentara disciplinar sigma_sub empiricamente.

---

## 7. Revisao pos-audit3 (2026-04-23)

### Parametros alterados

| Parametro | Valor anterior | Valor novo | Justificativa |
|-----------|----------------|-----------|---------------|
| omega (peso CES formal) | 0.80 | 0.622 | 1 - informalidade narrow (PNAD 4T 2025, 0.378) |
| eta_I (eficiencia relativa informal) | 0.60 | 0.15 | La Porta & Shleifer (2014) mediana VAB/empregado |
| sigma_sub (central) | 0.60 | 1.15 | Mapeamento R->sigma re-derivado sob novos omega, eta_I |
| R interval MNR | [1.15, 1.40] | [1.15, 1.55] | Bound superior ampliado (conservador) |
| sigma_sub interval | [0.57, 0.64] | [1.065, 1.230] | R=[1.15,1.55] sob novos omega, eta_I |

### Resultados principais (novos)

| Metrica | Conservador (simetrico) | Preferido (flat-below) |
|---------|------------------------|------------------------|
| A_req central | 7.98% | 6.47% |
| A_req envelope (sigma, omega, eta_I) | [6.90%, 9.01%] | [5.59%, 7.29%] |
| dY | -7.84% | -6.45% |
| dCV | -3.31% | -1.50% |
| dInf | +1.27 pp | ~+1.0 pp |
| dY/h | +1.08% | +2.66% |

### SHA-256 snapshot pos-revisao (raw bytes)

| Arquivo | SHA-256 |
|---------|---------|
| data_intermediate/pnad_targets.json | `f3ef59b66835b72d4d17c58b233d2a945ac78e5fc13a5de062aaeba8670b6e95` |
| data_intermediate/pwt_targets.json  | `4627e31a2a367034c1e31e5d07a6d65f2bb43d9342b7b0f51610b389a2fa6da7` |
| data_intermediate/rais_targets.json | `fd9a1c44888f1fe03b2cc1252b48a2e0f3bbfe97663877d510fd574055f61747` |
| data_intermediate/sectoral_data.json | `d02107c626a857604ac3b690e252222426cd6c299c6d7d891825c0da3b59a0e3` |
| data_final/calibration_targets.csv | `2e1323df49129b0ab3f4fe91bb86ea6ddd40f0bc0ea01165e5df87ddde808e59` |
| data_final/PARAMETER_MASTER_TABLE.csv | `a29f41a93d7f4a46dfcf44066c212b5a85f2f21ecc07197fa9d5a7a38a400174` |
| data_final/SECTORAL_BASELINE_FACTS.csv | `b24e15bc879bc6b6a6aee81cf5c63c129071ad081ae272079f3de34d18da9a9f` |
| data_final/SECTORAL_PNAD_EMPIRICAL.csv | `5064e1101b215e7a269aaad738ca4108f0d3f8aa8da6d4421e3bd7366b69f4a9` |
| data_final/stress_test_results.json | `0318a1b3420300937a377dd8d2ccd0eaa6e85877f8518859d8e5ffa416aabcf1` |
| data_final/portugal_validation.json | `73586b4440d96351cbc44fb2a500f9d0af3585d487ea608c2462a56d4ee71f7a` |
| data_final/tfp_brazil_anchor.json | `6983b07038ad4eaf7c2c97e27651e534a6a28febcdc23e393edbcd5916a4c0c7` |

Hashes obtidos com `hashlib.sha256(open(f,'rb').read()).hexdigest()`.
Data: 2026-04-23.

### Nota sobre sectoral_data.json

A partir de audit3 (2026-04) o arquivo passou a usar a definicao **broad** de
informalidade (71.8% agri, 44.4% industria, 41.2% servicos), alinhada com
`data_final/SECTORAL_PNAD_EMPIRICAL.csv`. Ver
`data_intermediate/sectoral_data.README.md` para detalhes.

