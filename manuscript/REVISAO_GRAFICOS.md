> Registro histórico de uma etapa anterior. A versão atual adota 44h como referência principal, com dados e núcleo corrigidos. Consulte [REFERENCIA_44H.md](REFERENCIA_44H.md) para os números atuais; os valores abaixo documentam o estado então revisado.

# Restauração dos gráficos originais

Esta revisão recupera o desenho dos gráficos do manuscrito original, atualizando suas séries e anotações com a replicação corrigida. A referência visual é o material preservado em `PAPER_original_20260905_020616` e, para as figuras do apêndice, os arquivos originais arquivados com o pacote. O estado imediatamente anterior a esta restauração está em `PAPER_antes_restaurar_graficos_20260905_134322`.

| Local | Gráfico original → arquivo restaurado em `generated/` | Desenho preservado e atualização |
|---|---|---|
| Texto principal | `fig_areq_vs_hours_pt.pdf` → mesmo nome | Um painel com as duas curvas de produtividade requerida, cores e estilos originais, marcadores e anotações de 40h e 36h. Recupera o intervalo de 30h a 44h, recalculado a cada 0,25h, com marcadores em horas inteiras. |
| Texto principal | `fig_areq_vs_tfp_history_pt.pdf` → mesmo nome | Um painel histórico, linha roxa, referência pontilhada de 1990, faixa dourada da melhor década e tipografia serifada. Mantém a série PWT 11.0 verificada, 1954–2023, base 2021 = 1; a janela selecionada continua 2000–2010. |
| Texto principal | `fig_welfare_schedule_pt.pdf` → mesmo nome | Um painel com o bem-estar em função do teto e as duas funções de eficiência, de 30h a 44h. Atualiza as curvas na grade de 0,25h e identifica a métrica como variação percentual do composto GHH. |
| Texto principal | `fig_transition_map_pt.pdf` → mesmo nome | Mapa de calor de produtividade requerida por elasticidade e alívio da cunha no teto de 40h, preservando a composição visual original. O experimento passa a corresponder ao grupo nacional efetivamente calibrado. |
| Apêndice | `fig_sectoral_areq.pdf` → mesmo nome | Barras verticais agrupadas por agricultura, indústria e serviços; séries de 40h e 36h sob penalidade bilateral. Atualiza os momentos setoriais e preserva requisitos negativos quando ocorrem. |
| Apêndice | `slide10c_welfare_threshold.png` → `slide10c_welfare_threshold.pdf` e `.png` | Um painel de bem-estar no teto de 36h em função do ganho exógeno de PTF, com duas curvas e anotações dos limiares. Recalcula as alocações e corrige a identificação da métrica. |
| Apêndice | `fig_decomposition.pdf` → mesmo nome | Barras verticais agrupadas para horas físicas, eficiência, realocação e total no teto de 36h. Substitui as parcelas anteriores por diferenças entre níveis intermediários de produto com denominador comum. |

O gráfico adicional `fig_sensitivity_pt.pdf`, introduzido na revisão anterior, fica no apêndice. Ele conserva a comparação entre distribuição habitual completa, limitação prévia a 44h e ausência de fadiga, sem substituir nenhum dos quatro gráficos originais do texto principal. Os demais resultados nacionais e setoriais continuam nas tabelas.

As mudanças indispensáveis de interpretação são:

- **GHH e equivalente de consumo:** o antigo rótulo “ΔCV” nomeava a variação percentual do composto GHH. Os gráficos que preservam esse objeto agora usam “ΔGHH”. O equivalente de consumo permanece separado nas tabelas, com denominador `C0`; não se atribui incidência individual a essas curvas agregadas. Máximos anotados se referem à grade de 0,25h, não a uma jornada ótima de política pública.
- **Mapa de transição:** a calibração principal tem um grupo nacional. O alívio da cunha não pode continuar rotulado como intervenção exclusiva nas pequenas firmas. O mapa é um exercício condicional, sem estimar o efeito de um subsídio observado ou seu financiamento.
- **Distribuição inicial:** o cenário principal preserva todas as horas habituais observadas, inclusive acima de 44h. Os eixos e as legendas não descrevem essa base como contratos de 44h. A limitação inicial a 44h permanece uma sensibilidade explícita.
- **Requisito assinado:** valores negativos de `A_req` indicam produto acima da referência com a PTF inicial. Não são apagados nem convertidos em números positivos; a necessidade de ganho não negativo é zero nesses casos. A composição formal–informal continua reotimizada durante a busca por `A_req`.
- **PTF histórica:** a figura original efetivamente executada tinha somente o painel histórico. O segundo painel de barras da revisão anterior foi retirado. Os valores novos de compensação e suas anualizações pertencem às tabelas; não são misturados ao eixo de nível da PWT.

