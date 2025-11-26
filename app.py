import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO


# =======================
# 🎨 MODO DARK PERSONALIZADO
# =======================
st.markdown("""
    <style>
        .stApp {
            background-color: #121212 !important;
        }

        html, body, [class*="css"] {
            color: #E0E0E0 !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1A1A1A !important;
        }

        /* Cards e containers */
        .stMetric, .stAlert, .stDataFrame, .stMarkdown {
            background-color: #1E1E1E !important;
            border-radius: 10px;
            padding: 10px;
        }

        /* Botão */
        .stButton>button {
            background-color: #333333 !important;
            color: #FFFFFF !important;
            border-radius: 8px;
            border: 1px solid #555555;
        }

        .stButton>button:hover {
            background-color: #444444 !important;
            border-color: #777777;
        }

        /* Gráficos */
        .stPlotlyChart {
            background-color: #1E1E1E !important;
            border-radius: 10px;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)


# =======================
# CONFIG
# =======================
st.set_page_config(page_title="Painel Check List EPI", layout="wide")
st.title("🦺 Check List EPI - Técnicos OK x Pendentes")


# =======================
# CARREGAMENTO DOS DADOS
# =======================
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    if "STATUS_CHECK_LIST" in df.columns:
        df["STATUS_CHECK_LIST"] = (
            df["STATUS_CHECK_LIST"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "CHECK LIST OK": "OK",
                "CHECKLIST OK": "OK",
                "OK": "OK",
                "PENDENTE": "PENDENTE"
            })
        )
    else:
        st.warning("⚠️ A coluna 'STATUS_CHECK_LIST' não existe na base.")
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    return df


url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados(url)


# =======================
# 🔍 FILTROS
# =======================
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())

gerente_sel = st.sidebar.selectbox("👩‍💼 Gerente", gerentes)
coord_sel = st.sidebar.selectbox("🧑‍🏭 Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coord_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coord_sel]


# =======================
# 📊 MÉTRICAS
# =======================
total = len(df_filtrado)
qtd_ok = (df_filtrado["STATUS_CHECK_LIST"] == "OK").sum()
qtd_pend = (df_filtrado["STATUS_CHECK_LIST"] == "PENDENTE").sum()
perc_ok = round((qtd_ok / total) * 100, 1) if total > 0 else 0
perc_pend = round((qtd_pend / total) * 100, 1) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("✅ OK", qtd_ok)
col2.metric("⚠️ Pendentes", qtd_pend)
col3.metric("📊 % OK", f"{perc_ok}%")
col4.metric("📉 % Pendentes", f"{perc_pend}%")


# =======================
# 📈 GRÁFICO POR GERENTE
# =======================
if "GERENTE" in df_filtrado.columns:
    cont_ger = df_filtrado.groupby(["GERENTE", "STATUS_CHECK_LIST"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
    
    for col in ["OK", "PENDENTE"]:
        if col not in cont_ger.columns:
            cont_ger[col] = 0
            
    cont_ger["TOTAL"] = cont_ger["OK"] + cont_ger["PENDENTE"]
    cont_ger["% OK"] = (cont_ger["OK"] / cont_ger["TOTAL"] * 100).where(cont_ger["TOTAL"] > 0, 0)
    cont_ger["% PENDENTE"] = (cont_ger["PENDENTE"] / cont_ger["TOTAL"] * 100).where(cont_ger["TOTAL"] > 0, 0)
    
    df_bar_ger = cont_ger.melt(
        id_vars=["GERENTE"],
        value_vars=["% OK", "% PENDENTE"],
        var_name="STATUS",
        value_name="PERCENTUAL"
    )
    df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ", "")

    fig_ger = px.bar(
        df_bar_ger,
        x="GERENTE",
        y="PERCENTUAL",
        color="STATUS",
        text=df_bar_ger["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_map={"OK": "mediumseagreen", "PENDENTE": "tomato"},
        barmode="group",
        title="📈 % OK x % Pendentes por Gerente"
    )

    fig_ger.update_traces(textposition="outside")
    fig_ger.update_layout(
        yaxis_title="Percentual (%)",
        plot_bgcolor="#1E1E1E",
        paper_bgcolor="#121212",
        font_color="white",
        height=350
    )

    st.plotly_chart(fig_ger, use_container_width=True)


# =======================
# 📊 GRÁFICO POR COORDENADOR
# =======================
if "COORDENADOR" in df_filtrado.columns:
    cont_coord = df_filtrado.groupby(["COORDENADOR", "STATUS_CHECK_LIST"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
    
    for col in ["OK", "PENDENTE"]:
        if col not in cont_coord.columns:
            cont_coord[col] = 0

    cont_coord["TOTAL"] = cont_coord["OK"] + cont_coord["PENDENTE"]
    cont_coord["% OK"] = (cont_coord["OK"] / cont_coord["TOTAL"] * 100).where(cont_coord["TOTAL"] > 0, 0)
    cont_coord["% PENDENTE"] = (cont_coord["PENDENTE"] / cont_coord["TOTAL"] * 100).where(cont_coord["TOTAL"] > 0, 0)

    df_bar_coord = cont_coord.melt(
        id_vars=["COORDENADOR"],
        value_vars=["% OK", "% PENDENTE"],
        var_name="STATUS",
        value_name="PERCENTUAL"
    )
    df_bar_coord["STATUS"] = df_bar_coord["STATUS"].str.replace("% ", "")

    fig_coord = px.bar(
        df_bar_coord,
        x="COORDENADOR",
        y="PERCENTUAL",
        color="STATUS",
        text=df_bar_coord["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_map={"OK": "mediumseagreen", "PENDENTE": "tomato"},
        barmode="group",
        title="📊 % OK x % Pendentes por Coordenador"
    )

    fig_coord.update_traces(textposition="outside")
    fig_coord.update_layout(
        yaxis_title="Percentual (%)",
        plot_bgcolor="#1E1E1E",
        paper_bgcolor="#121212",
        font_color="white",
        height=350
    )

    st.plotly_chart(fig_coord, use_container_width=True)


# =======================
# 📋 PENDENTES + DOWNLOAD
# =======================
df_pendentes = df_filtrado[df_filtrado["STATUS_CHECK_LIST"] == "PENDENTE"]

st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS_CHECK_LIST"]])

if not df_pendentes.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_pendentes.to_excel(writer, index=False, sheet_name="Pendentes")
        
    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=output.getvalue(),
        file_name="Pendentes_EPI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.success("🎉 Nenhum pendente encontrado! Tudo OK!")
