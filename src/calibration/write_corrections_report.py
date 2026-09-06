"""Write the audit report from the current executed results and archive hashes."""
from pathlib import Path
import csv,json,hashlib

ROOT=Path(__file__).resolve().parents[2]


def write_report(out,rows,status,archive):
    out=Path(out)
    def fmt(v,places=4):return f'{float(v):.{places}f}'.replace('.',',')
    def table(selected):
        lines=['| Eficiência | Teto | ΔY % | A_req % | A_fixo % | Informalidade % | ΔGHH % | CE % |',
               '|---|---:|---:|---:|---:|---:|---:|---:|']
        for r in selected:
            lines.append('| '+('Bilateral' if r['efficiency_mode']=='bilateral' else 'Fadiga acima do pico')+f" | {r['hours_cap']} | "+' | '.join(fmt(r[k]) for k in ['dY_pct','A_req_pct','A_req_frozen_pct','informality_pct','dGHH_pct','CE_pct'])+' |')
        return '\n'.join(lines)
    primary=[r for r in rows if r['version']=='reprocessed_data']
    frozen=[r for r in rows if r['version']=='code_corrected_frozen_inputs']
    top=[r for r in rows if r['version']=='reprocessed_topcoded44']
    changed=[]
    if archive:
        snap=Path(archive)/'snapshot'
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file() or p.parts[len(ROOT.parts)] not in ('src','tests','docs') and p.parent!=ROOT:continue
            if '__pycache__' in p.parts or p.suffix in ('.pyc','.pdf','.csv'):continue
            old=snap/p.relative_to(ROOT)
            if not old.exists() or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(old.read_bytes()).digest():
                changed.append(str(p.relative_to(ROOT)).replace('\\','/'))
    decomp=['| Eficiência | Teto | Horas físicas | Eficiência | Realocação | Total |','|---|---:|---:|---:|---:|---:|']
    for r in primary:
        decomp.append('| '+r['efficiency_mode']+f" | {r['hours_cap']} | "+' | '.join(fmt(r[k]) for k in ['hours_pct','efficiency_pct','reallocation_pct','dY_pct'])+' |')
    checks=status.get('numerical_checks',{})
    text=f'''# Relatório de correções e replicação

Execução: `{out.name}`. Código, dados reais, resultados nacionais e setoriais, tabelas e figuras foram executados. O comando original falhou por dependência de output setorial antigo; o executor corrigido gera esse resultado antes das figuras. Nenhum parâmetro foi escolhido para recuperar os números antigos.

## Reprodução e preservação

Na pasta `replication_package`, o comando completo é:

```powershell
python run_all.py --refresh-data --tests --paper
```

Na pasta aberta originalmente, use `python replication_package/run_all.py --refresh-data --tests --paper`. Instalação inicial: `python -m pip install -r requirements.txt`; `requirements-replication.lock.txt` registra as versões usadas. Sem `--refresh-data`, o executor lê exclusivamente os agregados reprocessados com proveniência explícita. Para refazer pelo arquivo bruto oficial arquivado: `python src/data_raw/reprocess_verified_inputs.py --official-only`. Para a rota BQ exclusiva, omita `--allow-official-fallback` no coletor e autentique um projeto autorizado.

A cópia anterior a qualquer modificação está em `{archive}`: `snapshot/`, `manifest_original.json`, `local_changes.patch`, `git_status.txt`, `git_head.txt` e versões originais. Ela inclui as alterações locais que já existiam; não houve checkout, reset ou restauração sobre o trabalho do usuário. Os dados originais foram comparados por SHA256 e continuam idênticos. Os arquivos novos ficam em `reprocessed/` e cada execução usa um diretório inédito em `output/runs/`.

O baseline foi executado com `python run_all.py --tests --paper` em `baseline_run/`, com `output/` inicialmente vazio. O log e status são `baseline_run.log` e `baseline_status.json`; os 20 testes originais foram executados também de forma independente e passaram. O pipeline original terminou com código 1: `plot_sectoral_fig.py` tenta ler `output/sectoral/tables/SECTOR_AREQ_EMPIRICAL.csv`, mas o executor não gera o arquivo. Por isso o LaTeX original não chegou a ser compilado; PDFs existentes são históricos, não resultados dessa execução. O novo apêndice numérico foi gerado separadamente e inspecionado visualmente.

O ambiente inicial tinha Python 3.12.14, NumPy 2.3.5, Pandas 3.0.1 e não tinha SciPy. Pandas estava fora do intervalo do requirements original. Instalado o requirements para o núcleo contínuo: Pandas 2.3.3 e SciPy 1.18.1; as demais versões estão nos logs de cada execução. O baseline original não dependia de SciPy porque resolvia a firma em grade.

`probe_original.py` usa outro interpretador/processo para importar somente o código arquivado e recalcular 40h/36h nos dois modos. A coluna `original` do comparativo é dessa execução nova. CE foi calculado agora a partir das alocações originais e está identificado assim. A decomposição corrigida e A_fixo não existiam no original e suas células ficam vazias; números antigos não foram inventados. O original arredondava informalidade para 37,70%, enquanto a grade do módulo produz 37,7045% no bilateral.

## Contabilidade, otimização e parâmetros

As participações formais são convertidas por `s_total[g] = [s_formal[g]/(1-i[g])] / sum_j[s_formal[j]/(1-i[j])]`. No teste 59%/41% com informalidades 50%/20%, as participações totais são 69,71935%/30,28065%, e a informalidade agregada é **40,915805%**. Isso é contabilidade, não uma estimativa empírica de informalidade brasileira.

Há um só núcleo para eficiência bilateral `exp[-kappa(h-h*)²]` e fadiga acima do pico `exp[-kappa max(h-h*,0)²]`. `solve_NF` resolve continuamente a condição `MP_NF - MP_NI - tau + pi*NI - gamma*(NF-NF_prev) = 0`, verificando KKT e os valores nas fronteiras. A produção é côncava para os parâmetros admitidos e os custos são convexos; nesse domínio a solução certificada é global.

O único momento de informalidade identifica `tau-pi*NI`. A separação impõe a normalização adicional `tau>=0`, `pi>=0`, `tau*pi=0`: se a diferença de produtos marginais é positiva, pi=0; caso contrário, tau=0. As cunhas são recalibradas para cada modo e cenário. Não se afirma que ambas foram identificadas separadamente por dados ou legislação. Gamma, capital por grupo, alpha e eta continuam hipóteses quando não há uma medição independente. O arquivo `CALIBRATED_PARAMETERS.csv` contém os valores efetivamente usados, por variante/grupo.

A busca por A_req **já reotimizava a composição no código original**. Isso foi preservado e testado. Agora o intervalo da raiz se expande quando necessário, o produto restaurado é verificado e a compensação com composição congelada aparece ao lado. A_req é assinado: se o contrafactual aumenta produto, um valor negativo restaura exatamente Y0; o ganho positivo necessário seria zero. Não há equação de investimento nem ajuste endógeno de capital.

## Dados reais e limitações de acesso

A Base dos Dados via BigQuery foi tentada primeiro. O login pessoal do CLI expirou; as credenciais disponíveis permitiram ler schemas, mas o job foi bloqueado por `bigquery.jobs.create` em `upa-research`. A leitura de linhas também encontrou restrição de acesso. Nenhum projeto corporativo foi usado para consultas e nenhum byte foi cobrado. A solicitação de reautenticação ficou registrada; o trabalho independente prosseguiu com **fallback explícito** aos arquivos oficiais. Não se apresenta essa rota como uma consulta BQ concluída.

A PNAD **2024T4** foi lida do arquivo `PNADC_042024_20250815.zip` (209.873.314 bytes), com 469.334 pessoas na amostra. Universo: ocupados de 14+ anos, Brasil, trabalho principal, peso V1028. São **101.831.958,51 ocupados** e **38,6000872% de informalidade**. V4019 é CNPJ (1 sim, 2 não); V4017 é sócio. Com os mesmos microdados/pesos, o erro V4017 daria **44,1741162%**, isolando o erro de variável de qualquer troca de trimestre. Categorias, ausentes, limites, pesos, URLs e hashes estão em [AUDITORIA_DADOS.md](docs/AUDITORIA_DADOS.md) e `data_intermediate/reprocessed/provenance/`. [Fonte IBGE](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/2024/).

A RAIS 2022 verificada tem **52.790.864 vínculos ativos em 31/12**. Estabelecimentos de 1 a 49 empregados somam **20.793.602 vínculos (39,3886374%)**: nem 59%, nem 13%+19%=32%. O dado é de estabelecimento, não empresa consolidada, e vínculos, não pessoas. A planilha oficial foi lida nas células C87:D95 da aba TABELA 2 e confere com a tabela 6 do Sumário Executivo. [Planilha MTE](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/rais/rais-2022/4-tabelas_rais-2022.xlsx).

As informalidades 50%/20% por porte não são dados da RAIS. A variante `rais_verified_only` troca apenas a participação administrativa e mantém essas taxas como hipóteses: isso implica informalidade agregada de 35,29245%, sem forçá-la a coincidir com a PNAD. O cenário empírico nacional usa um grupo com a informalidade PNAD observada, evitando inventar a ligação RAIS-vínculos/estabelecimentos versus PNAD-pessoas/negócios. `single_group_frozen_control` isola a mudança de agregação antes da mudança de dados.

Os pesos 0,085/0,269/0,646 antes atribuídos a DIEESE permanecem **hipóteses de fonte não verificada**; não foram certificados por uma homepage ou por documentos de outros anos. As novas horas são explicitamente habituais (V4039); efetivas são V4039C; contratadas não estão disponíveis nessa extração da PNAD. Não se substitui um conceito pelo outro nem se troca trimestre silenciosamente.

## Ponte formal-informal e horas iniciais

Sigma foi mantido em **1,326** em todas as comparações principais. A ponte calcula produtos marginais por firma, depois soma as remunerações imputadas e seus denominadores: `(sum folha_F/sum horas_F)/(sum folha_I/sum horas_I)`. Não aplica uma CES às somas de trabalho de firmas heterogêneas e não iguala omega à participação formal. O prêmio por trabalhador/semana e o prêmio por unidade de trabalho efetivo são objetos distintos.

Com entradas congeladas e omega=0,622, o bilateral implica razão horária **1,697819** e semanal **1,630061**. Para o alvo hipotético horário R=1,4, omega recalibrado é **0,576167**. A razão R=1,4 é uma hipótese legada; MNR é um modelo de busca e fixação de salários, e não fornece automaticamente a ponte CES competitiva usada aqui. [MNR, AER 2015](https://pubs.aeaweb.org/doi/10.1257/aer.20121110).

Na PNAD reprocessada, a razão ampla de remuneração/horas é **1,62244345**, enquanto a razão das remunerações médias semanais é **1,88009971**; a razão das médias individuais por hora é **1,58409450**. A primeira inclui renda de empregadores e conta própria, portanto não é um prêmio salarial puro. Para empregados privados apenas, o momento horário é **1,16432452**; sua aplicação ao modelo amplo aparece como sensibilidade com incompatibilidade de universo declarada. Remuneração positiva e horas válidas usam exatamente a mesma amostra em cada numerador/denominador. A associação entre remuneração observada e produto marginal é uma hipótese adicional, não causalidade identificada.

No cenário empírico principal, as horas habituais observadas são preservadas integralmente no baseline: H0=max(suporte) funciona como identidade, **não como limite legal**. A reforma aplica min(h,40/36) às horas habituais, uma aproximação explicitada. Há 17,9732755% de formais com mais de 44h; limitá-los previamente a 44h reduz sua média de 41,42440 para 39,94664. A variante `reprocessed_topcoded44` isola essa hipótese e recalcula também o denominador horário da ponte, cujo alvo passa a **1,68247326**. A âncora da curva de eficiência permanece em 42,244h para separar dados da hipótese tecnológica; E_Q=0,6 é elasticidade de h*e(h), não diretamente elasticidade de Y nem estimativa brasileira de Pencavel. A curva extrapola para jornadas muito curtas/longas; a sensibilidade sem fadiga e aos picos é essencial. [Pencavel, Economic Journal](https://onlinelibrary.wiley.com/doi/full/10.1111/ecoj.12166).

## Resultados recalculados

### Código corrigido, entradas numéricas congeladas

{table(frozen)}

### PNAD reprocessada, baseline habitual observado e ponte horária recalibrada

{table(primary)}

### Hipótese alternativa: baseline formal previamente limitado a 44h

{table(top)}

Esses contrastes não são efeitos causais estimados nem recomendação de teto ótimo. O pequeno A_req de 40h com horas habituais brutas depende da recuperação de eficiência que a curva atribui às jornadas longas. A variante limitada a 44h e os cenários sem fadiga mostram o papel dessa hipótese. Para 36h, o sinal do bem-estar também depende da função de eficiência e da medição das horas.

### Decomposição do cenário empírico principal

Ordem declarada: **horas físicas → eficiência → realocação formal-informal**. Y_H mantém a composição e a eficiência de cada bin inicial, trocando só as horas. Y_E atualiza a eficiência com composição congelada. Y1 permite reotimização. Parcelas: 100(Y_H-Y0)/Y0, 100(Y_E-Y_H)/Y0 e 100(Y1-Y_E)/Y0. Todas usam Y0; as interações são atribuídas conforme essa ordem.

{chr(10).join(decomp)}

O JSON completo guarda os níveis intermediários e o resíduo da soma. O gráfico antigo combinava objetos com denominadores/interpretações diferentes e não é usado na figura nova.

## GHH, CE e recursos

`v(h)=psi*h^(1+nu)/(1+nu)`, `G=C-v(h)`. Reporta-se separadamente `ΔGHH=100*(G1-G0)/G0` e `CE=100*[C1-C0-v(h1)+v(h0)]/C0`. Consumo e horas são por trabalhador no agente representativo. `dCV_pct` existe somente como alias depreciado de GHH para compatibilidade; tabelas novas usam nomes corretos.

Restrição principal: **C + ajuste = Y**. Tau e pi são pagamentos privados tratados como transferências devolvidas ao domicílio; o ajuste quadrático é destruição de recursos. A opção `resource_costs=True` testa **C + ajuste + tau*NF + pi*NI²/2 = Y**. O modelo mantém K e N fixos; não aloca consumo por indivíduo nem calcula transições de renda de formais que permanecem, informais que permanecem ou desformalizados. Portanto não entrega incidência distributiva nem correção endógena de capital de 1-2 pp.

## Setores, sensibilidades e testes

Os resultados de agricultura, indústria/construção, serviços e agregado estão em `RESULTADOS_SETORIAIS.csv`; ambos os modos e os tetos 40/36 são refeitos, com omega congelado e com ponte própria recalibrada sobre as folhas setoriais somadas. Os 19.279,83 ocupados sem setor (0,01893%) são excluídos explicitamente do modelo de três setores e os pesos são renormalizados. Capital proporcional ao VAB legado é uma hipótese, não estoque de capital observado. Não há insumo-produto nem mobilidade intersetorial. Ver [AUDITORIA_SETORIAL.md](docs/AUDITORIA_SETORIAL.md).

As sensibilidades nacionais congeladas contêm grade CES com interiores em sigma/omega/eta, além de eficiência, pico e distribuição de horas. A grade grava quais pontos passam o intervalo **hipotético** da ponte salarial; a caixa inteira não é chamada de conjunto identificado. A sensibilidade nacional empírica recalibra a ponte em cada ponto e inclui ausência de fadiga. A setorial tem 37 casos/592 linhas, também com interiores. Variações de horas/bins e médias são contabilidade, não validação comportamental.

Testes desta execução: código de retorno `{status.get('steps',{}).get('tests_returncode','não solicitado')}`; log em `logs/tests.log`. A suíte verifica transformação das participações, FOCs e fronteiras, CES, restauração com ambas as composições, soma da decomposição, CE/GHH, recursos, categorias PNAD, trimestre, ausentes, pesos, rendimentos e RAIS. Os testes antigos que exigiam recuperar números anteriores foram substituídos por propriedades matemáticas. Máximos de erro na execução: `{checks}`. A revisão independente da ponte está em [AUDITORIA_NUCLEO.md](docs/AUDITORIA_NUCLEO.md).

## Arquivos alterados e organização da entrega

As alterações do núcleo estão em `src/model/`; calibrações e ponte em `src/calibration/`; leitura empírica e merger em `src/data_raw/`, `src/data_clean/` e `src/sectoral/data/`; o modelo setorial chama o mesmo núcleo. `run_all.py` coordena dados, versões, sensibilidades, testes e artefatos em saídas isoladas. `src/tables_figures/build_corrected_assets.py` e `write_corrected_appendix.py` geram tabelas/figuras/apêndice a partir dos resultados atuais. Scripts antigos com cálculos duplicados foram substituídos por adaptadores; originais completos continuam no snapshot. Geradores autônomos exigem um diretório de execução explícito, sem buscar resultados antigos por conveniência.

Arquivos de código/documentação/testes diferentes do snapshot nesta tarefa:

{chr(10).join('- `'+x+'`' for x in changed)}

Os dados reprocessados são novos, não substituições dos brutos originais. `COMPARATIVO_RESULTADOS.csv` e `RESULTADOS_SETORIAIS.csv` na raiz são cópias da última execução concluída; `output/LATEST_RUN.json` aponta para seu diretório. `RUN_MANIFEST.json` registra hashes das entradas, códigos e saídas. Os resultados antigos de `output/` e os manuscritos/PDFs anteriores não são sincronizados como se fossem novos.

## Números e conclusões do manuscrito que exigem revisão

A lista localizada por arquivo/linha está em [NUMEROS_MANUSCRITO_A_REVISAR.md](docs/NUMEROS_MANUSCRITO_A_REVISAR.md) e seu CSV. Inclui: RAIS 59% e 32%; informalidade 37,7% como agregação incorreta; CNPJ V4017 e antiga informalidade setorial/ampla; mistura PNAD 2025 e 2024T4; pesos atribuídos a DIEESE sem documento; ponte semanal chamada horária; omega confundido com participação formal; condição de primeira ordem incorreta no apêndice; GHH chamado CE; parcelas de decomposição incompatíveis; caixa de parâmetros chamada identificada; “validação” por identidades de horas; incidência +1,41%/-28,57% sem equações; capital endógeno reduzindo A_req em 1-2 pp sem lei de movimento. Todos os A_req, produto, informalidade, bem-estar e ordenamentos setoriais devem citar a variante escolhida no novo CSV, em vez de trocar um número isolado mantendo as hipóteses antigas.

O manuscrito original foi preservado para comparação. O apêndice numérico novo contém apenas as estatísticas e qualificações sustentadas pela execução corrigida.
'''
    (ROOT/'RELATORIO_CORRECOES.md').write_text(text,encoding='utf-8')
    (out/'RELATORIO_CORRECOES.md').write_text(text,encoding='utf-8')