Os valores nacionais de referência usados nas anotações são os seguintes. Percentuais, salvo a informalidade, que é o nível após a reforma; arredondamento apenas para apresentação.

| Função e teto | ΔY (%) | A_req (%) | Informalidade (%) | ΔGHH (%) | CE (% de C0) |
|---|---:|---:|---:|---:|---:|
| Bilateral, 40h | −0,080 | 0,074 | 38,626 | 3,956 | 3,099 |
| Bilateral, 36h | −6,907 | 6,797 | 40,973 | −1,008 | −0,789 |
| Fadiga acima do pico, 40h | −0,078 | 0,072 | 38,625 | 3,958 | 3,100 |
| Fadiga acima do pico, 36h | −5,165 | 5,001 | 40,349 | 1,224 | 0,959 |

Com composição inicial congelada, `A_req` em 36h é 6,453% no bilateral e 4,749% na fadiga acima do pico. A sensibilidade de 40h permanece essencial: aproximadamente 0,07% na base completa, 1,53%–1,57% com limitação inicial a 44h e 4,32% sem fadiga.

Os quatro módulos novos, integrados por `scripts/generate_assets.py`, são `scripts/original_main_figures.py` (curvas de produtividade requerida e GHH), `scripts/original_transition_figure.py` (mapa de alívio da cunha), `scripts/original_tfp_figure.py` (painel PWT) e `scripts/original_appendix_figures.py` (setores, decomposição e limiar de bem-estar). Os dados centrais vêm da execução auditada `20260905_005724_846373`; curvas adicionais utilizam o mesmo núcleo corrigido.

Os códigos do modelo, os parâmetros centrais e os dados brutos não são alterados nesta etapa. A revisão trata da geração das figuras e de suas legendas e referências no manuscrito. Nenhum parâmetro é ajustado para recuperar os números antigos, e nenhum resultado antigo é reutilizado silenciosamente. A reprodução permanece `python build_paper.py`, executado dentro de `PAPER`.

## Execução e conferência final

O comando completo foi executado com sucesso. Foram recalculados 228 pontos das curvas, 1.364 cenários do mapa e 162 pontos do gráfico de limiar, além da busca contínua de neutralidade. A discrepância máxima das âncoras de 40h/36h é 7,11 × 10⁻¹⁵; o maior erro de restauração no mapa é 5,38 × 10⁻¹³. Os sete CSVs de resultados centrais, decomposição e PTF conferidos permanecem numericamente idênticos aos da versão anterior.

O limiar bilateral de neutralidade GHH em 36h é 0,77256894% de PTF; na fadiga só acima do pico o indicador já é positivo em zero. O mapa cobre A_req de −4,53245% a +0,08556% e, em sigma = 1,326 com alívio de 10%, resulta em −0,64343%. Esses valores são novos cálculos sob as hipóteses declaradas, não recuperação dos limiares ou cores numéricas antigos.

Foram inspecionadas individualmente as 24 páginas do artigo, as 20 do apêndice e as duas da folha de rosto, em renderizações Poppler de 1.400 pixels. Nenhuma referência indefinida ou caixa fora das margens. O contraste das anotações próximas de zero no mapa foi ajustado; após essa alteração, a página 19 foi reinspecionada e as outras 45 renderizações permaneceram idênticas. Fontes, margens e preâmbulo do artigo não foram modificados.

Também foram verificados todos os 252 arquivos dos quatro manifestos de preservação, incluindo os 82 arquivos da cópia imediatamente anterior. Os resultados estão em `VERIFICACAO_GRAFICOS.json`, `REVISAO_VISUAL.json`, `BUILD_MANIFEST.json` e `generated/ASSET_MANIFEST.json`.

Além dos quatro módulos gráficos e de `scripts/generate_assets.py`, foram alterados `build_paper.py` (seleção registrada de um Python científico já instalado e hashes dos módulos), `sections/results.tex`, `policy.tex`, `app_results.tex` e `app_model.tex` (figuras, referências, legendas e a breve discussão dos exercícios restaurados). A documentação foi sincronizada em `README.md`, `REVISAO_PAPER.md` e `FIDELIDADE_NARRATIVA.md`. As demais seções, resumos, bibliografia e entradas do modelo permaneceram preservados.
