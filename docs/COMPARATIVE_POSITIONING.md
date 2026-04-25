# COMPARATIVE_POSITIONING.md
**Projeto**: Redução de Jornada 6x1 — Reconstrução do Zero
**Data**: 2026-03-24
**Papers comparados**:
- **Meu paper**: "Quanto de produtividade precisamos para reduzir a jornada de trabalho? Um stress test estrutural para o Brasil" — Victor Rangel, Insper (35 pp, 30 refs, 9 figuras, 2 tabelas)
- **Paper do professor**: "Redução da jornada (6x1) com trabalho indivisível" — Celso Costa-Junior (13 pp, ~10 refs, 2 tabelas)

---

## 1. O Que o Paper do Professor Faz

### Modelo
- **DSGE New Keynesian** com trabalho indivisível (Hansen 1985/Rogerson)
- Economia fechada, agente representativo
- Calvo pricing (rigidez nominal de preços)
- Regra de Taylor (política monetária)
- Autoridade fiscal (impostos sobre consumo, renda do trabalho, capital)
- Função de produção Cobb-Douglas com 1 tipo de trabalho homogêneo
- Firma de bens finais + firmas de bens intermediários (Dixit-Stiglitz)
- Reforma = redução permanente de H_o (horas por shift) de 44/91 para 36/91

### Resultados Principais
- Reforma 44→36: PIB cai ~3,7% no curto prazo, ~4,3% em 20 períodos
- Emprego (horas totais) cai ~7,8% a ~11,1%
- Salários reais sobem ~1% a ~2,9%
- Work-sharing ocorre mas é incompleto — margem extensiva NÃO compensa totalmente
- Ganho de produtividade (+2%) mitiga mas não reverte as perdas
- Reforma 44→40: efeitos menores (~metade)

### O que NÃO faz
- **NÃO modela setor informal** (reconhece explicitamente: "além de possíveis ajustes do setor informal que não são modelados nesta versão")
- **NÃO tem heterogeneidade por porte** (menciona conceitualmente α_S < α_L mas não implementa)
- **NÃO tem calibração explícita** (parâmetros mencionados nas equações mas sem tabela de valores)
- **NÃO faz welfare** (utilidade está no modelo mas não reporta medida de bem-estar)
- **NÃO faz sensibilidade paramétrica**
- **NÃO tem bibliografia formal** (10 referências inline, sem seção de referências)

---

## 2. O Que o Paper do Professor Faz MELHOR

| Aspecto | Professor | Meu Paper | Veredicto |
|---------|-----------|-----------|-----------|
| Equilíbrio geral | ✓ Feedbacks: preços, investimento, consumo, fiscal, monetário | ✗ Equilíbrio parcial, capital fixo | **Professor melhor** para capturar efeitos de segunda ordem |
| Acumulação de capital | ✓ Investimento endógeno, transição de capital | ✗ Capital predeterminado | **Professor melhor** para horizonte >1 ano |
| Dinâmica de transição | ✓ Caminho completo (20 períodos), overshooting, convergência | ✓ Dinâmica parcial (24 períodos) mas sem investimento | **Professor melhor** — mais credível |
| Política monetária | ✓ Regra de Taylor, resposta à inflação/produto | ✗ Sem preços nominais | **Professor melhor** se rigidez nominal importa |
| Política fiscal | ✓ Impostos endógenos, restrição orçamentária do governo | ✗ Sem governo | **Professor melhor** para repercussão fiscal |
| Margem extensiva (work-sharing) | ✓ Endógeno via Hansen-Rogerson — ξ_t emerge da otimização | ✗ Sem margem extensiva | **Professor melhor** em microfundamentação |

---

## 3. O Que MEU Paper Faz MELHOR

| Aspecto | Meu Paper | Professor | Veredicto |
|---------|-----------|-----------|-----------|
| **Margem formal–informal** | ✓ CES com formal/informal, η_I, wedges τ_g | ✗ Zero — setor informal ausente | **Meu paper MUITO melhor** — canal de 1ª ordem para Brasil |
| Heterogeneidade por porte | ✓ Pequenas vs grandes, calibrado com RAIS/CAGED | ✗ Apenas conceitual, não implementado | **Meu paper melhor** |
| Calibração transparente | ✓ Tabela 1 com 3 painéis, fontes, estratégia | ✗ Sem tabela, sem valores numéricos | **Meu paper MUITO melhor** |
| Welfare | ✓ ΔCV via GHH, welfare schedule, limiar de PTF | ✗ Nenhum | **Meu paper melhor** |
| Sensibilidade | ✓ Heatmap, frontier, tornado, heterogeneidade σ | ✗ Nenhuma | **Meu paper MUITO melhor** |
| Dados brasileiros | ✓ PNAD, RAIS/CAGED, PWT, DIEESE | ✗ Apenas H_o = 44/91 | **Meu paper melhor** |
| Métrica comunicável | ✓ A_req comparável com crescimento histórico da PTF | ✗ Variação cumulativa de Y, H, w | **Meu paper melhor** |
| Bibliografia | ✓ 30 referências (precisa auditoria) | ✗ ~10 referências, sem seção formal | **Meu paper melhor** |
| Evidência empírica (fadiga) | ✓ Pencavel, Collewet-Sauermann, Fan et al. | ✗ Nenhuma | **Meu paper melhor** |
| Decomposição de canais | ✓ Fadiga vs realocação | ✗ Nenhuma | **Meu paper melhor** |

---

## 4. O Que Vale Incorporar (Apenas Como Melhora de Framing)

