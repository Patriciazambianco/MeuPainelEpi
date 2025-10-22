import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 🎨 CONFIGURAÇÃO GERAL
st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")

# CSS customizado 💅
st.markdown("""
    <style>
    body {
        background: linear-gradient(120deg, #e3f2fd, #f3e5f5);
    }
    .stApp {
        background: linear-gradient(120deg, #e3f2fd, #f3e5f5);
    }
    h1 {
        text-align: center;
        color: #2e7d32;
        font-weight: bold;
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff, #e8f5e9);
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0px 3px 8px rgba(0,0,0,0.1);
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.03);
        transition: 0.3s;
    }
    .stDownloadButton button {
        background-color: #2e7d32;
        color: white;
        font-weight: bold;
        border-radius: 10px;
    }
    .stDownloadButton button:hover {
        background-color: #1b5e20;
    }
    </style>
""", unsafe_allow_html=True)

# 🧠 TÍTULO
st.title("🦺 **Painel de Inspeções EPI - Técnicos OK e Pendentes**")

# 🚀 FUNÇÃO DE CARGA
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
    df["PERSONALIZAR"] = (
        df["PERSONALIZAR"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"CHECK LIST OK": "OK", "PENDENTE": "PENDENTE"})
    )
    return df

# 🔗 URL
url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados(url)

# 🎯 FILTROS
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())
produtos = ["Todos"] + sorted(df["PRODUTO_SIMILAR"].dropna().unique())

gerente_sel = st.sidebar.selectbox("👩‍💼 Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("🧑‍🏭 Coordenador", coordenadores)
produto_sel = st.sidebar.selectbox("🧰 Produto", produtos)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]
if produto_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["PRODUTO_SIMILAR"] == produto_sel]

# 📈 MÉTRICAS COLORIDAS
total_ok = (df_filtrado["PERSONALIZAR"]=="OK").sum()
total_pendente = (df_filtrado["PERSONALIZAR"]=="PENDENTE").sum()
total_geral = total_ok + total_pendente
perc_ok = total_ok/total_geral*100 if total_geral>0 else 0
perc_pendente = total_pendente/total_geral*100 if total_geral>0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✅ Inspeções OK", total_ok)
c2.metric("📊 % OK", f"{perc_ok:.1f}%")
c3.metric("⚠️ Pendentes", total_pendente)
c4.metric("📊 % Pendentes", f"{perc_pendente:.1f}%")

# 🔄 FUNÇÃO DE GRÁFICO
def grafico_percentual(df, grupo, titulo):
    cont = df.groupby([grupo, "PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
    for col in ["OK", "PENDENTE"]:
        if col not in cont.columns:
            cont[col] = 0
    cont["TOTAL"] = cont["OK"] + cont["PENDENTE"]
    cont["% OK"] = (cont["OK"]/cont["TOTAL"]*100).where(cont["TOTAL"]>0,0)
    cont["% PENDENTE"] = (cont["PENDENTE"]/cont["TOTAL"]*100).where(cont["TOTAL"]>0,0)
    
    df_bar = cont.melt(id_vars=[grupo], value_vars=["% OK", "% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
    df_bar["STATUS"] = df_bar["STATUS"].str.replace("% ","")

    fig = px.bar(df_bar, x=grupo, y="PERCENTUAL", color="STATUS",
                 color_discrete_map={"OK":"#2ecc71","PENDENTE":"#e74c3c"},
                 text=df_bar["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
                 barmode="group", title=titulo)
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Percentual (%)",
        xaxis=dict(categoryorder="total descending"),
        title_font=dict(size=18, color="#2e7d32")
    )
    return fig

# 📊 GRÁFICOS COLORIDOS
st.plotly_chart(grafico_percentual(df_filtrado, "GERENTE", "📈 % Técnicos OK x Pendentes por Gerente"), use_container_width=True)
st.plotly_chart(grafico_percentual(df_filtrado, "COORDENADOR", "📈 % Técnicos OK x Pendentes por Coordenador"), use_container_width=True)

# 📦 PRODUTOS
cont_prod = df_filtrado.groupby(["PRODUTO_SIMILAR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_prod.columns:
        cont_prod[col]=0
cont_prod["TOTAL"] = cont_prod["OK"]+cont_prod["PENDENTE"]
cont_prod["% PENDENTE"] = (cont_prod["PENDENTE"]/cont_prod["TOTAL"]*100).where(cont_prod["TOTAL"]>0,0)

fig_prod = px.bar(cont_prod, x="PRODUTO_SIMILAR", y="% PENDENTE",
                  text=cont_prod["% PENDENTE"].apply(lambda x:f"{x:.1f}%"),
                  color_discrete_sequence=["#e74c3c"],
                  title="🧰 % de Pendências por Produto")
fig_prod.update_traces(textposition='outside')
st.plotly_chart(fig_prod,use_container_width=True)

# 📋 TABELAS
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

df_pendentes = df_filtrado[df_filtrado["PERSONALIZAR"]=="PENDENTE"]
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","PERSONALIZAR"]])

st.download_button("📥 Baixar Pendentes (Excel)", data=to_excel(df_pendentes),
                   file_name="epi_tecnicos_pendentes.xlsx")

df_sem_saldo = df_filtrado[df_filtrado["SALDO_VOLANTE"].isna() | (df_filtrado["SALDO_VOLANTE"].astype(str).str.strip() == "")]
st.markdown("### 📋 Técnicos sem Saldo Volante")
st.dataframe(df_sem_saldo[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","SALDO_VOLANTE"]])

st.download_button("📥 Baixar Técnicos sem Saldo Volante (Excel)", 
                   data=to_excel(df_sem_saldo),
                   file_name="epi_tecnicos_sem_saldo.xlsx")
