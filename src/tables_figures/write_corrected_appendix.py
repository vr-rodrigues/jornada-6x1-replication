"""Numerical PDF appendix, generated solely from current-run records."""
from pathlib import Path
import csv
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4


def write_appendix(out,rows):
    out=Path(out);folder=out/'paper';folder.mkdir(parents=True,exist_ok=True)
    pdf=folder/'APENDICE_NUMERICO_CORRIGIDO.pdf'
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyPT',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9,textColor=colors.HexColor('#243746')))
    styles.add(ParagraphStyle(name='SmallPT',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=6))
    flow=[]
    def p(text,style='BodyPT'):flow.append(Paragraph(text,styles[style]))
    def table(data,widths=None,compact=False):
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#193b5b')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),8),
            ('BOTTOMPADDING',(0,0),(-1,-1),3 if compact else 6),('TOPPADDING',(0,0),(-1,-1),3 if compact else 6),
            ('ALIGN',(1,0),(-1,-1),'RIGHT'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#eff3f6')]),
            ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#193b5b'))]))
        flow.append(t);flow.append(Spacer(1,10))
    def n(v):return '--' if v is None else f'{v:.3f}'
    p('Jornada de trabalho, produtividade e informalidade','Title')
    p('Apêndice numérico da replicação corrigida','Heading2')
    p('Todos os resultados deste documento foram recalculados na execução indicada no rodapé. Sigma permanece em 1,326. O manuscrito original foi preservado para revisão editorial; este apêndice substitui apenas as estatísticas aqui especificadas.')
    p('Dados e comparação','Heading2')
    p('PNAD Contínua 2024T4: microdados reais, peso V1028, pessoas ocupadas de 14 anos ou mais, trabalho principal; CNPJ em V4019. A rota oficial IBGE/MTE foi usada e registrada após bloqueio de autenticação/permissão no BigQuery. RAIS 2022: vínculos ativos por estabelecimento, sem tratar vínculos como pessoas ou estabelecimentos como empresas.')
    p('Resultados nacionais com dados reprocessados','Heading2')
    primary=[r for r in rows if r['version']=='reprocessed_data']
    if not primary:p('Dados reprocessados indisponíveis. Nenhum resultado empírico foi substituído por output antigo.')
    else:
        table([['Eficiência','Teto','dY %','A_req %','Inf. %','GHH %','CE %']]+[
            ['Bilateral' if r['efficiency_mode']=='bilateral' else 'Só fadiga',str(r['hours_cap'])]+[n(r[k]) for k in ('dY_pct','A_req_pct','informality_pct','dGHH_pct','CE_pct')]
            for r in primary],[85,35,64,70,70,70,70])
        p('A distribuição da PNAD mede horas habituais; aplicar um teto nessas horas é uma hipótese de contrafactual. O cenário principal preserva as horas habituais observadas no baseline; a hipótese alternativa de limitar previamente a 44h é apresentada separadamente. Horas efetivas e contratadas não são substituídas por habituais.','SmallPT')
    p('Contabilidade e bem-estar','Heading2')
    p('As participações no emprego formal são convertidas em participações no emprego total: s_total proporcional a s_formal/(1-informalidade). O exemplo 59%/41%, com taxas 50%/20%, implica 40,915805% de informalidade; é um teste contábil. A RAIS verificada informa 39,388637% de vínculos formais em estabelecimentos com até 49 empregados.')
    p('A escolha formal-informal é contínua, com verificação das condições de primeira ordem e das fronteiras. A_req reotimiza essa escolha em cada tentativa de produtividade. A coluna A_fixo congela o emprego formal na alocação inicial. Capital e população total permanecem fixos.')
    p('GHH = 100(G1-G0)/G0, com G=C-v(h). CE = 100[C1-C0-v(h1)+v(h0)]/C0. Consumo e horas são por trabalhador representativo. No cenário principal, C + custo de ajuste = Y; tau e pi são transferências devolvidas ao domicílio. Não há inferência de incidência distributiva.')
    flow.append(PageBreak())
    p('Comparação em etapas','Title')
    codes={'original':'Original','code_corrected_frozen_inputs':'Código corrigido',
           'bridge_recalibrated_assumed_hourly':'Ponte R=1,4 (hipótese)',
           'rais_verified_only':'Somente RAIS verificada',
           'single_group_frozen_control':'Controle de um grupo',
           'reprocessed_data_fixed_omega':'PNAD / omega fixo',
           'reprocessed_topcoded44':'PNAD / baseline limitado44',
           'reprocessed_data':'PNAD / ponte recalibrada'}
    p('Cada bloco mantém explícita a mudança de código, entrada ou hipótese. No original, CE é calculado agora a partir da alocação original; o pacote antigo chamava a variação GHH de CV. Nenhum valor foi ajustado para recuperar o resultado antigo.','SmallPT')
    data=[['Etapa / eficiência','h','dY %','A_req %','GHH %','CE %','A_fixo %']]
    for r in rows:
        data.append([codes.get(r['version'],r['version'])+(' / B' if r['efficiency_mode']=='bilateral' else ' / F'),str(r['hours_cap'])]+[n(r.get(k)) for k in ('dY_pct','A_req_pct','dGHH_pct','CE_pct','A_req_frozen_pct')])
    table(data,[175,25,53,58,50,50,53],compact=True)
    p('B: eficiência bilateral; F: fadiga somente acima do pico. Os números são diagnósticos condicionais do modelo, sem região identificada conjunta. R=1,4 é uma hipótese antiga. A ponte empírica usa a razão das massas de remuneração por horas no mesmo universo de observações válidas.','SmallPT')
    flow.append(PageBreak())
    p('Decomposição em níveis de produto','Title')
    p('Ordem: horas físicas, eficiência, realocação formal-informal. Cada parcela usa Y0 como denominador: 100(Y_H-Y0)/Y0, 100(Y_E-Y_H)/Y0 e 100(Y1-Y_E)/Y0. A soma é exatamente a variação total, salvo arredondamento. A ordem define a atribuição das interações.')
    data=[['Cenário','h','Horas','Eficiência','Realocação','Total']]
    for r in rows:
        if r['version'] in ('code_corrected_frozen_inputs','reprocessed_data'):
            data.append([('PNAD' if r['version']=='reprocessed_data' else 'Congeladas')+(' / B' if r['efficiency_mode']=='bilateral' else ' / F'),str(r['hours_cap'])]+[n(r[k]) for k in ('hours_pct','efficiency_pct','reallocation_pct','dY_pct')])
    table(data,[130,40,73,73,75,73])
    image=out/'figures/decomposicao_bem_estar.png'
    if image.exists():flow.append(Image(str(image),width=515,height=215))
    p('A composição congelada restaura o produto com A_fixo = 100(Y0/Y_reforma_fixa - 1). A composição reotimizada deve ser resolvida dentro da busca por A. O núcleo preserva esse comportamento que já existia no original.','SmallPT')
    p('O A_req assinado pode ser negativo quando o teto aumenta o produto no modelo. Nesse caso, a redução de produtividade indicada restaura Y0 exatamente; o ganho positivo necessário é zero. Não se trunca o resultado antes de verificar a restauração.','SmallPT')
    p('Restrições da interpretação','Heading2')
    p('O momento de informalidade identifica apenas tau-pi*N_I. A normalização adicional tau>=0, pi>=0, tau*pi=0 separa os dois parâmetros. Omega é tecnológico, não a participação formal. A equivalência entre remuneração e produto marginal é uma hipótese da ponte; não decorre de um modelo de barganha ou fixação de salários.')
    p('E_Q e o pico de eficiência são hipóteses externas. Identidades das distribuições de horas não validam comportamento. Sensibilidades incluem pontos interiores e registram restrições da ponte, mas não constituem um conjunto identificado. Não há equação de acumulação de capital ou de incidência por tipo de trabalhador.')
    flow.append(PageBreak())
    p('Resultados setoriais','Title')
    sector_path=out/'RESULTADOS_SETORIAIS.csv'
    if sector_path.exists():
        with sector_path.open(encoding='utf-8-sig') as f:sector=list(csv.DictReader(f))
        wanted=[r for r in sector if r.get('scenario_variant')=='empirical_bridge']
        if not wanted:wanted=[r for r in sector if r['input_kind']=='reprocessed']
        data=[['Setor / eficiência','h','dY %','A_req %','dInf pp','GHH %','CE %']]
        names={'agriculture':'Agropecuária','industry':'Indústria','services':'Serviços','AGGREGATE':'Agregado'}
        for r in wanted:
            data.append([names.get(r['sector'],r['sector'])+(' / B' if r['efficiency_mode']=='bilateral' else ' / F'),r['h1']]+[n(float(r[k])) for k in ('dY_pct','A_req_pct','dInf_pp','dGHH_pct','CE_pct')])
        if len(data)>1:table(data,[144,30,66,66,66,66,66])
    p('Setores independentes, sem relações de insumo-produto ou mobilidade entre setores. O agregado soma níveis de produto e reotimiza cada setor. A alocação de capital proporcional às parcelas legadas de VAB é uma hipótese; não é uma medição do estoque de capital. Os indicadores setoriais de bem-estar são agentes representativos setoriais, sem incidência sobre pessoas.','SmallPT')
    p('Fontes e rastreabilidade','Heading2')
    p('As URLs oficiais, categorias, exclusões, dicionários, versão dos microdados, hashes e bloqueio BigQuery estão em data_intermediate/reprocessed/ e docs/AUDITORIA_DADOS.md. O manifesto RUN_MANIFEST.json registra códigos, entradas, resultados e testes desta execução. O relatório RELATORIO_CORRECOES.md detalha as alterações e a lista de afirmações do manuscrito que exigem revisão.','SmallPT')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#60717e'))
        canvas.drawString(36,22,'Execução '+out.name+' | Replicação corrigida')
        canvas.drawRightString(A4[0]-36,22,str(doc.page))
    SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=36,leftMargin=36,topMargin=34,bottomMargin=38).build(flow,onFirstPage=footer,onLaterPages=footer)
    return pdf
