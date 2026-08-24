# TP2 - Desenvolvimento Front-End com Python (com Streamlit)
# Rafael Celestino Tomiazi
# Dados: painel Coronavirus Brasil - https://covid.saude.gov.br/ (botao "Arquivo CSV")
# Para rodar: coloque os arquivos HIST_PAINEL_COVIDBR*.csv dentro da pasta "dados"
# e execute: streamlit run app.py

import glob

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import seaborn as sns
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="TP2 - COVID-19 Brasil", layout="wide")

# so puxo as colunas que entram nos graficos
COLUNAS = [
    "regiao",
    "estado",
    "municipio",
    "coduf",
    "codmun",
    "data",
    "semanaEpi",
    "populacaoTCU2019",
    "casosAcumulado",
    "casosNovos",
    "obitosAcumulado",
    "obitosNovos",
]


@st.cache_data
def carregar_dados():
    arquivos = sorted(glob.glob("dados/*.csv"))
    if not arquivos:
        return None

    partes = []
    for arquivo in arquivos:
        try:
            parte = pd.read_csv(arquivo, sep=";", usecols=COLUNAS, low_memory=False)
        except UnicodeDecodeError:
            # alguns csv vieram em latin-1
            parte = pd.read_csv(
                arquivo, sep=";", usecols=COLUNAS, encoding="latin-1", low_memory=False
            )
        partes.append(parte)

    df = pd.concat(partes, ignore_index=True)
    df["data"] = pd.to_datetime(df["data"])

    ano = df["data"].dt.year.astype(str)
    semana = df["semanaEpi"].fillna(0).astype(int).astype(str).str.zfill(2)
    df["ano_semana"] = ano + "-S" + semana

    # uso a primeira data da semana no eixo dos graficos
    inicio = df.groupby("ano_semana")["data"].min()
    df["inicio_semana"] = df["ano_semana"].map(inicio)

    return df


@st.cache_data
def carregar_coordenadas():
    # o arquivo do Ministerio nao tem latitude e longitude
    url = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
    mun = pd.read_csv(url)
    # gambiarra/ajuste no codigo ibge
    mun["codmun"] = mun["codigo_ibge"] // 10
    return mun[["codmun", "nome", "latitude", "longitude"]]


def linhas_brasil(df):
    return df[df["regiao"] == "Brasil"]


def linhas_estados(df):
    return df[df["estado"].notna() & df["codmun"].isna()]


def linhas_municipios(df):
    return df[df["codmun"].notna() & df["municipio"].notna()]


st.title("COVID-19 no Brasil")
st.write(
    "TP2 da disciplina de Desenvolvimento Front-End com Python. "
    "Os dados sao os do painel Coronavirus Brasil, do Ministerio da Saude."
)

df = carregar_dados()

if df is None:
    st.error(
        "Nao encontrei nenhum CSV na pasta 'dados'. Baixe os arquivos em "
        "https://covid.saude.gov.br/ e coloque nessa pasta antes de rodar o app."
    )
    st.stop()

estados = sorted(linhas_estados(df)["estado"].unique())
regioes = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]

st.caption(
    f"Base carregada com {len(df):,} registros, de {df['data'].min():%d/%m/%Y} "
    f"a {df['data'].max():%d/%m/%Y}.".replace(",", ".")
)

# ----------------------------------------------------------------------
# Exercicio 1 - Importancia da visualizacao de dados
# ----------------------------------------------------------------------
st.header("1. A importancia da visualizacao de dados na pandemia")
st.write("Os arquivos tem muita coisa e uma tabela enorme nao mostra facilmente as ondas da pandemia.")
st.markdown(
    """
Na minha leitura, o grafico ajuda principalmente em tres pontos:

- **Comparar as ondas:** fica mais simples ver os picos e as quedas.
- **Ajudar nas decisoes:** gestores podem pensar em leitos, testes e vacinas.
- **Comunicar melhor:** a populacao entende mais rapido se os casos estao subindo.

Tambem tem que tomar cuidado com escala, dado acumulado e diferenca de populacao entre estados.
"""
)

