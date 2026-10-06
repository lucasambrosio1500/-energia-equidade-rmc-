"""Relatório técnico em PDF, figuras e exploração HTML independente de servidor."""
import json
import math
from pathlib import Path
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .acquire import ROOT

OUT = ROOT / "reports"
DATA = ROOT / "data/processed"
INK, TEAL, MUTED = "#172c38", "#196b66", "#576a73"


def f(value, digits=2):
    if pd.isna(value): return "—"
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def read(name):
    return pd.read_csv(DATA / (name + ".csv"), dtype={"municipality_id": str, "set_id": str, "cnpj": str})


def rings(feature):
    coordinates = feature["geometry"]["coordinates"]
    return [coordinates[0]] if feature["geometry"]["type"] == "Polygon" else [p[0] for p in coordinates]


def figures(municipal, sensitivity, balanced, geo):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.labelcolor": INK, "text.color": INK,
                         "axes.edgecolor": "#9faeac", "savefig.facecolor": "white"})
    cmap = LinearSegmentedColormap.from_list("equidade", ["#e0eee8", TEAL])
    current = municipal[municipal.year.eq(2024)].set_index("municipality_id")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.8), layout="constrained")
    indices = {k: i+1 for i,k in enumerate(current.index)}
    for ax, metric, title, unit in zip(axes, ["low_income_pct", "dec_median"],
                                     ["Contexto social · 2022", "Continuidade · 2024"],
                                     ["Moradores com renda até 1/2 SM (%)", "Mediana de DEC dos conjuntos associados (h)"]):
        patches, values = [], []
        for feat in geo["features"]:
            key = feat["properties"]["codarea"]
            for ring in rings(feat):
                patches.append(Polygon(ring)); values.append(current.loc[key, metric])
            points = np.array(max(rings(feat), key=len))
            center = points.mean(axis=0)
            ax.text(*center, str(indices[key]), ha="center", va="center", fontsize=7, color=INK,
                    bbox=dict(facecolor="white", alpha=.8, edgecolor="none", pad=1))
        pc = PatchCollection(patches, cmap=cmap, edgecolor="white", linewidth=.7)
        pc.set_array(np.array(values)); ax.add_collection(pc); ax.autoscale()
        ax.set_aspect(1/math.cos(math.radians(23))); ax.axis("off"); ax.set_title(title, loc="left", fontsize=13, pad=12)
        cb = fig.colorbar(pc, ax=ax, orientation="horizontal", fraction=.045, pad=.03)
        cb.set_label(unit, fontsize=9)
    fig.savefig(OUT / "mapas.png", dpi=190); plt.close(fig)
    for year in [2022,2024]:
        d = municipal[municipal.year.eq(year)]
        fig, ax = plt.subplots(figsize=(10.4,5.5), layout="constrained")
        ax.scatter(d.low_income_pct, d.dec_median, s=55, color=TEAL, edgecolor="white", zorder=3)
        for i, r in d.iterrows():
            key=r.municipality_id
            ax.annotate(str(indices[key]), (r.low_income_pct,r.dec_median), xytext=(5,5), textcoords="offset points",fontsize=8)
        ax.set_xlabel("Moradores com renda até 1/2 salário mínimo (%) · Censo 2022")
        ax.set_ylabel("Mediana de DEC dos conjuntos associados (h)")
        ax.grid(alpha=.18); ax.set_axisbelow(True)
        rho = sensitivity.query("year == @year and scenario == 'baixa_renda_dec'").iloc[0].rho
        ax.set_title(f"Associação territorial · {year}  |  Spearman descritivo ρ = {f(rho,3)}",loc="left",pad=16)
        fig.savefig(OUT / f"associacao_{year}.png", dpi=180); plt.close(fig)
    fig, axes=plt.subplots(1,2,figsize=(10.4,4.3),layout="constrained")
    for ax,metric,title in zip(axes,["dec_median","fec_median"],["DEC mediano (h)","FEC mediano"]):
        for scope,color in [("Brasil",MUTED),("São Paulo","#956a38"),("RMC",TEAL)]:
            g=balanced[balanced.scope.eq(scope)]
            ax.plot(g.year,g[metric],marker="o",color=color,label=f"{scope} (n={int(g.n_sets.iloc[0])})")
        ax.set_xticks([2022,2023,2024,2025]); ax.set_title(title,loc="left");ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=8)
    fig.savefig(OUT / "evolucao_coorte.png",dpi=180);plt.close(fig)


