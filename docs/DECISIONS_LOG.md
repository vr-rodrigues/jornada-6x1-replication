# DECISIONS_LOG.md

| # | Data | Decisão | Justificativa | Artefato |
|---|------|---------|---------------|----------|
| 1 | 2026-03-24 | Reimplementar todo o código do zero | Legado não é auditável; inconsistência de welfare detectada; sem testes | LEGACY_INVENTORY.md |
| 2 | 2026-03-24 | Manter identidade curto-prazo/margem informal do paper | Evitar descaracterização; diferencial genuíno vs literatura existente | PROJECT_CHARTER.md |
| 3 | 2026-03-24 | σ_sub baseline 0.80 será REAVALIADO após Fase 3 | Disciplinamento atual [0.57-0.64] contradiz baseline | PAPER_DIAGNOSTIC.md §3.1 |
| 4 | 2026-03-24 | Paper do professor será lido para framing, NÃO para imitação | Extrair apenas melhorias de posicionamento | PROJECT_CHARTER.md |
| 5 | 2026-03-24 | Placeholder "?" (nota 4) será resolvido ou removido | Risco de rejeição por referee | PAPER_DIAGNOSTIC.md §4.1 |
| 6 | 2026-03-24 | σ_sub baseline alterado de 0.80 para 0.60 | 0.80 implica prêmio salarial 1.895, fora do observado [1.15,1.40]. Intervalo disciplinado [0.57,0.64] via Strategies B/C/D. A_req cai de 8.42% para 7.26%. | SIGMA_SUB_DECISION_MEMO.md |
| 7 | 2026-03-24 | ΔCV inconsistência resolvida: -4.29% é o valor correto | run_paper.py usava referência diferente de ψ/c₀. Reimplementação confirma -4.29%. | DATA_PROVENANCE_BOOK.md §4 |
