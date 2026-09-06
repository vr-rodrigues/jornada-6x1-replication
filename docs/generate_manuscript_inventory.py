"""Inventory old manuscript claims without modifying any manuscript input."""
from pathlib import Path
import re,csv,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[1]
SNAP=Path((ROOT.parent/"AUDITORIA_ATUAL.txt").read_text(encoding="utf-8-sig").strip())/"snapshot"
OUT=ROOT/"docs"
issues={
"RAIS_SHARES":("Participação formal por porte","59% para pequenas; subcategorias13%+19%=32%; nenhuma coincide com fonte oficial2022.",
"RAIS2022: 20.793.602/52.790.864=39,3886374% de vínculos ativos em estabelecimentos de1–49; complemento60,6113626%. Não confundir com pessoas ou empresa consolidada.",
"data_intermediate/reprocessed/rais_targets.json; fonte MTE TABELA2 C87:D95"),
"EMPLOYMENT_ACCOUNTING":("Contabilidade formal versus total","37,7% resulta de tratar59%/41% formais como participações totais.",
"Com os mesmos inputs hipotéticos59%/41% e50%/20%, aplicar s_total proporcional a s_formal/(1-i): agregado40,9158050%. Isso é teste contábil, não taxa PNAD.",
"src/model/groups.py; tests/test_model.py"),
"PNAD_CNPJ":("Dicionário CNPJ","V4017 não é o indicador CNPJ usado na definição ampla; resultado antigo não é comparável sem isolar codificação.",
"Usar V4019 com categorias1/2 e universo elegível explícitos. MESMA amostra2024T4: classificaçãoV4017=44,1741162%; corretaV4019=38,6000872%.",
"data_intermediate/reprocessed/empirical_audit.json; provenance/input_PNADC_trimestral.txt"),
"PNAD_MOMENTS":("Momentos PNAD nacionais/setoriais","Mudança de CNPJ altera status, médias, pesos, composição e todos os contrafactuais derivados.",
"Reconstruir tabelas usando PNAD2024T4 reprocessada; nacional informalidade38,6000872%; manter mesmas regras, pesos e trimestre entre setores.",
"data_intermediate/reprocessed/pnad_targets.json; data_final/reprocessed/"),
"VINTAGE":("Trimestre, versão e universo","pnad_targets legado contém média2025=37,8% e2025T4=37,6%, mas setor/microdados manuscrito usam2024T4.",
"Declarar cada vintage. Principal empírico2024T4; versão do arquivoPNADC_042024_20250815 e pesoV1028. Não chamar37,8 e38,6001 de simples atualização de definição sem decompor vintage.",
"data_intermediate/pnad_targets.json; data_intermediate/reprocessed/manifest.json"),
"HOURS_SOURCE":("Fonte e conceito de horas","Pesos .085/.269/.646 atribuídos a DIEESE/Table7 sem tabela verificável; V4039 habitual não mede horas contratadas.",
"Manter pesos legados identificados como hipótese. PNAD: habitualV4039, efetivaV4039C, sem substituir por contratada. Principal mantém habitual integral; topcode44 é cenário separado.",
"data_intermediate/reprocessed/pnad_targets.json; data_intermediate/reprocessed/rais_targets.json"),
"HOURS_IDENTITIES":("Validação contábil versus comportamental","Média das faixas e parcela acima36h são funções algébricas de theta; perturbar theta não as transforma em validação fora da calibração.",
"Reclassificar como identidade/mapeamento. Separar comparação de medida habitual/contratada e retirar alegação de validação comportamental; usar testes de otimização e momentos externos efetivamente independentes.",
"src/calibration/audit_fit_moments.py; tests/test_model.py"),
"OMEGA_IDENTIFICATION":("Peso tecnológico CES","omega=1-informalidade não decorre da CES; momento salarial não identifica simultaneamente sigma,omega,eta.",
"Rotular .622 hipótese congelada; manter sigma1,326 no comparativo e recalibrar omega condicionalmente à ponte de remuneração, com universo/medida explícitos.",
"src/calibration/wage_bridge.py; COMPARATIVO_RESULTADOS.csv"),
"WAGE_BRIDGE":("Ponte salarial e MNR","Prêmio wage-posting de MNR não é por identidade razão de produtos marginais CES; fórmulas semanais/horárias/efetivas e agregação por firma eram confundidas.",
"Calcular folhas por firma antes de médias. Diferenciar renda mensal/semanal, folha/horas e média individual horária. MNR e R[1,15;1,55] são hipóteses externas, não identificação automática.",
"src/calibration/wage_bridge.py; tests/test_wage_bridge.py; https://pubs.aeaweb.org/doi/10.1257/aer.20121110"),
"ETA_IDENTIFICATION":("Eficiência informal","eta=.40 não é automaticamente razão salarial observada: a razão CES depende também de sigma,omega,quantidades e horas.",
"Rotular eta como hipótese condicionante; evitar afirmação de identificação estrutural correta apenas pela faixa salarial1/3–1/2.",
"src/model/ces_aggregator.py; docs/AUDITORIA_NUCLEO.md"),
"WEDGES":("Cunhas e normalização","Uma informalidade-alvo não identifica separadamente tau e pi; gamma não é alíquota observada CLT/FGTS.",
"Declarar tau>=0,pi>=0,tau*pi=0 e tau-pi*NI=MP_NF-MP_NI no baseline; recalibrar valores da tabela; gamma permanece hipótese de ajuste.",
"src/model/calibration.py; docs/AUDITORIA_NUCLEO.md"),
"FIRM_FOC":("FOC incorreta no apêndice","FOC omite MP_NI, duplica fator marginal CES e usa sinal incompatível para pi*NI.",
"Substituir por MP_NF-MP_NI-tau+pi*NI-gamma*(NF-NFprev)=0; acrescentar desigualdadesKKT nas fronteiras.",
"src/model/firm_problem.py; tests/test_model.py"),
"GHH_CE":("Composto GHH versus CE","(C1-v1)/(C0-v0)-1 é variação percentual do composto, não CE normalizado pelo consumo.",
"Renomear dGHH; acrescentar CE=[C1-C0-v1+v0]/C0. Usar colunas dGHH_pct e CE_pct do COMPARATIVO_RESULTADOS.csv, nunca tratar dCV legado como CE.",
"src/model/welfare.py; COMPARATIVO_RESULTADOS.csv"),
"RESOURCE_CONSTRAINT":("Consumo e tratamento de custos","Função objetivo subtrai tau,pi e ajuste, mas bem-estar não explicita se pagamentos são transferências ou recursos.",
"Declarar padrão C+ajuste=Y com tau/pi integralmente devolvidos; alternativa recursos C+ajuste+tau*NF+pi*NI²/2=Y. Não inferir incidência das transferências.",
"src/model/firm_problem.py; docs/AUDITORIA_NUCLEO.md"),
"INCIDENCE":("Incidência não identificada","+1,41% formais que ficam; -28,57% desformalizados; zero informais e participações1,9% não são resultados sustentados por orçamento/utilidade por tipo.",
"Retirar resultados distributivos ou construir equações de renda, transferências, propriedade de capital e utilidade por tipo. hI fixo não implica renda/CE informal invariável.",
"docs/AUDITORIA_NUCLEO.md; src/model/simulation.py"),
"CAPITAL":("Capital endógeno não modelado","Redução1–2p.p.,1,5p.p. e horizonte3–5anos não decorrem do modelo deK fixo; fórmula de elasticidade não fecha equilíbrio de investimento.",
"Retirar números e afirmação de resposta endógena prevista. TratarK exógeno em sensibilidade ou adicionar equações de demanda/estoque/custo de uso/depreciação e horizonte.",
"src/model/production.py; src/model/simulation.py"),
"IDENTIFIED_BOX":("Sensibilidade versus identificação","Oito cantos de caixa escolhida não verificam restrições salariais e demais momentos; limites não são conjunto identificado.",
"Renomear grade de sensibilidade condicional; incluir pontos interiores e reportar restrições verificadas/falhas por ponto. Usar nova SENSITIVITY.csv.",
"src/calibration/corrected_pipeline.py; output/corrected/sensitivity/"),
"DECOMPOSITION":("Decomposição do produto","Parcelas anteriores/resíduo CES não garantem um denominador comum nem soma exata em níveis.",
"Usar Y0,YH,YE,Y1; horas→eficiência→realocação; todas as diferenças divididas porY0. Regenerar barras e valores do comparativo.",
"src/model/decomposition.py; COMPARATIVO_RESULTADOS.csv"),
"EFFICIENCY_ANCHOR":("Elasticidade e extrapolação","E_Q=.6 é derivada de h*e(h), não deY agregado; pico40h e resposta abaixo do pico não são estimativas brasileiras identificadas.",
"Declarar âncora externaH_REF_EFFICIENCY=42,244h e hipóteses dos dois modos. Não recalibrar fadiga usando média abaixo do pico nem supor igualdade de resultados das duas calibrações acima40h.",
"src/model/efficiency.py; docs/AUDITORIA_NUCLEO.md"),
"ALPHA_GOLLIN":("Parcela de capital","alpha=.35 é atribuída a ajustePWT/Gollin sem fórmula executável/insumos que levem labsh=.578 ao valor.",
"Identificar .35 como hipótese enquanto ajuste não for reconstituído; se chamar estimativaGollin, apresentar equação e componentes observados por ano/universo.",
"data_intermediate/pwt_targets.json; data_final/calibration_targets.csv"),
"RESULTS":("Resultados e conclusões dependentes","Valores deA_req,produto,informalidade,GHH,limiares,ranking,setores e comparações históricas dependem do código/dados corrigidos.",
"Regenerar da versão explícita no COMPARATIVO_RESULTADOS.csv. Mostrar original,código corrigido/entradas congeladas e reprocessado; separar ponte e topcode44. Não fixar novo principal por busca textual.",
"COMPARATIVO_RESULTADOS.csv; output/corrected/"),
"AREQ_ALLOCATION":("Composição dentro da compensação","Notação deve explicitar NF*(A); composição já reotimizava antes da correção e não foi uma margem nova adicionada.",
"Preservar reotimização a cadaA e reportar comparação composição baseline congelada; A_req assinado e teste de restauração.",
"src/model/areq_solver.py; docs/AUDITORIA_NUCLEO.md"),
"MIDPOINT":("Ponto médio aritmético","1,40 é chamado ponto médio do intervalo[1,15;1,55], cujo ponto médio é1,35.",
"Chamar1,40 alvo expositivo escolhido, não ponto médio; não modificar calibração para perseguir resultado antigo.",
"(1.15+1.55)/2=1.35; paper/tex/sec_calibration.tex:48"),
"CURVE_EQUALITY":("Função de eficiência versus curva calibrada","Igualdade de e(h) acima40h não implica curvasA_req idênticas quando baseline tem horas abaixo40 e cada modo recalibra cunhas.",
"Restringir igualdade à funçãoe(h) para h>=h_star; apresentar diferenças efetivamente calculadas entre curvas na versão correspondente.",
"src/model/efficiency.py; COMPARATIVO_RESULTADOS.csv"),
"STALE_DERIVATIVES":("Arquivos de submissão/apoio antigos","Cópias de submissão,texautogerado e notas locais retêm calibrações diferentes e conclusões antigas.",
"Preservar como histórico; não usar como saída nova. Regenerar PDFs e ZIPs somente após revisar fontesPT/EN; atualizar notas que dizem baseline atual7,26%sigma.60.",
"paper/arxiv_submission_main_pt*/; ../jornada 6x1/50-paper/paper-jornada-6x1.md")
}
def norm(s):
 return s.replace("{,}",".").replace(r"\,", "").lower()