def pdf(municipal, annual, sensitivity, benchmarks, balanced, diagnostics):
    fontdir=Path(matplotlib.get_data_path())/"fonts/ttf"
    pdfmetrics.registerFont(TTFont("DVS",str(fontdir/"DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DVS-Bold",str(fontdir/"DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("DVS",normal="DVS",bold="DVS-Bold",italic="DVS",boldItalic="DVS-Bold")
    styles=getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName="DVS";styles[name].textColor=colors.HexColor(INK)
    styles.add(ParagraphStyle(name="Body",fontName="DVS",fontSize=9.2,leading=14,spaceAfter=9))
    styles.add(ParagraphStyle(name="Small",fontName="DVS",fontSize=7.6,leading=11,spaceAfter=7,textColor=colors.HexColor(MUTED)))
    styles.add(ParagraphStyle(name="Kicker",fontName="DVS-Bold",fontSize=8,leading=12,spaceAfter=10,textColor=colors.HexColor(TEAL)))
    styles["Title"].fontName="DVS-Bold";styles["Title"].fontSize=30;styles["Title"].leading=35;styles["Title"].alignment=TA_LEFT
    styles["Heading1"].fontName="DVS-Bold";styles["Heading1"].fontSize=18;styles["Heading1"].leading=23
    styles["Heading2"].fontName="DVS-Bold";styles["Heading2"].fontSize=11.5;styles["Heading2"].leading=17
    story=[]
    def p(text,style="Body"):story.append(Paragraph(text,styles[style]))
    def title(k,t):p(k,"Kicker");p(t,"Heading1");story.append(Spacer(1,8))
    def table(rows,widths=None,fontsize=8):
        cellstyle=ParagraphStyle(name="cell",parent=styles["Body"],fontSize=fontsize,leading=fontsize+3,spaceAfter=0)
        cells=[[Paragraph(str(x),cellstyle) for x in row] for row in rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e6eeea")),("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("BOTTOMPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),
                               ("LINEBELOW",(0,0),(-1,-1),.35,colors.HexColor("#d9e0dc"))]))
        story.append(t);story.append(Spacer(1,10))
    def pic(name,w=490):
        from PIL import Image as PILImage
        with PILImage.open(OUT/name) as im: iw,ih=im.size
        story.append(Image(str(OUT/name),width=w,height=w*ih/iw));story.append(Spacer(1,8))
    def page():story.append(PageBreak())
    r2022=sensitivity.query("year==2022 and scenario=='baixa_renda_dec'").iloc[0]
    r2024=sensitivity.query("year==2024 and scenario=='baixa_renda_dec'").iloc[0]
    latest=municipal[municipal.year.eq(2024)].sort_values("municipality_id")
    title("RELATÓRIO TÉCNICO · VERSÃO 0.1 · 06 OUT 2026","Energia e Equidade")
    p("Continuidade do fornecimento e desigualdade social na Região Metropolitana de Campinas","Heading1")
    p("Projeto pessoal de portfólio de Lucas Barros Ambrósio<br/>Engenharia elétrica · análise de dados · políticas públicas","Body")
    p("Implementação assistida por IA. Análise exploratória, sem vínculo institucional ou intervenção executada.","Small")
    table([["Território","Base elétrica","Base social"],["20 municípios da RMC","56 conjuntos associados; 2022–2025","Censo 2022: renda e classes de rendimento"]],[160,165,165])
    p("Pergunta de investigação","Heading2")
    p("Áreas com maior proporção de moradores de baixa renda estão associadas a conjuntos elétricos com interrupções mais frequentes ou prolongadas? O estudo integra fontes oficiais, testa a compatibilidade territorial e examina a estabilidade da associação.")
    p("Resultado principal","Heading2")
    p(f"Em 2022, ano alinhado ao Censo, a correlação de Spearman entre baixa renda e mediana do DEC dos conjuntos associados foi <b>{f(r2022.rho,3)}</b>, próxima de zero. Em 2024, foi <b>{f(r2024.rho,3)}</b>. A base não sustenta um padrão territorial simples e estável de pior continuidade em municípios com maior baixa renda.")
    p("Esse resultado <b>não exclui desigualdade dentro dos municípios</b>. Dos 56 conjuntos regionais ativos na análise, 44 estão ligados a mais de um município. Não há informação suficiente para atribuir a cada cidade, bairro ou grupo social a interrupção que efetivamente experimentou.")
    p("Contribuição de engenharia","Heading2")
    p("O produto entrega uma base rastreável, reconstrução anual ajustada por consumidores, validação de séries completas, consultas SQL, mapas e análise de sensibilidade. Para políticas públicas, propõe uma sequência de diagnóstico e coleta de evidência antes de priorizar investimentos.")
    p("Dados elétricos publicados em 05/10/2026; relação territorial publicada em 09/09/2026; dados sociais de 2022. 2024 é o recorte regional recente com cobertura completa; 2025 é suplementar.","Small")
    page()
    title("01 / MÉTODO E CONTROLE DE QUALIDADE","Preservar unidades, períodos e fronteiras")
    p("Os indicadores mensais DEC (h/UC) e FEC (interrupções/UC) são mantidos por conjunto. A referência social é municipal. A unidade elétrica nunca é renomeada como bairro ou município.")
    table([["Etapa","Regra aplicada"],["Aquisição","Fontes oficiais com URL, data UTC e hash SHA-256."],["Validação","Chave única; valores finitos; 12 meses; NumCon positivo; ausências não viram zero."],["Anualização","DEC anual ≈ Σ(DEC mensal × NumCon mensal) / média(NumCon mensal). A mesma expressão vale para FEC."],["Território","Mediana e amplitude dos conjuntos associados; sem pesos municipais inventados."],["Robustez","Renda média/mediana, baixa renda, FEC, conjuntos exclusivos, retirada de um município e coorte temporal fixa."]],[96,394])
    p("Diagnóstico da fotografia utilizada","Heading2")
    table([["Verificação","Resultado"],["Registros mensais selecionados no Brasil",f(diagnostics['monthly_records'],0)],["Registros mensais dos conjuntos associados à RMC",f(diagnostics['regional_monthly_records'],0)],["Conjuntos regionais compartilhados / exclusivos","44 / 12"],["Séries regionais incompletas","3 conjunto-anos, todos em 2025"],["Limite DEC ausente em série regional completa",str(diagnostics['regional_missing_dec_limits_complete'])+" conjunto-anos"]],[350,140])
    incomplete=annual[~annual.complete]
    p("As três séries com 11 meses completos em 2025 são: "+"; ".join(incomplete.set_name.tolist())+". Não são usadas para produzir um número anual. A composição da amostra de 2025 muda; a evolução principal usa também uma coorte fixa.")
    p("Precisão e limites","Heading2")
    p("A reconstrução parte de valores mensais arredondados. Razões frente ao limite servem para triagem e conferência, sem certificar descumprimento regulatório ou compensação. Os componentes expurgados não foram incorporados aos indicadores selecionados. A relação territorial atual aplicada ao passado é uma aproximação.")
    page()
    title("02 / TERRITÓRIO","Dois mapas, duas unidades de observação")
    pic("mapas.png")
    p("À esquerda, proporção municipal de moradores com renda até meio salário mínimo, incluindo sem rendimento, no universo da tabela SIDRA 10296. À direita, mediana do DEC reconstruído dos conjuntos associados ao município em 2024. O segundo mapa não mostra DEC municipal oficial.","Small")
    names=list(latest.municipality)
    table([["Código no mapa","Código no mapa"]]+[[f"{i+1:02d} · {names[i]}",f"{i+11:02d} · {names[i+10]}"] for i in range(10)],[245,245],7.5)
    p("Interpretação territorial","Heading2")
    p("Um conjunto pode atender cidades dentro e fora da RMC. A mediana dos conjuntos não representa o consumidor médio: faltam os números de UCs em cada interseção. Municípios com conjuntos compartilhados não são observações elétricas independentes. Fronteiras da malha municipal também não descrevem a configuração histórica da rede.")
    page()
    title("03 / BASE PARA INSPEÇÃO","Panorama dos 20 municípios")
    p("Renda nominal mensal per capita e baixa renda: 2022. Continuidade: reconstrução de 2024. O intervalo entre conjuntos e os vínculos completos podem ser consultados no relatório interativo e nos CSVs.","Small")
    rows=[["Município","Renda média (R$)","Baixa renda (%)","DEC med. (h)","Conj. / comp.*"]]
    for r in latest.itertuples(): rows.append([r.municipality,f(r.income_mean),f(r.low_income_pct,1),f(r.dec_median),f"{r.n_sets} / {r.n_shared}"])
    table(rows,[170,85,80,72,83],7.6)
    p("* Conjuntos com série completa / quantos são compartilhados com outros municípios. Não representa cobertura populacional. Todas as séries regionais observadas em 2024 estão completas.","Small")
    p("Média e desigualdade","Heading2")
    p("A renda média pode ocultar diferenças internas. Por isso, a análise inclui renda mediana e participação de baixa renda. Não se estima Gini municipal: a tabela 10301 consultada não oferece esse nível territorial. Nenhum índice estadual foi atribuído artificialmente aos municípios.")
    page()
    title("04 / ASSOCIAÇÃO E SENSIBILIDADE","Testar a hipótese sem impor uma conclusão")
    pic("associacao_2022.png")
    p("Números dos pontos correspondem à legenda do mapa. Não se ajusta reta causal. Spearman descreve a associação entre posições relativas dos municípios.","Small")
    rows=[["Ano elétrico","Todos os vínculos: ρ (n=20)","Só exclusivos: ρ (n=7)","Retirada de um município*"]]
    for year in [2022,2023,2024,2025]:
        a=sensitivity.query("year==@year and scenario=='baixa_renda_dec'").iloc[0]
        b=sensitivity.query("year==@year and scenario=='baixa_renda_exclusivos'").iloc[0]
        rows.append([str(year)+( "¹" if year==2025 else ""),f(a.rho,3),f(b.rho,3),f(a.loo_min,3)+" a "+f(a.loo_max,3)])
    table(rows,[80,140,125,145],7.8)
    p("* Faixa de sensibilidade, não intervalo de confiança. ¹ Séries completas disponíveis; cobertura de 2025 reduzida. Renda sempre de 2022. O recorte exclusivo muda a população analisada e não elimina a limitação ecológica.","Small")
    p("O sinal e a intensidade dependem do recorte. Não há base para uma conclusão geral de ausência de desigualdade, nem para uma afirmação de causalidade. Clima, topologia de rede, densidade, ruralidade e investimento não foram controlados. Em especial, sete municípios com conjuntos exclusivos não representam toda a RMC.")
    page()
    title("05 / LEITURA DE ENGENHARIA","Evolução e sinais para conferência técnica")
    pic("evolucao_coorte.png")
    p("Coorte fixa: somente conjuntos completos nos quatro anos. Estatísticas são medianas de conjuntos, não indicadores globais oficiais da ANEEL. O critério pode favorecer conjuntos com melhor informação e não representa automaticamente toda a população.","Small")
    p("Maiores razões DEC reconstruído / limite em 2024","Heading2")
    top=annual[annual.year.eq(2024)&annual.complete].nlargest(5,"dec_limit_ratio")
    rows=[["Conjunto associado à RMC","DEC (h)","Limite (h)","Razão"]]
    for r in top.itertuples():rows.append([r.set_name,f(r.dec_h),f(r.dec_limit),f(r.dec_limit_ratio,3)])
    table(rows,[280,75,75,60])
    p("A identificação acima serve para conferir dados e investigar causas. Conjuntos com nome de cidade externa podem atender também a RMC. Uma razão próxima de 1 não deve ser classificada de modo definitivo a partir de números arredondados.")
    p("Próxima camada técnica","Heading2")
    p("Obter localização e causas de interrupções, configuração de alimentadores, cargas críticas e mudanças cadastrais. Só então avaliar intervenções como manutenção, proteção, automação e contingência. A análise atual não dimensiona equipamentos nem estima retorno financeiro.")
    page()
    title("06 / POLÍTICAS PÚBLICAS","Uma agenda de diagnóstico e proteção")
    p("A contribuição interdisciplinar é conectar desempenho de infraestrutura, condições sociais e capacidade de resposta institucional. As frentes abaixo são propostas para discussão, não intervenções executadas.")
    table([["Frente","Ação proposta","Como acompanhar"],["Dados e transparência","Esclarecer meses ausentes e solicitar UCs por interseção município–conjunto e histórico geográfico.","Completude, rastreabilidade e correções publicadas."],["Confiabilidade","Investigar conjuntos com sinais persistentes, incluindo causas, ativos e contexto climático.","Indicadores verificados, recorrência e tempo de restabelecimento."],["Serviços essenciais","Identificar cargas de saúde, abastecimento e assistência; avaliar planos de continuidade operacional.","Indisponibilidade dos serviços e testes de contingência."],["Vulnerabilidade e participação","Ouvir moradores e prestadores de serviços, com canais acessíveis e dados agregados.","Diversidade da participação, demandas registradas e resolvidas."]],[98,247,145],8.1)
    p("Critérios de decisão","Heading2")
    p("Verificar qualidade da evidência, necessidade do serviço, população efetivamente atendida, alternativas técnicas, custo de ciclo de vida e capacidade de manutenção. Tornar os critérios explícitos e permitir participação dos afetados. Não converter renda e DEC em um ranking automático sem discutir pesos e consequências.")
    p("Avaliação posterior","Heading2")
    p("Uma intervenção futura precisa de resultados definidos previamente, série anterior, área comparável e registro de eventos externos. A melhora após uma ação, isoladamente, não demonstra efeito da política. O desenho desta versão é diagnóstico, não avaliação de impacto.")
    p("Limites sociais","Heading2")
    p("Não foram medidos perdas de alimentos, prejuízo ao trabalho, efeitos em saúde ou acesso a equipamentos de contingência. Esses temas justificam investigação e escuta, mas não aparecem no relatório como danos quantificados.")
    page()
    title("07 / REPRODUÇÃO E APRESENTAÇÃO","Uma base que pode ser auditada e ampliada")
    p("Como reproduzir","Heading2")
    p("O relatório HTML abre diretamente no navegador. Para os cálculos: instalar Python 3.12 e as dependências; executar <b>python -m unittest discover -s tests -v</b>, <b>python -m energia_equidade.build</b> e <b>python -m energia_equidade.report</b>. O snapshot mensal acompanha o projeto; a análise não exige nova coleta.")
    p("A atualização completa é separada: <b>python -m energia_equidade.acquire --refresh</b> e depois <b>python -m energia_equidade.build --extract</b>. Atualizar a narrativa e revisar comparabilidade antes de divulgar uma nova edição.")
    p("O que acompanha a entrega","Heading2")
    p("Código Python, base SQLite, CSVs, malha regional, figuras, relatório interativo, testes automatizados, consultas SQL, metodologia, dicionário de dados, propostas de política pública e guia de apresentação. As fontes têm hashes para auditoria; dados pessoais e materiais internos de empresas não foram utilizados.")
    p("Fontes primárias","Heading2")
    sources=[("ANEEL · indicadores e limites", "https://dadosabertos.aneel.gov.br/dataset/indicadores-coletivos-de-continuidade-dec-e-fec"),
             ("ANEEL · relação conjunto–município", "https://dadosabertos.aneel.gov.br/dataset/indqual-municipio"),
             ("IBGE · renda média e mediana, tabela 10295", "https://sidra.ibge.gov.br/tabela/10295"),
             ("IBGE · classes de renda, tabela 10296", "https://sidra.ibge.gov.br/tabela/10296"),
             ("IBGE · documentação das APIs", "https://servicodados.ibge.gov.br/api/docs/"),
             ("AGEMCAMP · composição regional", "https://dadosabertos.sp.gov.br/organization/about/agencia-metropolitana-de-campinas-agemcamp"),
             ("PNUD · governança energética", "https://www.undp.org/governance/publications/strengthening-energy-governance-systems-energy-governance-framework-just-energy-transition")]
    for label,url in sources:p(f'<link href="{url}" color="#196b66">{label}</link>',"Small")
    p("Portfólio e participação","Heading2")
    p("Antes de inserir o projeto no currículo, Lucas deve executar a análise, conferir exemplos e conseguir explicar resultados e limitações. A implementação assistida por IA não comprova, por si só, domínio individual de programação. A apresentação deve descrever a participação efetiva e não afirmar parceria institucional, responsabilidade técnica profissional ou impacto social que não ocorreu.")
    p("O mérito desta versão está na integração verificável das bases e na explicitação dos limites da evidência. A próxima etapa substantiva é obter dados territorialmente compatíveis e validar o diagnóstico com conhecimento local.")
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor("#d8dfdb"));canvas.line(50,44,A4[0]-50,44)
        canvas.setFont("DVS",7);canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(50,31,"ENERGIA E EQUIDADE · RMC | 06/10/2026 | Estudo exploratório")
        canvas.drawRightString(A4[0]-50,31,str(doc.page))
    doc=SimpleDocTemplate(str(OUT/"Relatorio_Tecnico_Energia_Equidade.pdf"),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=59,
                          title="Energia e Equidade na Região Metropolitana de Campinas",author="Projeto pessoal de Lucas Barros Ambrósio")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)


def main():
    OUT.mkdir(exist_ok=True)
    municipal=read("municipal_context");annual=read("regional_sets");sensitivity=read("sensitivity")
    benchmarks=read("benchmarks");balanced=read("balanced_benchmarks")
    diagnostics=json.loads((DATA/"diagnostics.json").read_text());geo=json.loads((DATA/"rmc.geojson").read_text())
    figures(municipal,sensitivity,balanced,geo)
    pdf(municipal,annual,sensitivity,benchmarks,balanced,diagnostics)
    def records(df):return json.loads(df.to_json(orient="records"))
    content={"municipal":records(municipal),"sensitivity":records(sensitivity),"benchmarks":records(benchmarks),
             "balanced":records(balanced),"geo":geo,"diagnostics":diagnostics}
    template=(Path(__file__).parent/"report_template.html").read_text()
    embedded=json.dumps(content,ensure_ascii=False,allow_nan=False).replace("<","\\u003c")
    (OUT/"Observatorio_Energia_Equidade.html").write_text(template.replace("__DATA__",embedded),encoding="utf-8")
    print("PDF, HTML e figuras gerados.")


if __name__=="__main__": main()
