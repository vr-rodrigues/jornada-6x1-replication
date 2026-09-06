> Registro histórico de uma etapa anterior. A versão atual adota 44h como referência principal, com dados e núcleo corrigidos. Consulte [REFERENCIA_44H.md](REFERENCIA_44H.md) para os números atuais; os valores abaixo documentam o estado então revisado.

# Reaproximação ao texto original

Este documento registra as duas revisões textuais. A restauração posterior dos desenhos originais dos gráficos está documentada em `REVISAO_GRAFICOS.md`; essa etapa levou o artigo de 23 a 24 páginas e o apêndice de 19 a 20, preservando fontes, margens e a narrativa aqui recuperada.

A primeira revisão editorial alterou mais a redação e o foco do principal do que era necessário: a apresentação econômica cedeu espaço a uma exposição centrada na auditoria. Em atendimento à orientação do autor, a revisão atual recupera a sequência dos argumentos e formulações do original, atualizando os resultados e as interpretações que deles dependem.

## O que foi recuperado

| Parte | Elementos preservados ou recuperados do original |
|---|---|
| Resumos | Abertura sobre a PTF que neutraliza a perda de produto; modelo e dados; contraste 40h–36h; mecanismos; motivação para avaliar transição. Resumos português e inglês compartilhados com a folha de rosto. |
| Introdução | Problema brasileiro, pergunta de A_req, quatro ingredientes do modelo, três contribuições à literatura, comparação de tetos e fechamento de curto prazo. Várias passagens da literatura foram recuperadas integralmente. |
| Fatos | Ordem reforma e contrafactuais → horas, informalidade e produtividade; recuperação do contexto legislativo e da referência histórica de PTF. |
| Modelo | Ordem tecnologia e eficiência → formalização → produtividade requerida e bem-estar → fechamento. |
| Calibração | Ordem parâmetros e momentos → elasticidade formal–informal e disciplina empírica. |
| Checagens | Abertura sobre momentos não calibrados e comparação contextual com Portugal e Brasil em 1988. |
| Resultados | Ordem curva de produtividade → escala macroeconômica e mecanismos → bem-estar e heterogeneidade. Recuperados o contraste econômico entre 40h e 36h, a discussão de fadiga e trabalho efetivo e a comparação de PTF. |
| Implicações | Retomado o título “Implicações para o desenho da reforma”, a discussão de intensidade da reforma, produtividade histórica, informalidade, reorganização e caminhos faseados. |
| Conclusão | Retomada a estrutura de três parágrafos: produtividade requerida; distinção entre produto, compensação e consumo–lazer; limites e extensões. |

## Por que algumas passagens não podem voltar literalmente

- Os resultados principais usam a distribuição habitual completa da PNAD 2024T4. Uma redução do teto observado não equivale automaticamente a uma reforma contratual uniforme de 44 para 40 horas. A representação alternativa com base limitada a 44 permanece explícita.
- A informalidade inicial, o requisito de PTF e o diagnóstico de bem-estar mudaram. Em particular, o sinal de CE em 36 horas depende da eficiência; não cabe conservar a antiga conclusão de perda de bem-estar nas duas funções.
- Porte de estabelecimento na RAIS não identifica pessoas por empresa na PNAD. A extensão atual compara setores; não se mantém a afirmação de que pequenas firmas concentram o requisito.
- O modelo estático motiva avaliar transições graduais, mas não quantifica o benefício do calendário, de subsídios ou do ajuste endógeno de capital. A discussão desses temas foi preservada com essa delimitação.
- A condição de primeira ordem, a normalização das cunhas, o denominador comum da decomposição e a distinção entre GHH e CE precisam refletir os cálculos corretos.

O exemplo 59%/41%, os detalhes de V4017/V4019, a investigação RAIS, o histórico das versões e as verificações computacionais estão concentrados no apêndice e no relatório de correções. Essa revisão editorial não alterou parâmetros, simulações, figuras ou valores de tabelas para aproximar os resultados antigos.

## Preservação e reprodução

- Original: `../PAPER_original_20260905_020616`; os 10 arquivos foram conferidos contra seus hashes.
- Primeira revisão, mais ampla: `../PAPER_revisao_ampla_20260905_024411`; os 79 arquivos do manifesto foram conferidos.
- Versão atual: esta pasta `PAPER`.

Os apontadores externos são `PAPER_BACKUP_ATUAL.txt` e `PAPER_REVISAO_AMPLA_BACKUP.txt`. As três versões permitem comparação. `PRESERVACAO_ORIGINAL.json` registra as conferências.

Comando único desde esta pasta: `python build_paper.py`. Para esta alteração editorial foi executado `python build_paper.py --skip-assets`, com os ativos numéricos previamente gerados e verificados. `BUILD_MANIFEST.json` e `REVISAO_VISUAL.json` registram a compilação e a revisão visual atuais.

## Segunda revisão, 5 de setembro de 2026

A segunda passagem comparou novamente todas as seções com o original e concentrou as explicações técnicas que estavam repetidas. O principal passou de 27 para 23 páginas, mesma extensão do PDF original, sem alterar preâmbulo, margens, fontes ou espaçamento. Essa igualdade de páginas não é medida de identidade textual: permanecem as mudanças exigidas pelos dados e cálculos corrigidos.

- Modelo e calibração: redação mais próxima das aberturas originais; equações centrais preservadas; derivações de kappa e psi remetidas ao apêndice, onde já constavam integralmente.
- Fatos e checagens: recuperação da sequência original e concentração dos detalhes de mensuração em notas e no apêndice.
- Resultados: mantidos os quatro gráficos, tabelas e números essenciais; retiradas redefinições repetidas de A_req, CE/GHH e limites do modelo.
- Implicações e conclusão: retomadas passagens originais, com a discussão de 40h/36h, produtividade histórica, informalidade e transição; afirmações atualizadas onde o diagnóstico mudou.
- Recuperada a conclusão original de que serviços concentra a maior parte da perda agregada. Conferência dos níveis do exercício setorial com ponte recalibrada: 65,9087% no bilateral e 65,2843% na fadiga acima do pico, em 36h. O cálculo é (Y1_serviços - Y0_serviços) / soma_setores(Y1 - Y0), não a participação no emprego.

A versão imediatamente anterior foi arquivada em `../PAPER_antes_segunda_revisao_20260905_092422`, com 81 arquivos conferidos. O apontador está em `../PAPER_SEGUNDA_REVISAO_BACKUP.txt`. `VERIFICACAO_SEGUNDA_REVISAO.json` registra contagens da fonte, integridade e o cálculo setorial; `REVISAO_VISUAL.json` registra os PDFs atuais. Os 33 ativos gerados coincidem com os da versão anterior. Não foram alterados dados brutos, parâmetros ou simulações nesta passagem.
