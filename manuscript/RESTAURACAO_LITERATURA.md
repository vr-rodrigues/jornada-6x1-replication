# Restauração de contexto e literatura do original

Revisão de 5 de setembro de 2026, em atendimento ao pedido de desfazer cortes editoriais que não eram exigidos pelos novos resultados. A comparação usou o original `PAPER_original_20260905_020616` e a versão imediatamente anterior, preservada em `PAPER_antes_repor_literatura_20260905_152208`, com manifesto SHA256 de 116 arquivos. O ponteiro é `../PAPER_LITERATURA_BACKUP.txt`.

## Passagens recuperadas

| Arquivo | Recuperação |
|---|---|
| `sections/model.tex` | Frase original de Dix-Carneiro e coautores como microfundamentação relacionada de formalidade endógena. |
| `sections/calibration.tex` | Evidência de Derenoncourt e coautores sobre salário mínimo, salários informais e realocação; mantém a distinção entre essa resposta e a elasticidade CES. |
| `sections/policy.tex` | Caballero e a literatura de investimento como contexto para extensões dinâmicas; explicação de que a escala de produto dos serviços determina sua grande contribuição à perda agregada; ressalva de que a capacidade de trabalho em Fan e coautores é autorreportada e não é PTF agregada. |
| `sections/results.tex` | Frase original de que a curva GHH não implica oposição a reduções de jornada; fechamento da comparação histórica como régua de escala. |
| `sections/app_model.tex` | Discussão das diferentes elasticidades em Ottaviano–Peri, Bahar–Di Tella–Gülek, Leyva–Urrutia e McKiernan; motivação de Gollin para o tratamento da renda dos autônomos; enumeração dos canais macroeconômicos omitidos. |
| `bibliography_clean.bib` | Referências voltam às listas dos PDFs quando citadas. Corrigidos DOI de Dix-Carneiro, identificação de Caballero como capítulo e nota da versão revisada de Derenoncourt. |

A abertura e as três contribuições da introdução já estavam preservadas; não foram reescritas nesta passagem. As reposições usam a formulação original quando ela é compatível com o exercício atual. Nos demais casos, recuperam o contexto com a menor qualificação necessária: elasticidades entre origens, regimes e escolhas familiares não são o mesmo parâmetro; Gollin não estima alpha=0,35 para esta amostra; investimento não fornece ganho numérico de PTF sem uma extensão dinâmica.

A citação de Cacciatore não voltou à frase que o apresentava como evidência específica sobre redução da jornada. Continuam excluídas as inferências indevidas sobre identificação conjunta, incidência individual, porte de firma e benefícios numéricos do capital ou do calendário. Esses cortes corrigem o alcance das afirmações, enquanto a discussão econômica e bibliográfica pertinente foi recuperada.

## Fontes primárias conferidas

- [Dix-Carneiro et al., artigo publicado](https://doi.org/10.3982/ECTA19378): Econometrica 94(2), 573–618, 2026.
- [Derenoncourt et al., NBER 34445](https://www.nber.org/papers/w34445): publicação inicial em 2025, versão revisada em julho de 2026.
- [Caballero, Aggregate Investment](https://doi.org/10.1016/S1574-0048(99)10020-X): capítulo 12 do Handbook of Macroeconomics, 1999.
- [Fan et al., texto integral](https://par.nsf.gov/servlets/purl/10636509): a seção de variáveis mediadoras descreve capacidade de trabalho autorreportada.
- [Ottaviano e Peri](https://doi.org/10.1111/j.1542-4774.2011.01052.x), [página de autora de Bahar e coautores](https://economics.mit.edu/people/phd-students/isabel-di-tella), [Leyva e Urrutia](https://doi.org/10.1016/j.jinteco.2020.103340), [McKiernan](https://cdn.vanderbilt.edu/vu-my/wp-content/uploads/sites/2877/2020/08/05104611/SSReformInformality.pdf) e [Gollin](https://web.williams.edu/Economics/wp/Gollin_Getting_Income_Shares_Right_working_paper_with_figures.pdf): conferência dos objetos e mecanismos descritos no contexto recuperado.

## Verificação

Compilação editorial: `python PAPER/build_paper.py --skip-assets`. O comando completo de reprodução permanece `python PAPER/build_paper.py`.

Os 55 ativos gerados, inclusive oito pares PDF/PNG de figuras, CSVs, tabelas e parâmetros, permanecem idênticos à versão anterior, assim como o manifesto dos ativos. Os 32 blocos de equações e alinhamentos matemáticos foram comparados literalmente e permanecem iguais. Não houve nova calibração, mudança nos dados ou reexecução desnecessária das simulações.

Os PDFs têm 25 páginas no artigo, 23 no apêndice e 2 na folha de rosto. O acréscimo decorre do texto e das referências recuperados, com fontes e margens preservadas. As páginas alteradas foram renderizadas e inspecionadas individualmente; as demais coincidem com as renderizações já aprovadas. O controle local de linha viúva no apêndice mantém o parágrafo de compensação legível sem mudar seu conteúdo.

`VERIFICACAO_RESTAURACAO_LITERATURA.json` registra preservação e comparação dos arquivos. `BUILD_MANIFEST.json` e `REVISAO_VISUAL.json` identificam a compilação e a revisão visual vigentes. Os relatórios de base44 permanecem como registro da revisão numérica anterior.
