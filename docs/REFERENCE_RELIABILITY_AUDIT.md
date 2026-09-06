# Reference Reliability Audit

Date: 2026-04-28

Auditor profile: independent reference auditor focused on reliability, provenance, traceability, and the distinction between peer-reviewed evidence, working papers, official data, and institutional/news sources.

Scope:

- `paper/tex/bibliography_clean.bib`
- Main paper and appendices in `paper/tex/*.tex`
- Data provenance files and final calibration targets where they identify bibliographic or data-source anchors
- Select web verification for recent official and working-paper sources

## Executive assessment

The reference base is mostly reliable. The core theory and empirical anchors rely heavily on peer-reviewed economics articles and standard official data sources. There is no immediate reference failure that would invalidate the manuscript.

The main reliability risk is not the published literature. It is provenance. Several central data inputs are described in text and final CSV/JSON files, but not always anchored with a complete bibliographic record, stable URL, extraction date, table ID, variable ID, and stored raw input. This matters because the paper is presented as a replication package and because the referee is likely to ask whether the Brazilian-data inputs can be independently reconstructed.

## Source classification

High reliability, peer-reviewed or handbook/book sources:

- Pencavel (2015), Economic Journal
- Hsieh and Klenow (2009), QJE
- Restuccia and Rogerson (2008), RED
- Ulyssea (2018), AER
- Meghir, Narita, and Robin (2015), AER
- La Porta and Shleifer (2014), JEP
- Greenwood, Hercowitz, and Huffman (1988), AER
- Cacciatore et al. (2016), JEDC
- Leyva and Urrutia (2020), JIE
- McKiernan (2021), RED
- Gollin (2002), JPE
- Feenstra, Inklaar, and Timmer (2015), AER
- Gonzaga, Menezes Filho, and Camargo (2003), Revista Brasileira de Economia
- Ottaviano and Peri (2012), JEEA
- Collewet and Sauermann (2017), Labour Economics
- Bick, Fuchs-Schundeln, and Lagakos (2018), AER
- Caballero (1999), Handbook of Macroeconomics
- Crepon and Kramarz (2002), JPE
- Chemin and Wasmer (2009), Journal of Labor Economics
- Lee and Lee (2016), Labour Economics
- Calmfors and Hoel (1988), Scandinavian Journal of Economics

Generally reliable but should be treated as working-paper evidence:

- Derenoncourt, Gerard, Lagos, and Montialoux (2025), NBER WP 34445
- Asai, Lopes, and Tondini (2024), Paris School of Economics working paper
- Bahar, Di Tella, and Gulek (2025), working paper
- Busso, Fazio, and Levy (2012), IDB working paper
- Hunt (1996), NBER WP, later published in QJE 1999
- Corbi, Ferraz, and Narita (2024), PUC-Rio discussion paper
- Schramm (2014), job market paper

Official data or institutional sources:

- IBGE/SIDRA PNAD Continua
- RAIS/CAGED, Ministerio do Trabalho
- Penn World Table 11.0, University of Groningen and UC Davis
- FRED series `RTFPNABRA632NRUG`
- Camara dos Deputados news pages for PEC 8/2025 and the 40h/6x1 legislative discussion
- DIEESE 2024

## P0 findings

None.

No cited reference is missing from `bibliography_clean.bib`, and no used source appears obviously fabricated from the local files and web checks.

## P1 findings

### P1.1 Data-source provenance is incomplete for central Brazilian inputs

Location:

- `paper/tex/online_appendix.tex`
- `paper/tex/sec_calibration.tex`
- `data_final/calibration_targets.csv`
- `docs/DATA_PROVENANCE.md`

PNAD/SIDRA, RAIS/CAGED, and DIEESE are central to the calibration, but their bibliographic treatment is uneven. `PNAD2025` and `DIEESE2024` exist in the `.bib`, yet they are not cited consistently in the paper text. RAIS/CAGED is used in text and provenance files but does not have a dedicated `.bib` entry.

Reliability implication:

Official data are reliable, but reproducibility depends on table IDs, variable IDs, extraction date, API URL or download URL, and a frozen raw/intermediate file. Without those, a referee can accept the source but still question whether the exact inputs are reconstructible.

Recommended fix:

