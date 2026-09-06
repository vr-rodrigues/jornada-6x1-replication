> Registro histórico de uma etapa anterior. A versão atual adota 44h como referência principal, com dados e núcleo corrigidos. Consulte [REFERENCIA_44H.md](REFERENCIA_44H.md) para os números atuais; os valores abaixo documentam o estado então revisado.

# Revisão do artigo e do apêndice

Atualização posterior à segunda revisão textual: os desenhos originais dos gráficos foram restaurados, conforme `REVISAO_GRAFICOS.md`. O artigo tem agora 24 páginas e o apêndice, 20. As contagens de 23/19 páginas abaixo registram a etapa textual anterior; a verificação da etapa gráfica está em `VERIFICACAO_GRAFICOS.json` e `REVISAO_VISUAL.json`.

Revisão de 5 de setembro de 2026, aplicada à pasta `PAPER` indicada pelo autor. A cópia integral prévia está em `../PAPER_original_20260905_020616`, com `MANIFEST_SHA256.json`; o apontador `../PAPER_BACKUP_ATUAL.txt` registra sua localização. A versão anterior do manuscrito, as figuras e a folha de rosto foram preservadas antes das alterações.

## Reaproximação da narrativa ao original

Após orientação do autor, o principal recuperou a estrutura, a sequência dos argumentos e numerosas passagens do original. A comparação econômica de 40h e 36h, a literatura brasileira, o histórico de PTF e a discussão de desenho da reforma voltaram a conduzir o texto. Os detalhes de auditoria ficam principalmente no apêndice. `FIDELIDADE_NARRATIVA.md` registra o que foi recuperado e as alterações indispensáveis. A primeira revisão, mais ampla, também está preservada em `../PAPER_revisao_ampla_20260905_024411`. Esta etapa não alterou parâmetros, resultados, figuras ou valores de tabelas.

## Resultados que mudaram

O caso principal passa a usar a distribuição completa de horas **habituais** formais da PNAD 2024T4, um grupo Brasil, informalidade de 38,600087% e peso tecnológico CES calibrado à razão agregada de remuneração por hora. A elasticidade CES permanece em 1,326. O estado inicial preserva as horas observadas, inclusive acima de 44; aplicar um teto é uma hipótese de intervenção sobre essas horas e não uma observação da jornada contratual.

| Objeto | Texto anterior | Texto revisado e qualificação |
|---|---|---|
| PTF requerida em 40h | Cerca de 2% | 0,072–0,074% com base habitual integral e fadiga; 1,534–1,573% com base limitada a 44; 4,316% sem fadiga |
| PTF requerida em 36h | 6,63–8,18% | 5,001–6,797% na base habitual integral; 6,524–8,381% com base limitada a 44; 9,423% sem fadiga |
| Perda de produto em 36h | 6,60–8,02% | 5,165–6,907% na base principal |
| Aumento da informalidade em 36h | 1,57–1,92 p.p. | 1,749–2,373 p.p.; nível final 40,349–40,973% |
| Bem-estar em 36h | GHH negativo em ambas e denominado CV | GHH: −1,008% bilateral e +1,224% acima do pico; CE: −0,789% e +0,959%, respectivamente |
| Compensação com composição congelada em 36h | Não destacada | 6,453% bilateral e 4,749% acima do pico |
| Decomposição bilateral em 36h | Parcelas sem níveis/denominador comum | Horas −7,486 p.p.; eficiência +1,424; realocação −0,845; soma −6,907% |
| Informalidade PNAD | 37,8% restrita / 44,2% ampla | 38,6001% com V4019; o uso de V4017 gera 44,1741% por erro de variável |
| RAIS pequenas | 59%, com subcategorias somando 32% | 39,3886% dos vínculos em estabelecimentos de 1–49 empregados em 31/12/2022; não são pessoas ou empresas consolidadas |

As diferenças entre o texto anterior e o novo principal incluem mudanças de dados **e** de representação. Não foram atribuídas apenas à correção numérica. As tabelas comparativas do apêndice preservam execução original, código corrigido com entradas congeladas e versões empíricas intermediárias. Com entradas congeladas, a correção deixa o requisito bilateral de 36h próximo de 8,18%, enquanto corrige a informalidade inicial e o bem-estar. Não houve ajuste de parâmetros para recuperar resultados antigos.

## Alterações substantivas