def classify(path,line,context):
 s=norm(line);p=path.as_posix();found=set()
 if "V4017" in line:found.add("PNAD_CNPJ")
 if ("0.590" in s or "0.59" in s or "59\\%" in s or "59%" in s) and (any(x in s for x in ["formal","small","pequen","share"]) or "rais_targets" in p):found.add("RAIS_SHARES")
 if "rais_targets.json" in p and any(x in s for x in ["0.13","0.19","0.59","0.41"]):found.add("RAIS_SHARES")
 if any(x in s for x in ["37.7","0.377"]):found.add("EMPLOYMENT_ACCOUNTING")
 if ("44.2" in s or "44.174" in s or "71.8" in s or "44.4" in s) and any(x in s for x in ["inform","nacional","national","agric","ind","pnad"]):found.add("PNAD_MOMENTS")
 if "pnad2025" in s or ("2025" in s and ("pnad" in s or "trimestre" in s)):found.add("VINTAGE")
 if "dieese" in s or "source checked 2026-04-28" in s or ("v4039" in s and ("contract" in s or "contrat" in s)):found.add("HOURS_SOURCE")
 if any(x in s for x in ["algebraic","alg","panel b1","painel b1"]) and any(x in s for x in ["calibra","momento","moment","theta","weights"]):found.add("HOURS_IDENTITIES")
 if ("omega" in s or "ces weight" in s or "peso formal" in s) and any(x in s for x in ["pnad","informality","informalidade","narrow"]):found.add("OMEGA_IDENTIFICATION")
 if any(x in s for x in ["mnr","meghirnarita","wage premium","pr\\^emio salarial"]):found.add("WAGE_BRIDGE")
 if "eta_i" in s and any(x in s for x in ["wage","salarial","identifica"]):found.add("ETA_IDENTIFICATION")
 if any(x in s for x in ["tau_s","tau_g","pi_m","gamma_f"]) and any(x in s for x in ["calibr","bisse","bise","custo","cost","clt","enforcement","42.11"]):found.add("WEDGES")
 if r"\frac{\partial y_g}{\partial l_{f,g}}" in s and ("rho-1" in s):found.add("FIRM_FOC")
 if ("cv" in s and any(x in s for x in ["delta","compens","ghh","eq:cv"])) or "consumption-equivalents" in s:found.add("GHH_CE")
 if any(x in s for x in ["1.41","28.57","formal stayers","zero direct incidence","incid\\^encia direta zero","informal unaffected"]):found.add("INCIDENCE")
 if ("capital" in s or "varepsilon_k" in s or "req}}^{k}" in s) and any(x in s for x in ["adjust","ajuste","endogenous","end\\","1","2","5","horizon","horizonte"]):found.add("CAPITAL")
 if any(x in s for x in ["envelope","caixa","eight-corner","eight corners","oito cantos","disciplined box","identified set"]):found.add("IDENTIFIED_BOX")
 if any(x in s for x in ["decomposition","decomposi"]) and any(x in s for x in ["output","produto","delta y","res","ces","fig_decomp"]):found.add("DECOMPOSITION")
 if ("e_q" in s or "kappa" in s or "e(h)" in s) and any(x in s for x in ["pencavel","elastic","peak","pico","42.244","deriva"]):found.add("EFFICIENCY_ANCHOR")
 if "gollin" in s:found.add("ALPHA_GOLLIN")
 if "midpoint" in s and "1.40" in s:found.add("MIDPOINT")
 if ("curv" in s and "coincid" in s) or ("curves" in s and "coincide" in s):found.add("CURVE_EQUALITY")
 if ("areq" in s or "a_{\\text{req}}" in s or "a_req" in s) and any(x in s for x in ["solve","resolve","monot","equation","equa"]):found.add("AREQ_ALLOCATION")
 if re.search(r"\d",s) and any(x in s for x in ["a_req","a_{\\text{req}}","ptf","tfp","ghh","cv","informalidade","informality","output loss","perda","welfare","bem-estar"]):found.add("RESULTS")
 if "autogen" in p and "&" in s and re.search(r"\d",s):found.add("RESULTS")
 if "&" in s and re.search(r"\d",s) and any(x in norm(context) for x in ["results","resultados","heatmap","sensitivity","sensibilidade","welfare","bem-estar","setor","sector","facts","fatos","calibration_fit"]):found.add("RESULTS")
 if "/arxiv_submission" in p and found:found.add("STALE_DERIVATIVES")
 if "50-paper" in p and any(x in s for x in ["7.26","0.60","baseline atual","20/20"]):found.add("STALE_DERIVATIVES")
 return found
