# RISKS_AND_FAILURES.md
**Projeto**: Redução de Jornada 6x1 — Reconstrução do Zero
**Data de criação**: 2026-03-24
**Última atualização**: 2026-03-24

---

## 1. Riscos Identificados

### R1 — σ_sub Não Estimável
- **Probabilidade**: Média-Alta
- **Impacto**: Alto (parâmetro governa 30-40% do A_req)
- **Descrição**: Os dados disponíveis (PNAD, RAIS) podem não oferecer variação suficiente para estimar σ_sub com precisão. A estratégia A (demanda relativa CES) requer preços relativos formal/informal, que são mal medidos. A estratégia B (SMM) requer momentos informativos com poder de identificação.
- **Mitigação**: 4 estratégias paralelas (A–D). Se nenhuma produzir estimativa pontual, adotar intervalo disciplinado [0.57, 0.64] do prêmio salarial e reportar A_req como intervalo [7.0%, 7.6%].
- **Plano B**: Set identification (Estratégia C) + evidência externa auditada (Estratégia D).

### R2 — ΔCV Inconsistência Não Resolvida
- **Probabilidade**: Baixa (será resolvida na reimplementação)
- **Impacto**: Médio (credibilidade dos resultados de welfare)
- **Descrição**: `welfare_by_target_hours.csv` mostra ΔCV(36h)=-4.29%, enquanto `consolidated_report.txt` mostra -0.77%. Raiz provável: referências diferentes de ψ e c₀/h₀ nos dois scripts.
- **Mitigação**: Na Fase 4, implementar welfare com teste unitário que verifica consistência entre CSV e relatório.

### R3 — Referências Alucinadas no Paper Original
- **Probabilidade**: Alta (placeholder "?" já detectado)
- **Impacto**: Alto (rejeição imediata se referee detectar)
- **Descrição**: Footnote 4 contém "?" no lugar de referência. Outras referências podem ter DOIs incorretos ou não existir.
- **Mitigação**: Skill de verificação de referências. Cada referência será verificada via CrossRef/Google Scholar antes de entrar no manuscrito final.

### R4 — Modelo Parcial Rejeitado por Reviewer
- **Probabilidade**: Média
- **Impacto**: Médio (requer reframing, não reimplementação)
- **Descrição**: Reviewer pode argumentar que sem equilíbrio geral (capital, preços, fiscal), os resultados são incompletos. O paper do professor demonstra que GE produz resultados qualitativamente diferentes.
- **Mitigação**: Seção "Escopo do Modelo" com justificativa deliberada (não acidental). Argumento: margem formal-informal é de 1ª ordem e incompatível com agente representativo + trabalho homogêneo do DSGE.

### R5 — Dados PNAD/RAIS Indisponíveis ou Mudaram
- **Probabilidade**: Baixa
- **Impacto**: Médio (atraso na calibração)
- **Descrição**: APIs do SIDRA podem mudar, microdados podem exigir novo acesso.
- **Mitigação**: Scripts de coleta com fallback para dados já coletados. Hash e timestamp em cada arquivo.

### R6 — Calibração Não Reproduz Resultados do Legado
- **Probabilidade**: Média
- **Impacto**: Baixo (resultado esperado se legado tinha bugs)
- **Descrição**: Reimplementação limpa pode gerar A_req ≠ 8.42% do legado.
- **Mitigação**: Documentar divergências em MODEL_VALIDATION.md. Se resultados diferem, os novos são canônicos (desde que passem nos testes unitários).

### R7 — Sobreajuste na Calibração
- **Probabilidade**: Baixa
- **Impacto**: Médio
- **Descrição**: Com muitos parâmetros livres (κ, ω, ψ, τ_S, τ_L, π_m), modelo pode "caber" nos dados trivialmente.
- **Mitigação**: Documentar graus de liberdade vs targets. Cada parâmetro deve ser ancorado em UMA fonte independente. Teste de sensibilidade verifica que resultados não dependem de calibração fina.

---

## 2. Modos de Falha Documentados

### F1 — Legado: ΔCV Inconsistente
- **Status**: Detectado, não resolvido
- **Detecção**: Comparação `welfare_by_target_hours.csv` vs `consolidated_report.txt`
- **Valores**: -4.29% vs -0.77% para h=36
- **Causa provável**: `recalibrado_br.py` e `run_paper.py` usam referências diferentes para ψ (GHH) e consumo/horas baseline
- **Resolução planejada**: Fase 4, teste `test_welfare_consistency`

### F2 — Legado: σ_sub Fora do Intervalo Disciplinado
- **Status**: Detectado, decisão na Fase 3
- **Detecção**: Baseline σ=0.80 → prêmio implícito 1.895, fora de [1.15, 1.40]
- **Consequência**: A_req=8.42% pode estar superestimado (intervalo disciplinado: 7.0–7.6%)
- **Resolução planejada**: Fase 3, SIGMA_SUB_DECISION_MEMO.md

### F3 — Legado: Placeholder "?" na Footnote 4
- **Status**: Detectado
- **Detecção**: Leitura do PDF, página 8
- **Resolução planejada**: Fase 7, verificação de todas as referências

### F4 — Legado: Rótulo "fadiga" enganoso
- **Status**: Detectado, reframing planejado
- **Detecção**: PAPER_DIAGNOSTIC.md
- **Descrição**: e(h) captura curvatura de rendimentos decrescentes, não fadiga fisiológica. Rótulo leva reviewer a esperar evidência médica.
- **Resolução planejada**: Fase 5, trocar rótulo para "canal de eficiência" ou "rendimentos decrescentes de horas"

---

## 3. Registro de Falhas Durante Execução

| Data | Fase | Falha | Causa | Ação | Status |
|------|------|-------|-------|------|--------|
| 2026-03-24 | 1 | ΔCV inconsistente | Referências diferentes de ψ/c₀ | Documentar; resolver na Fase 4 | **RESOLVIDO** (Fase 2) |
| 2026-03-24 | 1 | σ_sub fora do intervalo | Baseline arbitrário | Documentar; resolver na Fase 3 | Aberto |
| 2026-03-24 | 1 | Placeholder "?" | Referência não encontrada | Documentar; resolver na Fase 7 | Aberto |
| 2026-03-24 | 2 | ΔCV=-4.29% confirmado | run_paper.py tinha bug na ref. de psi/c₀ | -4.29% é o valor correto | **RESOLVIDO** |

---

## 4. Princípios de Gestão de Risco

1. **Falha precoce > falha tardia**: Detectar problemas na Fase 2-3, não na 6-7
2. **Documentar tudo**: Cada falha é registrada aqui com data, causa e ação
3. **Nunca mascarar**: Se o modelo produz resultado diferente do legado, reportar ambos
4. **Transparência paramétrica**: Cada parâmetro tem provenance documentada
5. **Anti-hallucination**: Nenhuma referência entra sem verificação; nenhum dado sem fonte