# ----------------------------------------------------------------------
# Exercicio 2 - Grafico de barras com Streamlit
# ----------------------------------------------------------------------
st.header("2. Casos novos por semana epidemiologica (grafico de barras)")

uf_barras = st.selectbox("Estado", estados, index=estados.index("SP"), key="ex2")

base_estado = linhas_estados(df)
casos_semana = (
    base_estado[base_estado["estado"] == uf_barras]
    .groupby("inicio_semana")["casosNovos"]
    .sum()
)

st.bar_chart(casos_semana)

st.write(
    f"""
Deixei Sao Paulo como opcao inicial porque e o estado mais populoso e tem muitos registros. As ondas
ficam bem visiveis, principalmente o pico do comeco de 2022. Estado selecionado: {uf_barras}.
"""
)

# ----------------------------------------------------------------------
# Exercicio 3 - Grafico de linha com Streamlit
# ----------------------------------------------------------------------
st.header("3. Obitos acumulados no Brasil (grafico de linha)")

# acumulado nao se soma: pego o maior valor da semana
obitos_acumulados = (
    linhas_brasil(df).groupby("inicio_semana")["obitosAcumulado"].max()
)

st.line_chart(obitos_acumulados)

st.write(
    """
A curva acumulada nao volta para baixo. Por isso, o mais importante e observar a inclinacao: uma
subida forte representa mais mortes naquele periodo. Usei o maior valor da semana porque somar
valores acumulados deixaria o resultado errado.
"""
)
st.caption("Resumo: linha subindo mais rapido = mais obitos novos naquele periodo.")

# ----------------------------------------------------------------------
# Exercicio 4 - Grafico de area com Streamlit
# ----------------------------------------------------------------------
st.header("4. Casos acumulados em tres estados (grafico de area)")

tres_estados = st.multiselect(
    "Escolha tres estados",
    estados,
    default=["SP", "RJ", "AM"],
    key="ex4",
)

if len(tres_estados) == 0:
    st.info("Selecione pelo menos um estado.")
else:
    comparacao = (
        base_estado[base_estado["estado"].isin(tres_estados)]
        .groupby(["inicio_semana", "estado"])["casosAcumulado"]
        .max()
        .reset_index()
        .pivot(index="inicio_semana", columns="estado", values="casosAcumulado")
    )
    st.area_chart(comparacao)

st.write(
    """
Escolhi Sao Paulo, Rio de Janeiro e Amazonas para comparar estados de tamanhos diferentes. Sao Paulo
fica bem acima por ter mais habitantes, enquanto o Amazonas aparece em uma escala menor. Esse e o
limite do acumulado: ele mostra volume, mas nao mede sozinho a gravidade. Para isso, o tamanho da
populacao tambem precisa entrar na conta.
"""
)

# ----------------------------------------------------------------------
# Exercicio 5 - Mapa com st.map
# ----------------------------------------------------------------------
st.header("5. Casos acumulados por municipio (st.map)")

uf_mapa = st.selectbox("Estado do mapa", estados, index=estados.index("RJ"), key="ex5")

coordenadas = carregar_coordenadas()
ultima_data = df["data"].max()

municipios = linhas_municipios(df)
municipios_uf = municipios[
    (municipios["estado"] == uf_mapa) & (municipios["data"] == ultima_data)
]
mapa_uf = municipios_uf.merge(coordenadas, on="codmun", how="inner")
# o st.map espera o tamanho em metros, uso raiz quadrada pra cidade grande nao virar um borrao
mapa_uf["tamanho"] = (mapa_uf["casosAcumulado"] ** 0.5) * 20

if mapa_uf.empty:
    st.warning("Nao consegui cruzar os municipios desse estado com as coordenadas.")
else:
    st.map(mapa_uf, latitude="latitude", longitude="longitude", size="tamanho")