files=list((ROOT/"paper").rglob("*.tex"))+list((ROOT/"paper").rglob("*.bib"))
files+=list((ROOT.parent/"jornada 6x1"/"50-paper").glob("*.md"))
files+=[ROOT/"data_intermediate"/s for s in ["pnad_targets.json","rais_targets.json","sectoral_data.README.md"]]
files+=[ROOT/"data_final/calibration_targets.csv"]
files+=[ROOT/"docs"/s for s in ["DATA_PROVENANCE.md","MODEL_VALIDATION.md","SIGMA_SUB_DECISION_MEMO.md"]]
rows=[];manifest=[]
for path in sorted(files):
 raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 try:rel=path.relative_to(ROOT).as_posix()
 except ValueError:rel="../"+path.relative_to(ROOT.parent).as_posix()
 snapshot=SNAP/rel if not rel.startswith("../") else None
 manifest.append(dict(file=rel,sha256=digest,lines=len(raw.decode("utf-8-sig").splitlines()),
                      archived_snapshot=str(snapshot) if snapshot and snapshot.exists() else "external local note preserved in place"))
 context=""
 for n,line in enumerate(raw.decode("utf-8-sig").splitlines(),1):
  if r"\section" in line or r"\caption" in line or r"\label{tab:" in line:context=line
  for issue in sorted(classify(Path(rel),line,context)):
   category,reason,action,evidence=issues[issue]
   rows.append(dict(issue_id=issue,category=category,status="triagem_contexto_numerico" if issue=="RESULTS" else "revisao_exigida",
                    source_file=rel,line=n,old_number_or_claim=line.strip(),reason=reason,
                    replacement_or_required_action=action,evidence_new=evidence,
                    source_sha256=digest,source_snapshot=str(snapshot) if snapshot and snapshot.exists() else ""))
