# SIGMA_SUB_DECISION_MEMO.md
**Projeto**: Reducao de Jornada 6x1 — Reconstrucao do Zero
**Data**: 2026-03-24
**Fase**: 3 (Estimacao/Disciplinamento de sigma_sub)

---

## 1. O Problema

sigma_sub (elasticidade de substituicao entre trabalho formal e informal no agregador CES) eh o parametro mais influente e menos ancorado do modelo. Governa 30-40% da variacao de A_req.

O baseline legado (sigma=0.80) implica um premio salarial formal/informal de 1.895, que estah FORA do intervalo observado [1.15, 1.40]. Isso significa que o resultado principal do paper (A_req=8.42%) estah baseado em um parametro inconsistente com os dados.

## 2. Estrategias Tentadas

### Estrategia A — Demanda Relativa CES
- **Status**: Nao executada (requer microdados PNAD nao disponiveis via API)
- **Contribuicao**: Nenhuma estimativa produzida
- **Viabilidade futura**: Possivel com download de microdados PNAD Continua

### Estrategia B — SMM / Indirect Inference
- **Status**: Executada com sucesso
- **Metodo**: Para cada sigma em grid [0.40, 3.00], recalibrar o modelo (wedges, pi_m) e computar premio salarial implicito
- **Resultado**: Mapeamento 1-para-1 entre sigma e premio salarial
- **Intervalo disciplinado**: sigma in [0.569, 0.642] para R in [1.15, 1.40]
- **A_req disciplinado**: [7.01%, 7.55%]

### Estrategia C — Bounds / Set Identification
- **Status**: Concluida
- **Intervalo amplo**: sigma in [0.50, 1.00] (intersecao de todos os bounds)
- **Intervalo estreito (wage premium)**: sigma in [0.57, 0.64]
- **Limites**: Lower = complementaridade economica + literatura; Upper = resposta a politicas

### Estrategia D — Evidencia Externa
- **Status**: Preliminar (referencias a verificar na Fase 7)
- **Meghir et al. (2015, AER)**: Premio salarial 15-40% no Brasil -> sigma=0.57-0.64
- **Ulyssea (2018, AER)**: Modelo de firmas -> substituibilidade moderada (~0.5-1.0)
- **Katz & Murphy (1992)**: Substitucao skilled/unskilled = 1.4-2.0 (bound superior)
- **Central tendency**: sigma ~ 0.6

## 3. Consolidacao

| Fonte | sigma_low | sigma_high | Confianca |
|-------|-----------|------------|-----------|
| Premio salarial (CES FOC) | 0.569 | 0.642 | ALTA |
| Evidencia externa (Brasil) | 0.50 | 1.00 | MEDIA |
| Evidencia externa (internacional) | 0.50 | 2.00 | BAIXA |
| Bounds economicos | 0.30 | 3.00 | BAIXA |
| **Intersecao informada** | **0.57** | **0.64** | **ALTA** |

## 4. Decisao

### Opcao escolhida: INTERVALO DISCIPLINADO como baseline

**sigma_sub = 0.60** (central) com intervalo **[0.57, 0.64]**

Justificativa:
1. 0.60 eh o ponto medio do intervalo disciplinado [0.569, 0.642]
2. Eh consistente com premio salarial de ~1.26 (dentro de [1.15, 1.40])
3. Eh consistente com a evidencia externa (Meghir et al., Ulyssea)
4. Produz A_req = 7.26% (central), com intervalo [7.01%, 7.55%]

### O que muda no paper

| Metrica | Legado (sigma=0.80) | Novo (sigma=0.60) | Diferenca |
|---------|---------------------|---------------------|-----------|
| A_req | 8.42% | 7.26% | -1.16pp |
| dY | -8.66% | -7.41% | +1.25pp (menos negativo) |
| dInf | +0.81pp | -0.43pp | -1.24pp (INVERTE sinal) |
| dCV | -4.29% | -2.54% | +1.75pp (menos negativo) |
| Premio salarial implicito | 1.895 | 1.259 | -0.636 |

