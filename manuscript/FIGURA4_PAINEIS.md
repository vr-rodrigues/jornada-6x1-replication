# Figura 4 — comparação das transições para 40h e 36h

Revisão de 5 de setembro de 2026, a pedido do autor. A Figura 4 mantém o mapa de calor e as isocurvas, agora com **44→40h no painel A, acima, e 44→36h no painel B, abaixo**. O nome apresentado ao leitor passa de “cunha formal” a **“custo de formalização”**, definido como o componente privado adicional por emprego formal, τ.

Os painéis usam os mesmos limites nos eixos e a mesma escala de cores. O eixo vertical mostra a redução percentual de τ, entre 0% e 100%; não uma alíquota observada nem um gasto fiscal identificado. A ampliação do limite anterior de 50% permite verificar o que ocorre mesmo com a eliminação desse componente. Os painéis representam alternativas a uma única base de 44h, e não etapas sucessivas de uma trajetória dinâmica.

## Resultados que sustentam a comparação

Mantêm-se a eficiência bilateral, os dados PNAD reprocessados, a base formal inicialmente limitada a 44h e o grupo nacional. Na calibração central, σ = 1,326:

| Redução do custo de formalização | PTF requerida em 40h | PTF requerida em 36h |
|---:|---:|---:|
| 0% | 1,573% | 8,381% |
| 10% | 0,845% | 7,606% |
| 20% | 0,205% | 6,923% |
| 50% | −1,180% | 5,437% |
| 100% | −1,934% | 4,621% |

Para preservar o produto sem ganho de PTF, **40h requer redução de 23,5296% nesse custo**. Com um ganho de PTF de 1%, a redução necessária cai a 7,7640%. Em **36h, mesmo reduzir esse componente em 100% deixa uma necessidade de 4,6211% de PTF**. Nessa calibração, portanto, o pacote para 36h precisa incluir ganhos de produtividade além da redução do custo de formalização. O exercício não identifica orçamento, financiamento, focalização por porte ou efeitos de instrumentos temporários.

O A_req é assinado: números negativos indicam que a combinação de teto e redução do custo já eleva o produto sob a PTF inicial. O CSV também fornece `A_req_nonnegative_pct = max(0, A_req_pct)` para quem precisa expressar somente o ganho adicional necessário. Isso não altera a referência inicial de 44h.

## Cálculo e verificações

- A grade contém 44 valores de σ entre 0,4 e 2,5, incluindo 1,326; 61 reduções de custo entre 0 e 100%; e dois tetos: **5.368 cenários**.
- Para cada σ, a ponte de remuneração **horária** determina ω no estado inicial. A normalização τ ≥ 0, π ≥ 0 e τπ = 0 determina os custos iniciais. Depois, somente τ muda: τ_cap = (1 − r)τ. Os parâmetros da ponte, π, capital, custo de ajuste e sua âncora permanecem fixos durante a intervenção; a razão salarial após a reforma pode mudar.
- O produto de referência e a composição inicial são idênticos entre os dois tetos e todas as reduções de custo, para cada σ. A escolha formal–informal é reotimizada em cada avaliação da raiz que restaura o produto.
- A compensação com composição congelada continua reportada: na calibração central, 1,4941% em 40h e 7,9555% em 36h. Como se trata de produto bruto, esse cálculo não muda com a redução do custo privado quando a composição fica congelada.
- Os custos τ e π seguem a convenção contábil canônica de transferências devolvidas à família; o ajuste de composição consome recursos. O mapa restaura produto bruto, não equivale a uma análise fiscal ou de bem-estar do pacote.
- Os limites de custo são resolvidos diretamente pela igualdade do produto, com verificação da primeira ordem, fronteiras e restauração. Os mínimos são conferidos pela composição que maximiza o produto CES e por otimização limitada na calibração central. Não se extrapola para τ negativo.
- Os 1.364 pontos antigos de 40h, com redução até 50%, reaparecem no novo mapa: a maior diferença numérica é de 1,42 × 10⁻¹⁴ ponto percentual. O cenário sem alívio coincide com os resultados nacionais de 40h e 36h já auditados. Nenhum parâmetro foi ajustado para induzir a comparação.
- A grade é uma análise de sensibilidade condicional. Não constitui um conjunto identificado de políticas ou parâmetros.

As verificações numéricas detalhadas são gravadas em `generated/transition_map_checks.json`. A integridade dos arquivos, a preservação dos resultados anteriores e as escalas comuns são registradas em `VERIFICACAO_FIGURA4_PAINEIS.json`. `REVISAO_VISUAL.json` registra a conferência da versão compilada.

## Arquivos e reprodução

Alterações desta etapa:

- `scripts/transition_experiments.py`: cálculo separado dos dois tetos, limites de compensação e verificações.
- `scripts/original_transition_figure.py`: desenho dos painéis A/B com eixos, cores e unidades comuns.
- `sections/policy.tex`: discussão, legenda e nota sincronizadas com os dois cenários.
- `main.tex`: controle de linhas isoladas nas referências, após a mudança de paginação causada pelo painel adicional.
- `README.md` e este registro: documentação atualizada.
- `generated/transition_map.csv`, `generated/transition_map_checks.json` e os arquivos da Figura 4: regenerados pelo comando abaixo, junto com os documentos e manifestos.

Na pasta que contém `PAPER` e `replication_package`:

```powershell
python PAPER/build_paper.py
```

O comando recalcula os gráficos e tabelas a partir das entradas auditadas, verifica os resultados e compila texto principal, apêndice e folha de rosto. A identificação do run permanece `20260905_005724_846373`. Os demais resultados, figuras e a restauração de literatura da etapa anterior são preservados. O texto-fonte do apêndice não requer alteração para esta mudança na Figura 4 do principal; suas referências são recompiladas.

A versão imediatamente anterior foi copiada para `../PAPER_antes_figura4_paineis_20260905_161318`, com 118 arquivos e manifesto SHA-256. Todas as cópias anteriores continuam preservadas. Registros anteriores sobre a Figura 4 de painel único documentam etapas históricas; este arquivo descreve a versão atual.
