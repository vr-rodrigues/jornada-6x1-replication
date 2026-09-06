# Referência de 44h: decisão e resultados atuais

Revisão de 5 de setembro de 2026. Preserva-se a pergunta do artigo original: a redução do teto de 44h para 40h ou 36h. Mantêm-se a narrativa geral e os sete desenhos originais dos gráficos, com dados, equações e números corrigidos. Os relatórios editoriais anteriores registram etapas históricas; este documento identifica a referência atual.

## Definição e motivo

No exercício principal, cada hora habitual formal inicial é `h0 = min(h_observada, 44)`, preservando seu peso PNAD. Horas inferiores a 44h permanecem na distribuição; não se supõe que todos trabalhem 44h. A jornada informal mantém a média observada. Para um novo teto H, aplica-se `h1 = min(h0, H)`.

O produto de referência é calculado nessa base, depois de recalibrar a ponte horária, as cunhas e a normalização de preferências. Em 44h, nada muda e A_req, variação do produto, informalidade, GHH e CE são exatamente zero. Isso decorre da identidade entre os estados comparados; não houve deslocamento gráfico, truncamento de A_req ou ajuste de parâmetros para recuperar resultados antigos.

A PNAD observa horas habituais, não horas contratadas. Há 17,97% dos formais acima de 44h. A limitação inicial é uma hipótese explícita de mensuração e exposição ao teto. A média formal observada é 41,4244h; a média transformada é 39,9466h. Não se apresenta a segunda como dado bruto.

Na alternativa com distribuição habitual integral, impor 44h já altera trabalho efetivo e produto; por isso pode resultar em A_req negativo. Esse resultado permanece nos dados de sensibilidade. As duas referências respondem a comparações diferentes, e a escolha de 44h deve acompanhar a interpretação do cenário principal.

## Calibração preservada e recalculada

Mantêm-se sigma=1,326, eficiência relativa informal=0,40, alpha=0,35, pico=40h e a âncora externa de eficiência. A razão horária da ponte passa de 1,622443 nos dados integrais para 1,682473 com o denominador de horas formais limitado a 44h, mantendo a renda. Os pesos tecnológicos recalibrados são 0,675651 (bilateral) e 0,676650 (fadiga acima do pico), distintos da participação formal.

A escolha formal–informal continua sendo reotimizada dentro de cada avaliação de A_req. A compensação com composição congelada continua reportada separadamente. A mudança de referência é uma mudança de hipótese do exercício, separada das correções numéricas e da atualização empírica. Os dados brutos, os códigos do núcleo e a execução auditada não foram alterados.

## Resultados nacionais

Produto, A_req, GHH e CE em porcentagem; informalidade em porcentagem do emprego. Decomposição em pontos percentuais de Y0, na ordem horas físicas, eficiência e realocação. Valores arredondados; CSVs guardam precisão completa.

| Função | Teto | Produto | A_req | A_req congelada | Informalidade | GHH | CE | Horas | Eficiência | Realocação |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bilateral | 40 | -1,6766 | 1,5726 | 1,4941 | 39,1520 | 0,2250 | 0,1762 | -2,2435 | 0,7714 | -0,2045 |
| Fadiga acima do pico | 40 | -1,6358 | 1,5338 | 1,4572 | 39,1384 | 0,2763 | 0,2164 | -2,1888 | 0,7525 | -0,1995 |
| Bilateral | 36 | -8,3976 | 8,3813 | 7,9555 | 41,5208 | -4,3659 | -3,4199 | -6,7070 | -0,6622 | -1,0284 |
| Fadiga acima do pico | 36 | -6,6462 | 6,5244 | 6,1945 | 40,8786 | -2,1210 | -1,6614 | -6,5397 | 0,7066 | -0,8131 |

A informalidade inicial é 38,6001%. Em 36h, a eficiência contribui negativamente na função bilateral, que penaliza horas abaixo do pico; na fadiga acima do pico, sua contribuição é positiva. O limiar de PTF que zera GHH em 36h é 3,39647% na bilateral e 1,62307% na fadiga; CE tem o mesmo limiar, com denominador distinto. Todos os valores de bem-estar acima são sem compensação de PTF.

Os resultados setoriais usam a mesma regra inicial, recalibrando a ponte após agregar folhas e horas dos três setores classificados. As compensações bilaterais em 36h são 8,8540% na agropecuária, 8,9691% na indústria/construção e 8,1616% nos serviços. O agregado resolve a restauração conjunta; não é média simples de requisitos setoriais.

## Arquivos e conclusões atualizados

- `scripts/paper_config.py`: referência editorial única e explícita.
- `scripts/baseline44_experiments.py`: 64 sensibilidades e 16 resultados setoriais calculados novamente com a referência de 44h; detalhes e proveniência em `generated/base44/`.
- `scripts/generate_assets.py` e módulos `original_main_figures.py`, `original_appendix_figures.py`, `original_transition_figure.py`: base coerente nos gráficos, tabelas e exportações, com teste de identidade em 44h. A série histórica de PTF permanece a mesma.
- `sections/abstract_*.tex`, `intro`, `facts`, `model`, `calibration`, `validation`, `results`, `policy` e `conclusion`: resultados, referência, calibração e discussão sincronizados, preservando encadeamento e desenhos originais.
- `sections/app_data.tex`, `app_model.tex`, `app_results.tex` e abertura de `online_appendix_pt.tex`: definição da transformação, ponte, decomposição, setores e sensibilidades sincronizados. O comando de reprodução no PDF usa caracteres literais copiáveis.
- `README.md`: comando, origem, organização e estado atual. `REVISAO_VISUAL.json` e `VERIFICACAO_BASE44.json`: verificação desta entrega.

As conclusões quantitativas agora são: 40h requer 1,53–1,57% de PTF; 36h requer 6,52–8,38%; CE sem compensação é positivo em 40h e negativo em 36h nas duas funções. A distribuição integral, na qual 40h requer aproximadamente 0,07%, permanece como sensibilidade visível inclusive no resumo. O mapa segue nacional, pois a ponte PNAD–RAIS não sustenta atribuição por porte; o bem-estar é representativo, sem incidência distributiva nem ajuste endógeno de capital.

## Reprodução e preservação

Na pasta do projeto: `python PAPER/build_paper.py`. Na pasta PAPER: `python build_paper.py`. O comando completo foi executado, recalculou os ativos e compilou os três PDFs. Uma compilação adicional com `--skip-assets` incorporou apenas ajustes finais de texto. Logs e manifesto do comando completo estão em `.build_paper/commands/` e `.build_paper/BUILD_MANIFEST_FULL_BASE44.json`; `BUILD_MANIFEST.json` registra a compilação final.

Os resultados nacionais principais coincidem com `national_empirical_topcode44` da execução `20260905_005724_846373`. O comparativo histórico permanece íntegro; exportações `_integral.csv` preservam a referência habitual integral. A nova computação de 80 cenários verifica restauração, composição congelada, KKT, decomposição, CE, GHH, recursos e ponte. O maior erro de restauração é 7,11e-15 e o de decomposição 1,78e-15 pontos percentuais. Isso verifica o cálculo, não identifica os parâmetros empiricamente.

O estado anterior desta revisão foi copiado em `../PAPER_antes_base44_20260905_143805`, com manifesto SHA256 de 97 arquivos. As quatro cópias históricas anteriores também foram mantidas. Os PDFs finais foram renderizados e todas as 47 páginas foram inspecionadas individualmente.