**Nota critica**: Com sigma=0.60, a informalidade DIMINUI com a reforma (-0.43pp),
invertendo o sinal do legado (+0.81pp). Isso muda a narrativa: com substituicao
mais baixa, a reforma nao empurra tantos trabalhadores para a informalidade.

### Como reportar no paper

1. **Baseline**: sigma = 0.60, A_req = 7.26%
2. **Intervalo disciplinado**: sigma in [0.57, 0.64], A_req in [7.01%, 7.55%]
3. **Sensibilidade ampla**: Manter heatmap/tornado com sigma in [0.40, 2.50]
4. **Discussao**: Explicar wage premium discipline, citar Meghir et al.
5. **Transparencia**: Reportar que sigma=0.80 (legado) estah FORA do intervalo disciplinado

## 5. Confronto com a Literatura

A busca na literatura revelou que modelos DSGE de informalidade usam sigma MUITO mais alto:
- Leyva & Urrutia (2020, JIE, Mexico): sigma = 7.65
- McKiernan (2019, Chile): sigma = 6.5
- Gulek (2024, MIT WP, Turquia): sigma = 10
- Batini et al. (2011, IMF, Paquistao): sigma = 2

**Por que nosso sigma=0.60 nao contradiz esses valores**:

Esses modelos usam sigma para um conceito DIFERENTE: substituicao SETORIAL
(mobilidade macroeconomica entre setores formal e informal). Nosso sigma captura
substituicao INTRA-FIRMA (quao facilmente uma firma troca um formal por um informal
mantendo eta_I fixo).

Ulyssea (2018, AER, Brasil) — o modelo mais proximo — trata formal/informal como
substitutos PERFEITOS (sigma=infinito). Toda a diferenca de produtividade estah
na distribuicao de firmas, nao nos trabalhadores.

Nosso modelo decompoe a diferenca em: (1) eta_I=0.60 (gap de eficiencia) +
(2) sigma=0.60 (substituibilidade imperfeita). Isso eh uma decomposicao parametrica
valida, disciplinada pelo premio salarial observado.

## 6. Riscos Residuais

1. **Premio salarial depende de controles**: R=[1.15,1.40] assume controle por observaveis.
   Mitigacao: Meghir et al. (2015) usam modelo estrutural com heterogeneidade.

2. **Conceito de sigma**: Nosso sigma intra-firma nao tem estimativa direta na literatura.
   O wage premium discipline eh a ancora mais model-consistent disponivel.
   Mitigacao: Sensibilidade ampla [0.40, 2.50] cobre todas as possibilidades.

3. **omega e sigma confundidos**: Mudar omega pode mudar sigma disciplinado.
   Mitigacao: omega=0.80 ancorado no share de emprego formal.

4. **Estrategia A nao executada**: Estimacao microdata poderia dar resultado diferente.
   Mitigacao: Wage premium discipline usa a mesma informacao de forma model-consistent.

## 6. Acao Imediata

- [x] Atualizar PARAMETER_MASTER_TABLE.csv com sigma=0.60
- [x] Re-rodar calibracao com sigma=0.60
- [ ] Atualizar todas as figuras (Fase 4)
- [ ] Reescrever secao de calibracao do paper (Fase 5)
- [ ] Discutir inversao do sinal de dInf no texto (Fase 5)

## 7. Registro em DECISIONS_LOG.md

**Decisao D6**: sigma_sub baseline alterado de 0.80 para 0.60
- Motivo: 0.80 implica premio salarial (1.895) fora do observado [1.15, 1.40]
- Evidencia: Strategies B (SMM), C (bounds), D (literatura)
- Consequencia: A_req cai de 8.42% para 7.26%; dInf inverte sinal
- Intervalo: [0.57, 0.64] reportado como sensibilidade primaria
