import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard de Inspeções EPI", layout="wide", page_icon="🧤")

# ============================
# 🎨 ESTILO E CORES
# ============================
st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    h1, h2, h3, h4, h5 {color: #003366;}
    .stButton>button {
        background-color: #00bfa6;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 0.6em 1.2em;
    }
    .stButton>button:hover {
        background-color: #009e8c;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ============================
# 📥 LEITURA DOS DADOS
# ============================
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url, engine="openpyxl")
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    if "PERSONALIZAR" in df.columns:
        df["PERSONALIZAR"] = (
            df["PERSONALIZAR"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"CHECK LIST OK": "OK", "PENDENTE": "PENDENTE"})
        )

    # Renomeia coluna "PRODUTO_SIMILAR" para "EPI"
    if "PRODUTO_SIMILAR" in df.columns:
        df = df.rename(columns={"PRODUTO_SIMILAR": "EPI"})

    return df

url = st.text_input("🔗 Cole o link do arquivo Excel no GitHub:", "")
if url:
    df = carregar_dados(url)

    st.title("🧤 Dashboard de Inspeções de EPI")
    st.markdown("### Acompanhe o status de inspeções por gerente, coordenador e tipo de EPI.")

    # ============================
    # 🔍 FILTROS
    # ============================
    col1, col2, col3 = st.columns(3)
    gerente_sel = col1.selectbox("👩‍💼 Selecione o Gerente:", ["Todos"] + sorted(df["GERENTE"].dropna().unique().tolist()))
    coord_sel = col2.selectbox("🧑‍🔧 Selecione o Coordenador:", ["Todos"] + sorted(df["COORDENADOR"].dropna().unique().tolist()))
    epi_sel = col3.selectbox("🧤 Selecione o EPI:", ["Todos"] + sorted(df["EPI"].dropna().unique().tolist()))

    df_filtrado = df.copy()
    if gerente_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
    if coord_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coord_sel]
    if epi_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["EPI"] == epi_sel]

    # ============================
    # 📊 FUNÇÃO GENÉRICA DE GRÁFICO
    # ============================
    def grafico_percentual(df, grupo, titulo, cores):
        cont = df.groupby([grupo, "PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
        for col in ["OK", "PENDENTE"]:
            if col not in cont.columns:
                cont[col] = 0
        cont["TOTAL"] = cont["OK"] + cont["PENDENTE"]
        cont["% OK"] = (cont["OK"] / cont["TOTAL"] * 100).where(cont["TOTAL"] > 0, 0)
        cont["% PENDENTE"] = (cont["PENDENTE"] / cont["TOTAL"] * 100).where(cont["TOTAL"] > 0, 0)

        df_bar = cont.melt(id_vars=[grupo], value_vars=["% OK", "% PENDENTE"],
                           var_name="STATUS", value_name="PERCENTUAL")
        df_bar["STATUS"] = df_bar["STATUS"].str.replace("% ", "")

        fig = px.bar(
            df_bar, x=grupo, y="PERCENTUAL", color="STATUS",
            barmode="group", text=df_bar["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
            color_discrete_map=cores, title=titulo
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            yaxis_title="Percentual (%)",
            xaxis_title=grupo,
            xaxis=dict(categoryorder="total descending"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            title_font=dict(size=20, color="#003366", family="Arial Black")
        )
        return fig

    # ============================
    # 🧮 GRÁFICOS COLORIDOS
    # ============================
    cores = {"OK": "#00c853", "PENDENTE": "#ff1744"}

    st.plotly_chart(grafico_percentual(df_filtrado, "GERENTE", "📈 Percentual por Gerente", cores), use_container_width=True)
    st.plotly_chart(grafico_percentual(df_filtrado, "COORDENADOR", "🧭 Percentual por Coordenador", cores), use_container_width=True)
    st.plotly_chart(grafico_percentual(df_filtrado, "EPI", "🧤 Percentual por Tipo de EPI", cores), use_container_width=True)

    # ============================
    # 🚨 TABELA DE PENDENTES
    # ============================
    st.markdown("## 🚨 Pendências de EPI")
    df_pendentes = df_filtrado[df_filtrado["PERSONALIZAR"] == "PENDENTE"]
    st.dataframe(df_pendentes[["TECNICO", "GERENTE", "COORDENADOR", "EPI"]])

    # ============================
    # 💾 DOWNLOAD
    # ============================
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        label="📥 Baixar Pendências (Excel)",
        data=to_excel(df_pendentes),
        file_name="pendencias_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Cole o link do Excel do GitHub para carregar os dados.")
