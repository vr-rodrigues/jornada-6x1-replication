# Prompt para LLMs especializados em deep research

Objetivo: encontrar uma reforma de jornada de trabalho no Brasil que sirva como experimento natural para análise causal, identificável em dados administrativos da RAIS (2003+). Copiar o bloco abaixo ("PROMPT") e colar em ChatGPT Deep Research / Perplexity / Gemini Pro Deep Research.

---

## PROMPT

```
Você é um assistente de pesquisa em direito do trabalho e economia do trabalho
no Brasil. Faça uma busca profunda na legislação federal, estadual, municipal
e em atos normativos regulatórios (portarias do MTE, resoluções de conselhos
profissionais, normas regulamentadoras) para identificar reformas que tenham
reduzido mandatoriamente a jornada semanal de trabalho de uma categoria
profissional identificável, entre 2003 e 2022, no Brasil.

## Contexto

Estou trabalhando em um paper estrutural que estima o efeito macroeconômico
da proposta brasileira de reduzir a jornada padrão de 44 para 36 horas
semanais (PEC 8/2025, "reforma 6x1"). O paper já tem modelo estrutural
calibrado e citações a evidência internacional (Asai-Lopes-Tondini 2025
sobre Portugal 1996; Hunt 1996 sobre Alemanha; Gonzaga-Menezes-Camargo 2003
sobre Brasil 1988, 48→44h).

Preciso encontrar um experimento natural BRASILEIRO para fazer uma
estimativa causal reduced-form. Já investiguei e DESCARTEI os seguintes
candidatos:

1. NR-17 Anexo II (Portaria MTE 09/2007): redução para 36h para operadores
   de telemarketing. Dados RAIS mostram que 75% do setor JÁ estava a 36h
   pré-reforma (via CCTs). Efeito agregado pequeno, sinal limpo só em
   subconjunto reduzido. Exploratório viável mas com narrativa de
   "codificação de prática", não de choque.

2. Reforma de enfermagem: não há lei federal clara de redução de jornada.
   Lei 14.434/2022 (piso salarial) NÃO incluiu cláusula de 30h. Variação
   estadual/municipal existe mas é fragmentada.

3. Reformas antigas (pré-2003): Lei 8.856/1994 (fisioterapeutas 30h),
   Lei 7.394/1985 (radiologistas 24h), Decreto-Lei 972/1969 (jornalistas
   5h), Lei 3.999/1961 (médicos 4h). Fora da janela de cobertura dos
   microdados RAIS pseudonimizados do Base dos Dados (que começam com
   qualidade em 2003).

4. Lei do Piso da Educação (Lei 11.738/2008): reserva 1/3 para atividades
   extraclasse mas NÃO reduz jornada total. Não é redução de jornada.

5. Lei do Motorista Profissional (Lei 12.619/2012, Lei 13.103/2015):
   regulamenta tempo de direção e descanso, NÃO reduz jornada semanal.

6. Lei do Aeronauta (Lei 13.475/2017): em parte aumenta tetos de voo,
   não é redução.

7. PPE - Programa de Proteção ao Emprego (Lei 13.189/2015) e
   programas de MP COVID (936/2020): permitem redução voluntária
   temporária com compensação; não são reformas mandatórias permanentes.

## O que preciso encontrar

Idealmente, uma lei ou ato normativo que:

1. Reduziu a jornada semanal de trabalho de forma mandatória e permanente.
2. Afetou uma categoria profissional identificável (via CBO, CNAE,
   categoria funcional de servidor público, ou outro identificador
   rastreável na RAIS).
3. Teve data de vigência clara.
4. Aconteceu entre 2003 e 2022 (idealmente 2005-2018 para ter
   pré e pós-períodos com dados limpos).
5. NÃO está confundida por outros choques simultâneos para a
   mesma categoria (não foi acompanhada de corte de contribuições
   sociais, mudança tarifária, mudança estrutural de CBO etc.).

## Candidatos concretos sinalizados pelos dados RAIS

Meu scan de todos os CBOs grandes em 2003-2019 identificou estas
mudanças bruscas na distribuição de horas contratadas. Por favor investigue
o que as causou:

| CBO | Ano | Queda pct_44h | Queda mean_h | Hipótese a verificar |
|-----|-----|---------------|---------------|----------------------|
| 4241 | 2007 | −65.8 p.p. | −1.69h | CBO 4241 = "Caixas e bilheteiros (exceto banco)". Mudança administrativa ou reforma real? Possível Lei 11.603/2007 (descanso semanal comércio)? |
| 4241 | 2010 | −44.4 p.p. | −0.84h | Mesma CBO. Possível CCT nacional? |
| 2147 | 2013 | −61.7 p.p. | −2.59h | CBO 2147 = "Engenheiros eletricistas, eletrônicos e afins". Alguma regulamentação? |
| 3171 | 2018 | −20.3 p.p. | −5.80h | CBO 3171 = "Técnicos de desenvolvimento de sistemas e aplicações". Alguma reforma em TI? CCT nacional de TI? |
| 4222 | 2011-2014 | gradual −25 p.p. | gradual | CBO 4222 = "Operadores de centrais de atendimento". Spillover da NR-17? |
| 2233 | 2008 | −11.9 p.p. | −1.63h | CBO 2233 = "Profissionais de saúde". Alguma reforma específica? |
| 2346 | 2007 | — | −5.62h | CBO 2346 = "Professores do ensino fundamental". Lei 11.738/2008? (anterior?) |
| 3171 | 2018 | −20.3 p.p. | −5.80h | conferir CCT TI ou PL específico |

Para cada um desses candidatos, preciso saber:
- Qual foi o evento legal/regulatório que causou a mudança?
- Data exata de vigência?
- Escopo (quem era afetado, quem não era)?
- Existe variação geográfica (estado, município)?
- Há confundimento com outras reformas na mesma categoria na mesma janela?

## Formato da resposta

Para cada reforma candidata identificada, reporte:

1. **Nome e citação da lei/ato normativo** com número, data de publicação
   no Diário Oficial e link se possível.
2. **Categoria afetada**: descrição + código CBO + código CNAE (se aplicável).
3. **Detalhes do tratamento**: jornada antes, jornada depois, data de vigência,
   prazo de adaptação, exceções.
4. **Avaliação de "cleanness" causal**:
   - Simultaneidade com outras reformas? (sim/não + quais)
   - Corte de contribuições sociais? (sim/não)
   - Mudança de escopo administrativo (CBO/CNAE reclassificação)? (sim/não)
   - Existe variação regional aproveitável? (sim/não)
5. **Evidência empírica pré-existente**: existe paper, dissertação, estudo
   ou relatório técnico que já analisou o efeito?
6. **Grau de confiança** (ALTO/MÉDIO/BAIXO) de que esta é uma reforma
   real e causalmente identificável.

Organize em ordem de qualidade causal (melhores primeiro). Inclua pelo menos
10 candidatos se existirem. Se concluir que não existe nenhuma reforma
federal limpa no intervalo 2003-2022, diga isso explicitamente e proponha
variações estaduais ou municipais de leis de redução de jornada
(servidores públicos, professores, enfermeiros, etc.) com datas específicas.

## Regras

- NÃO invente leis, números de portaria ou DOIs. Se não tiver certeza,
  marque "VERIFICAR" e omita números não confirmados.
- Priorize fontes primárias (Diário Oficial, Planalto, STF, TST).
- Inclua leis estaduais e municipais se forem mais limpas que as
  federais.
- Se encontrar paper acadêmico que analisou um desses eventos como
  experimento natural, cite.
- Se a reforma foi aplicada apenas a servidores públicos de um ente
  federativo, diga isso — ainda é útil, mas muda o desenho.
```

---

## O que fazer com a resposta

Quando a resposta voltar:
1. Validar cada lei citada contra os dados RAIS (rodar event-study preliminar na CBO afetada).
2. Escolher a reforma com melhor qualidade causal.
3. Construir o painel agregado correspondente.
4. Rodar o DiD / event-study cell-level.

Ver scripts em `src/nr17_study/` para os diagnósticos já executados:
- `01_diagnose_sizes.py` — contagens por CBO-ano.
- `02_hours_distribution.py` — distribuição de horas em CBOs candidatas.
- `03_explore_nursing.py` — trajetórias em CBOs de enfermagem.
- `04_scan_all_cbos.py` — varredura de todos os CBOs em busca de breaks.
