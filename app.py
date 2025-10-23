import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 🎨 CONFIGURAÇÃO GERAL
st.set_page_config(page_title="Check List  EPI - Técnicos OK/Pendentes", layout="wide")

# CSS personalizado 💅
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(120deg, #f8fbff, #f3e5f5);
    }
    h1 {
        text-align: center;
        color: #1b5e20;
        font-weight: 800;
        font-size: 2.2rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    .metric-card {
        padding: 13px;
        border-radius: 13px;
        color: white;
        font-weight: bold;
        text-align: center;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: scale(1.05);
    }
    .ok-card {background: linear-gradient(135deg, #2ecc71, #27ae60);}
    .pendente-card {background: linear-gradient(135deg, #e74c3c, #c0392b);}
    .percent-ok-card {background: linear-gradient(135deg, #3498db, #2980b9);}
    .percent-pend-card {background: linear-gradient(135deg, #f1c40f, #f39c12);}
    .stDownloadButton button {
        background-color: #1b5e20;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        box-shadow: 0px 3px 6px rgba(0,0,0,0.2);
    }
    .stDownloadButton button:hover {
        background-color: #43a047;
        transform: scale(1.03);
        transition: 0.2s;
    }
    </style>
""", unsafe_allow_html=True)

# 🧠 TÍTULO
st.title("🦺 Check List EPI - Técnicos OK e Pendentes")

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

with c1:
    st.markdown(f"""
    <div class='metric-card ok-card'>
        <h3>✅ Inspeções OK</h3>
        <h2>{total_ok}</h2>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='metric-card percent-ok-card'>
        <h3>📊 % OK</h3>
        <h2>{perc_ok:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class='metric-card pendente-card'>
        <h3>⚠️ Pendentes</h3>
        <h2>{total_pendente}</h2>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class='metric-card percent-pend-card'>
        <h3>📉 % Pendentes</h3>
        <h2>{perc_pendente:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

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
        title_font=dict(size=18, color="#1b5e20")
    )
    return fig

# 📊 GRÁFICOS
st.plotly_chart(grafico_percentual(df_filtrado, "GERENTE", "📈 Técnicos OK x Pendentes por Gerente"), use_container_width=True)
st.plotly_chart(grafico_percentual(df_filtrado, "COORDENADOR", "📈 Técnicos OK x Pendentes por Coordenador"), use_container_width=True)

# 📦 PRODUTOS
cont_prod = df_filtrado.groupby(["PRODUTO_SIMILAR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_prod.columns:
        cont_prod[col]=0
cont_prod["TOTAL"] = cont_prod["OK"]+cont_prod["PENDENTE"]
cont_prod["% PENDENTE"] = (cont_prod["PENDENTE"]/cont_prod["TOTAL"]*100).where(cont_prod["TOTAL"]>0,0)

fig_prod = px.bar(cont_prod, x="PRODUTO_SIMILAR", y="% PENDENTE",
                  text=cont_prod["% PENDENTE"].apply(lambda x:f"{x:.1f}%"),
                  color_discrete_sequence=["#f39c12"],
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