- Add dedicated `.bib` entries for RAIS/CAGED and any specific SIDRA table family used.
- Cite `PNAD2025` and `DIEESE2024` where the inputs are first introduced.
- Add extraction dates for PNAD/SIDRA, FRED/PWT, and DIEESE.
- For each calibration target, point to a raw or frozen intermediate file when available.

### P1.2 DIEESE contracted-hours weights need a stronger audit trail

Location:

- `data_final/calibration_targets.csv`
- `paper/tex/sec_facts.tex`
- `paper/tex/main_pt.tex`

The contracted-hours weights are central: 0.085, 0.269, and 0.646. The local file maps them to "DIEESE Tabela 7 / PNAD Continua", but the report/source is not fully identified in the bibliography. A public web search found general DIEESE annual-report pages, but not a clean, stable source for exactly those bins.

Reliability implication:

This is a high-load calibration object. If the referee cannot trace it, they may treat the baseline hours distribution as author-imposed rather than source-based.

Recommended fix:

- Add the exact DIEESE report title, table number, publication URL, page number, and extraction/download date.
- Store the original PDF or extracted table if licensing permits.
- If the mapping is partly author-created, describe the mapping explicitly in the appendix and label it as a mapping from DIEESE categories, not a direct DIEESE statistic.

### P1.3 Legislative sources are reliable but should be described more narrowly

Location:

- `paper/tex/sec_introduction.tex`
- `paper/tex/main_pt.tex`
- `paper/tex/bibliography_clean.bib`

The Camara dos Deputados pages are reliable for legislative news and dates. Web verification confirmed:

- PEC 8/2025 protocol on 2025-02-25 and the 36h proposal.
- The 40h relator proposal on 2025-12-03.
- CCJ admissibility approval on 2026-04-22.
- Special commission creation on 2026-04-24, updated 2026-04-27.

Reliability implication:

The sources support the factual legislative chronology. The only risk is wording. "Official discussions included 40-hour, 5x2, and phased alternatives" can sound broader than the source. The 40h path is a relator/report proposal and should be described that way when precision matters.

Recommended fix:

- Use wording such as "the relator proposed" or "Camara coverage reported proposals including..." for the 40h/transition claims.
- Keep separate the formal PEC status from proposals in reports or subcommittee discussions.

### P1.4 The `sigma_sub` calibration rests on a valid but inferential bridge

Location:

- `paper/tex/sec_calibration.tex`
- `paper/tex/online_appendix.tex`

Meghir, Narita, and Robin (2015) is a strong peer-reviewed anchor. The risk is not the paper. The risk is the mapping from a formal-informal wage premium to an intra-firm CES substitution elasticity through the CES first-order condition.

Reliability implication:

This is a model interpretation layer, not a direct empirical estimate of `sigma_sub`. The appendix already states this. A skeptical referee may still want the assumption visible near the main calibration table.

Recommended fix:

- Keep the current footnote.
- In the main calibration table or surrounding text, state that the estimate is "wage-premium-disciplined" rather than directly estimated.
- Preserve the PNAD/SIDRA bridge as a descriptive diagnostic, not identifying evidence.

### P1.5 Some recent articles need final publication metadata checked

Location:

- `paper/tex/bibliography_clean.bib`

`DixCarneiroGoldbergMeghirUlyssea2026` appears to be final or forthcoming in Econometrica, but the `.bib` entry has no DOI. Web checks found the NBER WP and author-page evidence listing Econometrica, Vol. 94, Issue 2, March 2026, pp. 573-618. A final Wiley/Econometrica DOI should be added if available.

`LemosGalvao2020` is less secure. A search did not find a clean match for the exact title/authors. Since it supports the agricultural wedge comparison, it should be verified or replaced with a source that is easier to audit.

Recommended fix:

- Add DOI or final publisher URL for Dix-Carneiro et al. if available.
- Verify `LemosGalvao2020` manually. If not verifiable, replace the claim with official payroll-tax sources or a more visible peer-reviewed source.

## P2 findings

### P2.1 Bibliography contains unused entries

Several entries are in `bibliography_clean.bib` but are not cited in the compiled paper or appendix. This is not a reliability failure, but it weakens the sense of a clean final package.

Recommended fix:

- Run a citation-cleanup pass before submission.
- Keep unused references only if they are intentionally retained for future robustness discussion.

### P2.2 PWT/FRED is strong but revision-sensitive