st.write(
    """
O mapa mostra onde os casos estao concentrados. No Rio de Janeiro, a capital e a regiao metropolitana
ficam com os maiores pontos. Isso ajuda a perceber a distribuicao espacial e a planejar atendimento,
mas o tamanho do ponto e absoluto: cidades grandes naturalmente aparecem mais.
"""
)
st.caption("Neste mapa, ponto maior significa mais casos acumulados, e nao necessariamente maior risco.")

# ----------------------------------------------------------------------
# Exercicio 6 - Matplotlib
# ----------------------------------------------------------------------
st.header("6. Casos novos x obitos novos por estado na ultima semana (Matplotlib)")

ultima_semana = df["ano_semana"].max()
semana_estados = (
    base_estado[base_estado["ano_semana"] == ultima_semana]
    .groupby("estado")[["casosNovos", "obitosNovos"]]
    .sum()
    .sort_values("casosNovos", ascending=False)
)

fig, ax = plt.subplots(figsize=(11, 5))
posicoes = range(len(semana_estados))
largura = 0.4
ax.bar(
    [p - largura / 2 for p in posicoes],
    semana_estados["casosNovos"],
    width=largura,
    label="Casos novos",
)
ax.bar(
    [p + largura / 2 for p in posicoes],
    semana_estados["obitosNovos"],
    width=largura,
    label="Obitos novos",
)
ax.set_xticks(list(posicoes))
ax.set_xticklabels(semana_estados.index, rotation=90)
ax.set_ylabel("Quantidade")
ax.set_title(f"Semana epidemiologica {ultima_semana}")
ax.legend()
st.pyplot(fig)

st.write(
    f"""
Na semana {ultima_semana}, os casos novos sao muito maiores que os obitos novos, por isso as barras
de obitos quase somem nessa escala. Os estados com mais casos costumam ter mais obitos, mas a proporcao
muda entre eles. Tambem vale lembrar que a semana mais recente pode estar incompleta por causa do
atraso nas notificacoes.
"""
)
st.markdown("**O que eu observei:** casos e obitos caminham na mesma direcao, mas nao na mesma proporcao.")

# ----------------------------------------------------------------------
# Exercicio 7 - Boxplot com Seaborn
# ----------------------------------------------------------------------
st.header("7. Distribuicao dos casos novos por regiao (Seaborn)")

tres_regioes = ["Norte", "Nordeste", "Sudeste"]
por_regiao = (
    base_estado[base_estado["regiao"].isin(tres_regioes)]
    .groupby(["regiao", "ano_semana"])["casosNovos"]
    .sum()
    .reset_index()
)

fig2, ax2 = plt.subplots(figsize=(8, 5))
sns.boxplot(data=por_regiao, x="regiao", y="casosNovos", order=tres_regioes, ax=ax2)
ax2.set_xlabel("Regiao")
ax2.set_ylabel("Casos novos na semana")
st.pyplot(fig2)

st.write(
    """
O boxplot compara a distribuicao das semanas, nao uma linha do tempo. O Sudeste tem mais casos e uma
variacao maior, enquanto Norte e Nordeste ficam em valores menores. Os pontos acima das caixas sao
semanas de pico. Como as populacoes sao diferentes, isso representa quantidade absoluta e nao risco
individual.
"""
)

# ----------------------------------------------------------------------
# Exercicio 8 - Grafico de area com Altair
# ----------------------------------------------------------------------
st.header("8. Casos novos por semana em uma regiao (Altair)")

regiao_area = st.selectbox("Regiao", regioes, index=2, key="ex8")

serie_regiao = (
    base_estado[base_estado["regiao"] == regiao_area]
    .groupby("inicio_semana")["casosNovos"]
    .sum()
    .reset_index()
)

area = (
    alt.Chart(serie_regiao)
    .mark_area(opacity=0.7)
    .encode(
        x=alt.X("inicio_semana:T", title="Semana epidemiologica"),
        y=alt.Y("casosNovos:Q", title="Casos novos"),
        tooltip=["inicio_semana:T", "casosNovos:Q"],
    )
    .properties(height=350)
)
st.altair_chart(area, use_container_width=True)

