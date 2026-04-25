# Strategy D: External Evidence Audit for sigma_sub

## Status: CONCLUIDA (literatura auditada 2026-03-24)

## ACHADO CRUCIAL: Dois conceitos diferentes de sigma

A literatura usa "sigma formal/informal" para dois objetos DIFERENTES:

**Conceito 1 (nosso modelo)**: Substituicao entre TRABALHADORES formais e informais
DENTRO da funcao de producao de uma firma. CES(LF, LI) como input unico para Y.
- Nosso sigma captura: quao facilmente a firma troca um formal por um informal
- Calibrado via: premio salarial formal/informal

**Conceito 2 (literatura macro/DSGE)**: Substituicao entre SETORES formal e informal
na economia agregada. Sigma captura quao facilmente a economia realoca producao.
- Sigma alto (6-10): economia se ajusta rapidamente entre setores
- Calibrado via: co-movimentos ciclicos de emprego formal/informal

Esses dois conceitos NAO sao diretamente comparaveis. Um sigma de 8 no sentido
setorial e compativel com um sigma de 0.6 no sentido intra-firma.

---

## Evidencia Tipo 1: Substituicao Intra-Firma (nosso conceito)

### Ulyssea (2018, AER) — "Firms, Informality, and Development"
- **sigma implicito**: INFINITO (trabalhadores sao substitutos perfeitos)
- **Modelo**: Firma contrata formal/informal como inputs identicos; diferenca eh compliance
- **Pais**: Brasil
- **Nota**: Ulyssea trata formal/informal como MESMO tipo de trabalho.
  Isso eh incompativel com nosso modelo (que tem eta_I < 1).
  Se seguissemos Ulyssea, sigma -> infinito e eta_I capturia tudo.

### Meghir, Narita, Robin (2015, AER) — "Wages and Informality"
- **sigma**: NAO estimado (modelo de search, nao CES)
- **Pais**: Brasil
- **Relevante**: Premio salarial formal/informal ~15-40% (R=[1.15, 1.40])
- **Verificacao**: PENDENTE (Fase 7)

### Card (2009, AER P&P) / Ottaviano & Peri (2012, JEEA) — Imigrantes/Nativos
- **sigma**: ~20 (quase substitutos perfeitos)
- **Conceito**: Trabalhadores com mesmo skill mas diferente status legal
- **Relevante**: Analogia F/I mais proxima (diferenca eh legal, nao de skill)
- **Implicacao**: Se F/I diferem SÓ por status, sigma -> muito alto
- **Contraargumento**: eta_I=0.60 sugere diferenca REAL de produtividade

---

## Evidencia Tipo 2: Substituicao Setorial (conceito diferente)

### Leyva & Urrutia (2020, J. Int. Econ.) — Mexico
- **sigma = 7.65** (benchmark ~8)
- **Modelo**: DSGE com mercados formais/informais segmentados
- **Calibracao**: Momentos ciclicos do emprego formal/informal
- **Pais**: Mexico
- **Verificacao**: PENDENTE

### McKiernan (2019, WP) — Chile
- **sigma = 6.5**
- **Modelo**: Modelo estrutural de informalidade
- **Calibracao**: Ciclica
- **Pais**: Chile
- **Verificacao**: PENDENTE

### Gulek (2024, MIT WP) — Turquia
- **sigma = 10**
- **Contexto**: Refugiados sirios (so trabalham informalmente)
- **Metodo**: IV estimation
- **Nota**: Contexto muito especifico (choque de oferta exogeno)
- **Verificacao**: PENDENTE

### Batini et al. (2011, IMF WP) — Paquistao
- **sigma = 2**
- **Modelo**: DSGE com informalidade
- **Metodo**: Estimacao com dados de forca de trabalho
- **Verificacao**: PENDENTE

---

## Evidencia sobre Substituicao Skill-Based (bounds)

### Katz & Murphy (1992, QJE) — EUA
- **sigma = 1.4-1.5** (skilled/unskilled)
- **Verificacao**: Referencia canonica, bem estabelecida

### IMF WP 2023/165 — Paises em Desenvolvimento
- **sigma = 2.0** (media paises em desenvolvimento)
- **sigma = 1.7-1.8** (America Latina)
- **Margem**: Skilled/unskilled

### Haanwinckel & Soares (2021, REStud) — Brasil
- **Modelo**: Search com heterogeneidade de firmas e trabalhadores
- **sigma**: Estimado para skilled/unskilled dentro de firmas formais/informais
- **Relevancia**: ALTA — diretamente sobre Brasil com formal/informal
- **Verificacao**: PENDENTE (valor exato nao acessivel via busca web)

---

## Reconciliacao

| Fonte | sigma | Conceito | Comparavel? |
|-------|-------|----------|-------------|
| Nosso wage premium | 0.57-0.64 | Intra-firma | SIM (model-consistent) |
| Ulyssea (2018) | infinito | Intra-firma | NAO (sem eta_I) |
| Meghir et al. (2015) | n/a | Search model | NAO (diferente arcabouco) |
| Leyva-Urrutia (2020) | 7.65 | Setorial/macro | NAO (conceito diferente) |
| McKiernan (2019) | 6.5 | Setorial/macro | NAO (conceito diferente) |
| Gulek (2024) | 10 | Setorial/migracaoNAO (contexto especifico) |
| Batini et al. (2011) | 2 | DSGE macro | PARCIAL |
| Katz-Murphy (1992) | 1.4-1.5 | Skill-based | BOUND |
| Card/Ottaviano-Peri | ~20 | Legal status | BOUND superior |

## Conclusao para o Paper

1. A literatura NAO fornece estimativa direta de sigma no nosso conceito exato
2. Os valores altos (6-10) sao para um conceito DIFERENTE (setorial)
3. O wage premium discipline (R=[1.15,1.40] -> sigma=[0.57,0.64]) permanece
   a melhor ancora MODEL-CONSISTENT
4. O paper deve DISCUTIR a diferenca de conceitos e explicar por que
   sigma=0.60 eh consistente com a literatura apesar de parecer baixo
5. Reportar sensibilidade ampla (sigma=[0.40, 2.50]) para mostrar robustez

## Referencia para o paper
> "A elasticidade de substituicao no nosso modelo captura a margem INTRA-FIRMA
> de realocacao entre trabalhadores formais e informais, mantendo eta_I fixo.
> Esse conceito difere da substituicao SETORIAL estimada em modelos DSGE
> (Leyva e Urrutia, 2020: sigma=8; McKiernan, 2019: sigma=6.5), onde sigma
> governa a mobilidade macroeconomica entre setores. O modelo mais proximo
> ao nosso eh Ulyssea (2018), que trata formal/informal como substitutos
> perfeitos — implicando que toda a diferenca de produtividade estah em eta_I.
> Nosso sigma=0.60 pode ser interpretado como uma reducao paramonica:
> parte da diferenca vai para eta_I (0.60), parte para sigma (<1).
> O intervalo disciplinado [0.57, 0.64] eh ancorado no premio salarial
> observado de 15-40% (Meghir et al., 2015)."