### 4.1 INCORPORAR: Explicitação do que falta em GE
O paper do professor mostra que um DSGE captura feedbacks reais (investimento, preços, fiscal). Meu paper deve **reconhecer mais explicitamente** que esses canais estão ausentes e explicar por que isso é aceitável no curto prazo (1 ano). Não basta dizer "capital predeterminado" — precisa argumentar que investimento não se ajusta em 1 ano E que preços relativos são de segunda ordem para o mecanismo central (realocação formal–informal).

**Ação**: Reescrever seção de escopo do modelo (nova Seção 2.0 ou expandir introdução da Seção 2).

### 4.2 INCORPORAR: Menção à margem extensiva (work-sharing)
O Hansen-Rogerson mostra que firmas podem contratar mais trabalhadores com menos horas. Meu modelo fixa N_total, perdendo essa margem. A sensibilidade extensiva (ΔN = ±5%) é uma proxy, mas deveria ser melhor justificada. Mencionar o mecanismo Hansen-Rogerson como possível extensão.

**Ação**: Expandir limitações; adicionar discussão de por que N fixo é conservador (superestima A_req).

### 4.3 INCORPORAR: Framing de canais mais limpo
O professor organiza em: (i) margem extensiva, (ii) recomposição entre tipos de firma, (iii) repercussões macro-fiscais. Essa organização é mais limpa que minha decomposição "fadiga vs outros". Posso adotar um framing de 4 canais:

1. Canal de eficiência (fadiga/horas)
2. Canal de realocação formal–informal
3. Canal de heterogeneidade por porte
4. Canal de ajuste de quantidade (work-sharing) — ausente no modelo, discutido

**Ação**: Reestruturar Seção 3.1 com decomposição em canais nomeados.

---

## 5. O Que NÃO Deve Ser Incorporado

### 5.1 NÃO: Transformar em DSGE
Meu paper é deliberadamente estático/parcial. Isso é uma ESCOLHA, não uma limitação acidental:
- Transparência > complexidade para a pergunta de curto prazo
- O modelo responde "quanto de PTF" — não precisa de trajetória de capital
- A margem formal–informal é impossível de tratar com a mesma profundidade em um DSGE
- O DSGE do professor NÃO tem informal, NÃO tem porte, NÃO faz welfare — perda de escopo > ganho de GE

### 5.2 NÃO: Adicionar política monetária/fiscal
- Para 1 ano, política monetária é secundária vs realocação formal–informal
- Adicionar Taylor rule + Calvo obscureceria o mecanismo central sem ganho quantitativo

### 5.3 NÃO: Trabalho indivisível Hansen-Rogerson
- Trocaria a margem de formalidade (meu diferencial) por uma margem extensiva genérica
- Hansen-Rogerson assume trabalho homogêneo — exatamente o que meu paper supera

### 5.4 NÃO: Firmas representativas sem heterogeneidade
- Meu modelo com 2 grupos calibrados é superior a 1 firma representativa

---

## 6. Posicionamento Final

### Narrativa de posicionamento (para a introdução)
> "A literatura estrutural sobre redução de jornada opera em modelos de equilíbrio geral dinâmico que capturam feedbacks de preço, investimento e política monetária (e.g., Costa-Junior, 2026; Cacciatore et al., 2016; Eggertsson et al., 2014), mas tipicamente modelam trabalho homogêneo em uma economia sem setor informal. Esse arcabouço omite o canal quantitativamente mais relevante para economias em desenvolvimento com informalidade elevada: a realocação entre emprego formal e informal em resposta a restrições regulatórias. Nosso modelo adota deliberadamente uma estrutura estática de curto prazo — sacrificando feedbacks de equilíbrio geral em favor de uma modelagem explícita da margem de formalização com heterogeneidade por porte."

### Teste: "Isso fortalece a pergunta brasileira do meu paper ou apenas o aproxima do paper alheio?"

| Mudança proposta | Fortalece meu paper? | Aproxima do professor? | Decisão |
|-----------------|---------------------|----------------------|---------|
| Explicitar ausência de GE | ✓ Sim — torna a escolha deliberada | Não | **INCORPORAR** |
| Mencionar work-sharing | ✓ Sim — mostra consciência da margem | Levemente | **INCORPORAR** |
| Framing de canais | ✓ Sim — organiza melhor | Neutra | **INCORPORAR** |
| Virar DSGE | ✗ Perderia diferencial | ✓ Sim | **REJEITAR** |
| Adicionar Taylor rule | ✗ Sem ganho para a pergunta | ✓ Sim | **REJEITAR** |
| Hansen-Rogerson | ✗ Perderia margem informal | ✓ Sim | **REJEITAR** |

---

## 7. Resumo para o Paper

O paper do professor contribui com uma perspectiva de equilíbrio geral que captura feedbacks macroeconômicos ausentes do meu modelo. Em particular, a margem extensiva (work-sharing via Hansen-Rogerson) e a dinâmica de investimento são canais relevantes para horizontes mais longos.

Contudo, a ausência total da margem formal–informal é uma omissão de primeira ordem para o Brasil. Meu paper preenche exatamente essa lacuna, demonstrando que o canal de realocação formal–informal domina o canal de fadiga e governa o custo macroeconômico de curto prazo. A heterogeneidade por porte e a avaliação de welfare são contribuições adicionais que não existem no DSGE.

**O projeto NÃO virou um DSGE porque**:
1. A margem informal é incompatível com agente representativo + trabalho homogêneo
2. O ganho de GE (feedbacks de preço, investimento, monetário) é de segunda ordem para a pergunta de curto prazo
3. A transparência do modelo parcial é mais valiosa que a completude formal do DSGE para comunicação de política
