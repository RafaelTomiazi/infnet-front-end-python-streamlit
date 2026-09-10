# TP3 - Desenvolvimento Front-End com Python (Streamlit)
# Rafael Celestino Tomiazi - Infnet
# Dados: portal Data.Rio, secao Turismo (Tabela 3665 - visitantes do Parque Nacional da Tijuca)
# rodar com: streamlit run app_tp3_rafael_tomiazi.py

import io
import time

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="TP3 - Turismo Data.Rio", layout="wide")

MESES = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


# pega os nomes das abas do arquivo (cada aba e um ano). tiro a aba de mapa
# que vem junto no arquivo do Data.Rio e nao tem dado nenhum.
@st.cache_data
def listar_abas(conteudo):
    xls = pd.ExcelFile(io.BytesIO(conteudo))
    return [a for a in xls.sheet_names if a != "ESRI_MAPINFO_SHEET"]


# item 8 - cache pra nao reprocessar a planilha a cada clique
# aqui e onde eu limpo o arquivo, porque ele vem bem baguncado do site:
# tem umas linhas de titulo em cima, celulas vazias no meio e ... no lugar
# de numero que falta.
@st.cache_data
def carregar_aba(conteudo, aba):
    bruto = pd.read_excel(io.BytesIO(conteudo), sheet_name=aba, header=None)

    # os dados de verdade comecam na linha 7 (as de cima sao titulo e cabecalho)
    dados = bruto.iloc[7:, :16].copy()
    dados.columns = ["Setor", "Segmento", "Categoria", "Total"] + MESES

    # o site usa ... quando o numero nao existe, troco por vazio
    dados = dados.replace("...", pd.NA)

    # as colunas Setor e Segmento vem com celula mesclada, entao so a primeira
    # linha do grupo tem o nome. o ffill copia o nome pra baixo ate mudar.
    dados["Setor"] = dados["Setor"].ffill()
    dados["Segmento"] = dados["Segmento"].ffill()

    # transformo os meses em numero
    for m in MESES:
        dados[m] = pd.to_numeric(dados[m], errors="coerce")

    # o Total do arquivo as vezes vem vazio, entao refaco somando os 12 meses
    dados["Total"] = dados[MESES].sum(axis=1)

    # tiro linhas sem categoria (sao as linhas de subtotal e as vazias)
    dados = dados.dropna(subset=["Categoria"])
    dados = dados[dados["Categoria"].astype(str).str.strip() != ""]

    return dados.reset_index(drop=True)


def virar_excel(df):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()


# item 9 - session state: crio os valores padrao aqui pra guardar as escolhas
# do usuario (cores e filtros). assim eles nao somem quando a pagina recarrega.
padrao = {
    "cor_fundo": "#FFFFFF",
    "cor_fonte": "#000000",
    "setor_filtro": "Todos",
    "usar_faixa": False,
}
for chave, valor in padrao.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


st.title("Visitantes do Parque Nacional da Tijuca - Rio de Janeiro")

# item 1 - objetivo e motivacao
st.header("1. Objetivo e motivacao")
st.write(
    "Peguei no Data.Rio a tabela de numero de visitantes do Parque Nacional da Tijuca, na parte de "
    "turismo. Escolhi ela porque a Tijuca (Corcovado, Floresta da Tijuca, Pedra Bonita) e um dos "
    "cartoes postais do Rio e recebe muito turista, entao os numeros de visitantes ajudam a ver como "
    "o turismo se comporta ao longo do ano."
)
st.write(
    "A ideia do painel e deixar a pessoa explorar esses dados sem abrir a planilha, que ainda por cima "
    "vem meio baguncada do site. Da pra escolher o ano, filtrar por setor, ordenar a tabela, ver "
    "graficos e baixar so a parte que interessa. O painel ja faz a limpeza do arquivo na hora de ler."
)

# item 2 - upload do arquivo
st.header("2. Upload do arquivo")
arquivo = st.file_uploader("Envie o arquivo XLSX da tabela 3665 (Data.Rio)", type=["xls", "xlsx"])

if arquivo is None:
    st.info("Envie o arquivo pra continuar.")
    st.stop()

conteudo = arquivo.getvalue()
abas = listar_abas(conteudo)

# escolha do ano (cada aba do arquivo e um ano)
ano = st.selectbox("Ano", abas, index=len(abas) - 1)

# item 6 - barra de progresso e spinner enquanto le o arquivo
# o arquivo e pequeno e carrega quase na hora, entao coloco um sleep so pra
# dar tempo do spinner e da barra aparecerem na tela.
with st.spinner("Lendo e limpando o arquivo..."):
    barra = st.progress(0)
    for i in range(0, 100, 25):
        time.sleep(0.15)
        barra.progress(i + 25)
    df = carregar_aba(conteudo, ano)
barra.empty()
st.success(f"Ano {ano} carregado: {df.shape[0]} linhas depois da limpeza.")