st.write(
    """
Deixei o Sudeste como padrao porque e a regiao onde moro e a serie tem muitos registros. Aparecem
ondas bem separadas, com um pico maior no comeco de 2022. Depois de 2023 os valores ficam menores.
"""
)
st.markdown(
    """
**O que da para notar no grafico:**

- as ondas nao acontecem todas com a mesma intensidade;
- o pico de 2022 se destaca bastante;
- o tooltip mostra o valor exato de cada semana.
"""
)

# ----------------------------------------------------------------------
# Exercicio 9 - Heatmap de correlacao com Altair
# ----------------------------------------------------------------------
st.header("9. Correlacao entre indicadores em um estado (Altair)")

st.info(
    "O arquivo do painel Coronavirus Brasil nao traz leitos hospitalares ocupados, "
    "entao usei as colunas que existem na base: casos e obitos, novos e acumulados."
)

uf_heat = st.selectbox("Estado", estados, index=estados.index("SP"), key="ex9")

base_heat = (
    base_estado[base_estado["estado"] == uf_heat]
    .groupby("ano_semana")
    .agg(
        casosNovos=("casosNovos", "sum"),
        obitosNovos=("obitosNovos", "sum"),
        casosAcumulado=("casosAcumulado", "max"),
        obitosAcumulado=("obitosAcumulado", "max"),
    )
)

correlacao = base_heat.corr().reset_index().melt(id_vars="index")
correlacao.columns = ["variavel_x", "variavel_y", "correlacao"]

heat = (
    alt.Chart(correlacao)
    .mark_rect()
    .encode(
        x=alt.X("variavel_x:N", title=""),
        y=alt.Y("variavel_y:N", title=""),
        color=alt.Color("correlacao:Q", scale=alt.Scale(scheme="blueorange", domain=[-1, 1])),
        tooltip=["variavel_x", "variavel_y", alt.Tooltip("correlacao:Q", format=".2f")],
    )
    .properties(height=320)
)
texto = heat.mark_text(baseline="middle").encode(
    text=alt.Text("correlacao:Q", format=".2f"),
    color=alt.value("black"),
)
st.altair_chart(heat + texto, use_container_width=True)

st.write(
    """
A correlacao entre os acumulados costuma ser alta porque as duas series so crescem. Entre casos novos
e obitos novos, ela tende a ser menor, ja que o obito pode ser notificado semanas depois. Correlacao
alta tambem nao quer dizer que uma coisa causou a outra.
"""
)
st.caption("Nesse caso, o heatmap ajuda a comparar os indicadores, mas nao prova uma relacao de causa.")

# ----------------------------------------------------------------------
# Exercicio 10 - Grafico de pizza com Plotly
# ----------------------------------------------------------------------
st.header("10. Distribuicao dos casos acumulados por regiao (Plotly)")

ultimo_por_estado = (
    base_estado.sort_values("data").groupby("estado").tail(1)
)
por_regiao_total = (
    ultimo_por_estado.groupby("regiao")["casosAcumulado"].sum().reset_index()
)

pizza = px.pie(
    por_regiao_total,
    names="regiao",
    values="casosAcumulado",
    title="Casos acumulados por regiao",
)
pizza.update_traces(textinfo="percent+label")
st.plotly_chart(pizza, use_container_width=True)

st.write(
    """
O Sudeste fica com a maior fatia, seguido por Nordeste e Sul. Isso combina com a concentracao da
populacao e das cidades grandes nessas regioes. A pizza mostra a carga absoluta de casos, nao o risco
por habitante.
"""
)
st.caption("A comparacao mudaria bastante se eu calculasse casos por 100 mil habitantes.")

# ----------------------------------------------------------------------
# Exercicio 11 - Subplots com Plotly
# ----------------------------------------------------------------------
st.header("11. Comparacao entre duas regioes (subplots com Plotly)")