1. **Dados e universo.** CNPJ usa V4019, com categorias, ausentes, peso V1028, universo e versão documentados. Horas habituais, efetivas e contratadas são distinguidas. O uso da fonte oficial alternativa após o bloqueio do BigQuery está declarado. Os antigos pesos atribuídos ao DIEESE permanecem hipóteses legadas. A RAIS não é indevidamente combinada com pessoas da PNAD para identificar grupos por empresa.
2. **Núcleo e derivações.** A escolha formal–informal é contínua, com o custo de oportunidade do trabalho informal na FOC, sinal correto do termo convexo e condições nas fronteiras. Um momento de informalidade identifica apenas uma combinação das cunhas; a separação usa normalização não negativa com `tau*pi=0`. A reotimização dentro da busca de A_req é preservada, como já existia; a compensação com composição congelada aparece separadamente.
3. **Ponte de remuneração.** A elasticidade 1,326 é fixada, não apresentada como estimativa identificada por MNR. O peso tecnológico não é igual à participação formal. A ponte agrega folhas e horas depois de calcular produtos marginais por grupo. Razões horária, semanal e por trabalho efetivo são objetos distintos; rendimentos de autônomos incluem renda mista e o universo remunerado difere de todos os ocupados.
4. **Decomposição e bem-estar.** A decomposição usa níveis intermediários e o produto inicial em todas as parcelas. O texto distingue variação GHH de CE, com consumo por trabalhador e restrição agregada de recursos explícita. No principal, cunhas são transferências e ajuste consome recursos. As horas médias não determinam utilidades individuais.
5. **Sensibilidade e identificação.** Foram incorporados ausência de fadiga, pico, curvatura, parâmetros CES, tratamento da cauda das horas e pontos interiores. As grades não são chamadas conjuntos identificados. Reproduzir momentos de horas introduzidos como entradas não é validação comportamental; a razão semanal compartilha informação com a ponte horária.
6. **Conclusões retiradas.** Não se mantém recomendação de calendário gradual ou de teto ótimo como resultado dinâmico; a curva é estática. Foram retiradas incidências individuais sem contas de rendimento e consumo, redução de A_req por ajuste endógeno de capital sem investimento e o mapa de subsídios às pequenas firmas sem identificação das cunhas/financiamento. A diferença entre escalas de dias, a horas semanais constantes, não é modelada.
7. **Referências.** Foram adicionadas referências verificadas dos microdados, dicionário, tabela e nota técnica da RAIS. As referências de PWT/FRED registram a consulta atual e a versão. Cacciatore (2016) saiu da afirmação sobre redução de jornada, pois examina outras reformas; seu DOI foi corrigido para `10.1016/j.jedc.2016.03.008`.

## Arquivos e figuras

`main.tex` foi dividido em seções editáveis. Os resumos em português e inglês passaram a ser compartilhados com `folha_rosto.tex`. `online_appendix_pt.tex` foi reconstruído com inputs presentes, título consistente, anonimização e referências corretas ao artigo. A bibliografia adicional está em `bibliography_verified.bib`.

Todas as figuras atuais estão em `generated/` e são regeneradas por `scripts/generate_assets.py`:

- Curva de A_req: um painel, duas funções, base habitual integral, cores e intervalo originais de 30h a 44h; requisitos negativos preservados.
- Bem-estar: um painel GHH por teto, com o rótulo da métrica corrigido. CE permanece nas tabelas. O limiar GHH versus PTF em 36h voltou ao apêndice, recalculado com composição reotimizada.
- Mapa: desenho original, agora com alívio da cunha nacional e A_req assinado. Não quantifica subsídio identificado ou intervenção por porte.
- Sensibilidade: figura adicional no apêndice, com fadiga e representação das horas; não substitui mais o mapa.
- Histórico de PTF: um painel com a série PWT 11.0, referência de 1990 e faixa da melhor década inteiramente contida em 1990–2019. Taxas e anualizações ficam nas tabelas.
- Setorial: barras verticais originais para agricultura, indústria e serviços, 40h/36h sob penalidade bilateral, com compensação assinada e dados novos.
- Decomposição: barras agrupadas originais em 36h, nas duas funções, para horas físicas, eficiência, realocação e total, em pontos percentuais do produto inicial.

Os quatro gráficos antigos permanecem em `legacy_assets/` e na cópia integral prévia. Não entram na compilação.

## Reprodução e verificações

O comando único nesta pasta é `python build_paper.py`. Ele usa a execução econômica fixada `20260905_005724_846373`, verifica integridade dos resultados e códigos, regenera os ativos e compila os três PDFs. Os arquivos de manifesto e logs registram versões, comandos e verificações, sem depender de PDFs antigos para declarar sucesso.

Na etapa gráfica foram recalculados 228 pontos das curvas, 1.364 cenários do mapa e 162 pontos de GHH versus PTF, além da busca contínua do limiar. Os pontos de 40h e 36h coincidem com a execução auditada à precisão numérica. A execução econômica de origem passou 61 testes e sua auditoria verificou restauração, otimização, decomposição e CE. Essa evidência certifica implementação e contabilidade, não identificação empírica.

`BUILD_MANIFEST.json` registra as checagens da compilação final. A inspeção visual das páginas e figuras é registrada em `REVISAO_VISUAL.json`. Os dados brutos e os resultados canônicos da replicação permaneceram intactos. A revisão não foi publicada no repositório remoto.

Verificação final da segunda revisão: artigo com 23 páginas, apêndice com 19 e folha de rosto com 2. As 25 páginas do artigo e da folha de rosto foram novamente inspecionadas; as 19 renderizações do apêndice coincidem integralmente com as páginas antes inspecionadas. Nenhuma referência indefinida ou caixa excedendo as margens. Links do apêndice para `main.pdf` verificados. A tabela de níveis intermediários usa diretamente os quatro níveis salvos no JSON canônico e tem CSV de precisão integral. Os dez arquivos da cópia original e os 79 arquivos do manifesto da primeira revisão passaram a conferência SHA256. Os ativos numéricos gerados também coincidem com a revisão anterior. O contexto legislativo foi datado em 2025–abril de 2026, com a fonte oficial do PL 1838/2026; a referência de Asai, Lopes e Tondini foi corrigida para a versão impressa de 11 de janeiro de 2024.

A segunda revisão recuperou mais redação original e retirou explicações repetidas. Equações, dados e resultados corrigidos foram preservados. A mudança de 27 para 23 páginas decorre de redução de texto, sem alteração de fontes, margens ou espaçamento. A conclusão sobre a concentração da perda agregada no setor de serviços foi restabelecida após cálculo dos níveis setoriais (65,28%–65,91% em 36h). Ver `FIDELIDADE_NARRATIVA.md` e `VERIFICACAO_SEGUNDA_REVISAO.json`.