# item 7 - color picker pra mudar as cores da pagina
st.sidebar.header("Cores")
st.session_state["cor_fundo"] = st.sidebar.color_picker("Fundo", st.session_state["cor_fundo"])
st.session_state["cor_fonte"] = st.sidebar.color_picker("Fonte", st.session_state["cor_fonte"])

# alem do fundo, forco a cor nos textos dos titulos, labels e filtros. sem isso
# o texto dos filtros (radio, checkbox) pega a cor do tema e some quando o fundo
# fica claro.
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {st.session_state['cor_fundo']}; }}
    .stApp, .stApp p, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3 {{
        color: {st.session_state['cor_fonte']};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# item 3 - tres filtros: dropdown, radio e checkbox
# uso key= nos filtros pra que o Streamlit guarde a escolha no session state
# e ela continue valendo quando a pagina recarregar.
st.header("3. Filtros")
df_filtrado = df.copy()

# dropdown pra escolher quais colunas aparecem
colunas = st.multiselect(
    "Colunas pra mostrar", df.columns.tolist(), default=df.columns.tolist(), key="colunas_filtro"
)

# radio pra filtrar por setor
setores = ["Todos"] + sorted(df["Setor"].dropna().unique().tolist())
setor = st.radio("Setor", setores, horizontal=True, key="setor_filtro")
if setor != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Setor"] == setor]

# checkbox pra ligar um filtro pela quantidade total de visitantes
if st.checkbox("Filtrar por faixa de visitantes (Total)", key="usar_faixa"):
    mn = int(df["Total"].min())
    mx = int(df["Total"].max())
    faixa = st.slider("Faixa de Total", mn, mx, (mn, mx))
    df_filtrado = df_filtrado[(df_filtrado["Total"] >= faixa[0]) & (df_filtrado["Total"] <= faixa[1])]

if colunas:
    df_filtrado = df_filtrado[colunas]

# item 4 - tabela (da pra ordenar clicando no titulo da coluna)
st.header("4. Tabela")
st.write("Clique no nome da coluna pra ordenar.")
st.dataframe(df_filtrado, use_container_width=True)

# item 5 - download do que esta filtrado
st.header("5. Download")
c1, c2 = st.columns(2)
c1.download_button("Baixar XLSX", virar_excel(df_filtrado), "tijuca_filtrado.xlsx")
c2.download_button("Baixar CSV", df_filtrado.to_csv(index=False).encode("utf-8"), "tijuca_filtrado.csv")

# item 12 - metricas
st.header("6. Metricas")
num_agora = df_filtrado.select_dtypes(include="number").columns.tolist()
m1, m2, m3 = st.columns(3)
m1.metric("Registros", len(df_filtrado))
if "Total" in df_filtrado.columns:
    m2.metric("Media de visitantes", f"{df_filtrado['Total'].mean():,.0f}")
    m3.metric("Soma de visitantes", f"{df_filtrado['Total'].sum():,.0f}")

# item 10 - graficos simples (barra, linha, pizza)
st.header("7. Graficos simples")
if len(df_filtrado) > 0 and "Total" in df_filtrado.columns:
    # barra: total de visitantes por setor
    por_setor = df_filtrado.groupby("Setor")["Total"].sum().reset_index()
    st.subheader("Visitantes por setor (barras)")
    st.plotly_chart(px.bar(por_setor, x="Setor", y="Total"), use_container_width=True)

    # linha: total mes a mes (somando tudo que esta filtrado)
    meses_presentes = [m for m in MESES if m in df_filtrado.columns]
    if meses_presentes:
        por_mes = df_filtrado[meses_presentes].sum().reset_index()
        por_mes.columns = ["Mes", "Visitantes"]
        st.subheader("Visitantes por mes (linha)")
        st.plotly_chart(px.line(por_mes, x="Mes", y="Visitantes"), use_container_width=True)

    # pizza: participacao de cada setor
    st.subheader("Participacao por setor (pizza)")
    st.plotly_chart(px.pie(por_setor, names="Setor", values="Total"), use_container_width=True)

# item 11 - graficos avancados (histograma e scatter)
st.header("8. Graficos avancados")
if len(df_filtrado) > 0 and "Total" in df_filtrado.columns:
    st.subheader("Distribuicao do Total (histograma)")
    st.plotly_chart(px.histogram(df_filtrado, x="Total"), use_container_width=True)

    meses_presentes = [m for m in MESES if m in df_filtrado.columns]
    if len(meses_presentes) >= 2:
        st.subheader("Comparacao entre dois meses (scatter)")
        cx, cy = st.columns(2)
        x_s = cx.selectbox("Mes X", meses_presentes, index=0, key="sx")
        y_s = cy.selectbox("Mes Y", meses_presentes, index=1, key="sy")
        st.plotly_chart(px.scatter(df_filtrado, x=x_s, y=y_s, hover_name="Categoria"),
                        use_container_width=True)