col_a, col_b = st.columns(2)
regiao_a = col_a.selectbox("Primeira regiao", regioes, index=2, key="ex11a")
regiao_b = col_b.selectbox("Segunda regiao", regioes, index=0, key="ex11b")


def serie_semanal(regiao):
    return (
        base_estado[base_estado["regiao"] == regiao]
        .groupby("inicio_semana")[["casosNovos", "obitosNovos"]]
        .sum()
        .reset_index()
    )


serie_a = serie_semanal(regiao_a)
serie_b = serie_semanal(regiao_b)

sub = make_subplots(rows=1, cols=2, subplot_titles=(regiao_a, regiao_b))
sub.add_trace(
    go.Bar(x=serie_a["inicio_semana"], y=serie_a["casosNovos"], name="Casos novos"),
    row=1,
    col=1,
)
sub.add_trace(
    go.Bar(x=serie_a["inicio_semana"], y=serie_a["obitosNovos"], name="Obitos novos"),
    row=1,
    col=1,
)
sub.add_trace(
    go.Bar(
        x=serie_b["inicio_semana"],
        y=serie_b["casosNovos"],
        name="Casos novos",
        showlegend=False,
    ),
    row=1,
    col=2,
)
sub.add_trace(
    go.Bar(
        x=serie_b["inicio_semana"],
        y=serie_b["obitosNovos"],
        name="Obitos novos",
        showlegend=False,
    ),
    row=1,
    col=2,
)
sub.update_layout(barmode="group", height=420)
st.plotly_chart(sub, use_container_width=True)

st.write(
    f"""
Comparei {regiao_a} e {regiao_b} lado a lado. A diferenca de escala aparece logo, mas as ondas ficam
em periodos parecidos. As barras de obitos sao pequenas na mesma escala dos casos, entao nao da para
comparar bem os dois indicadores visualmente.
"""
)

# ----------------------------------------------------------------------
# Exercicio 12 - Mapa interativo com PyDeck
# ----------------------------------------------------------------------
st.header("12. Casos por 100 mil habitantes (PyDeck)")

regiao_deck = st.selectbox("Regiao do mapa", regioes, index=2, key="ex12")

mun_regiao = municipios[
    (municipios["regiao"] == regiao_deck) & (municipios["data"] == ultima_data)
].merge(coordenadas, on="codmun", how="inner")

mun_regiao = mun_regiao[mun_regiao["populacaoTCU2019"] > 0].copy()
mun_regiao["casos_por_100mil"] = (
    mun_regiao["casosAcumulado"] / mun_regiao["populacaoTCU2019"] * 100000
)

if mun_regiao.empty:
    st.warning("Nao ha dados de municipio para essa regiao na ultima data da base.")
else:
    camada = pdk.Layer(
        "ColumnLayer",
        data=mun_regiao,
        get_position=["longitude", "latitude"],
        get_elevation="casos_por_100mil",
        elevation_scale=30,
        radius=4000,
        get_fill_color=[200, 60, 60, 160],
        pickable=True,
    )
    visao = pdk.ViewState(
        latitude=mun_regiao["latitude"].mean(),
        longitude=mun_regiao["longitude"].mean(),
        zoom=4.5,
        pitch=45,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[camada],
            initial_view_state=visao,
            tooltip={"text": "{municipio}\ncasos por 100 mil: {casos_por_100mil}"},
        )
    )

st.write(
    """
Aqui usei casos por 100 mil habitantes, e nao o numero bruto. Assim, algumas cidades pequenas aparecem
mais altas e as capitais deixam de dominar sozinhas. A densidade pode facilitar a transmissao por causa
de transporte e aglomeracao, mas ela nao explica tudo: testagem, turismo e acesso a atendimento tambem
interferem no resultado.
"""
)
st.markdown(
    """
**Leitura rapida do mapa:**

- coluna alta: mais casos proporcionalmente;
- cidade grande nem sempre sera a primeira;
- outros fatores, como testagem e turismo, tambem pesam.
"""
)