# Precise equation/resource entry whose missing budget cannot be regex-located.
for rel,number in [("paper/tex/main_pt.tex",159),("paper/tex/sec_model.tex",21)]:
 path=ROOT/rel;raw=path.read_bytes();line=raw.decode("utf-8-sig").splitlines()[number-1]
 category,reason,action,evidence=issues["RESOURCE_CONSTRAINT"]
 rows.append(dict(issue_id="RESOURCE_CONSTRAINT",category=category,status="revisao_exigida",
                  source_file=rel,line=number,old_number_or_claim=line,reason=reason,
                  replacement_or_required_action=action,evidence_new=evidence,
                  source_sha256=hashlib.sha256(raw).hexdigest(),source_snapshot=str(SNAP/rel)))
rows.sort(key=lambda r:(r["source_file"],r["line"],r["issue_id"]))
with (OUT/"NUMEROS_MANUSCRITO_A_REVISAR.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/"MANIFESTO_INVENTARIO_MANUSCRITO.json").write_text(json.dumps(dict(
 created="2026-09-05",files=manifest,issue_count=len(rows),locations=len({(r["source_file"],r["line"]) for r in rows})),
 ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(dict(rows=len(rows),locations=len({(r["source_file"],r["line"]) for r in rows}),
                       files_scanned=len(files),categories=collections.Counter(r["issue_id"] for r in rows)),indent=2))