The PWT/FRED anchor is reliable. Web verification confirmed that FRED lists `RTFPNABRA632NRUG` under Penn World Table 11.0, annual frequency, and `rtfpna` as the source ID. Groningen's PWT 11.0 page states that version 11.0 extends coverage through 2023.

Reliability implication:

The source is strong, but PWT data are revised across versions. The package already stores a local FRED CSV, which is good. The text should make the extraction date visible.

Recommended fix:

- Add extraction date to the FRED/PWT `.bib` entry and data provenance note.
- Keep the local CSV in `data_raw/fred/`.

### P2.3 Working papers should stay clearly qualified

`AsaiLopesTondini2024`, `DerenoncourtGerardLagosMontialoux2025`, and `BaharDiTellaGulek2025` are useful but not all are peer-reviewed. The current text mostly uses them as directional or contextual evidence, which is appropriate.

Recommended fix:

- Avoid using working papers as sole support for a central calibrated parameter.
- Use "directional benchmark", "working paper evidence", or "recent evidence" where needed.

### P2.4 The `h*=40` choice is plausible but not directly estimated

Pencavel (2015), Collewet and Sauermann (2017), and Bick et al. (2018) are reliable sources for productivity declining at long hours. They do not directly identify a universal 40-hour productivity peak for Brazil.

Recommended fix:

- The appendix already qualifies this well.
- In the main calibration table, use "informed by Pencavel range" rather than language that implies direct identification.

## Web sources checked

- Camara dos Deputados, PEC 8/2025 protocol: https://www.camara.leg.br/noticias/1136400-pec-que-acaba-com-a-escala-de-trabalho-6x1-e-protocolada-na-camara
- Camara dos Deputados, 40h relator proposal: https://www.camara.leg.br/noticias/1229360-relator-propoe-jornada-maxima-de-40-horas-e
- Camara dos Deputados, CCJ admissibility: https://www.camara.leg.br/noticias/1265049-comissao-aprova-admissibilidade-de-propostas-que-acabam-com-a-escala-6x1
- Camara dos Deputados, special commission: https://www.camara.leg.br/noticias/1266146-motta-cria-comissao-especial-para-analisar-fim-da-escala-6x1
- FRED, `RTFPNABRA632NRUG`: https://fred.stlouisfed.org/series/RTFPNABRA632NRUG
- Groningen PWT 11.0: https://www.rug.nl/ggdc/productivity/pwt/pwt-releases/pwt110
- NBER WP 34445: https://www.nber.org/papers/w34445
- PSE working paper PDF, Asai, Lopes, and Tondini: https://www.parisschoolofeconomics.eu/app/uploads/2024/11/asai-kentaro-firm-level-effects-of-reductions-in-working-hours.pdf
- NBER WP 28391, Dix-Carneiro et al.: https://www.nber.org/papers/w28391
- Author-page publication metadata for Dix-Carneiro et al.: https://campuspress.yale.edu/pennygoldberg/research/selected-publications/

## Recommended next actions

1. Add complete bibliographic entries and citations for PNAD/SIDRA, RAIS/CAGED, and DIEESE.
2. Strengthen the DIEESE contracted-hours provenance with exact table/page/source file.
3. Qualify legislative wording around 40h as a relator proposal or reported legislative alternative.
4. Add DOI/final metadata for Dix-Carneiro et al. and verify or replace Lemos and Galvao (2020).
5. Add extraction dates for FRED/PWT and SIDRA data.
6. Clean unused `.bib` entries before submission.

## Implementation status

Applied on 2026-04-28:

- Added or strengthened `.bib` entries for PNAD/SIDRA, RAIS 2022, PWT 11.0, FRED/PWT Brazil, DIEESE 2024, Lei 8.212/1991, and eSocial rural payroll guidance.
- Replaced the unverified Lemos and Galvao agricultural-cost citation with official payroll-compliance sources and softened the sectoral-wedge language.
- Qualified 40-hour legislative language as a relator proposal or reported alternative rather than as a settled official endpoint.
- Made the DIEESE mapping explicit in the main text, appendices, and `data_final/calibration_targets.csv`.
- Added extraction and frozen-file notes for SIDRA and FRED/PWT inputs.
- Made the wage-premium-to-`sigma_sub` bridge visible near the main calibration table as an inferential discipline, not a direct estimate.
