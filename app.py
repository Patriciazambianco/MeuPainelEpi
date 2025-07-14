import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# Cor de fundo Verde Menta Pastel
st.markdown(
    """
    <style>
    .stApp {
        background-color: #d0f0c0;
    }
    /* Botão de download piscando - texto branco e fundo azul forte */
    @keyframes blink {
      0% {opacity: 1;}
      50% {opacity: 0.4;}
      100% {opacity: 1;}
    }
    .download-btn {
        font-size:18px; 
        color:#ffffff !important; 
        background-color:#005a9c; 
        padding:10px 15px; 
        border-radius:5px; 
        text-decoration:none !important;
        animation: blink 1.5s infinite;
        display: inline-block;
        margin-bottom: 20px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

    com_data = df[df["DATA_INSPECAO"].notna()]

    ultimas_por_tecnico = (
        com_data
        .sort_values("DATA_INSPECAO")
        .drop_duplicates(subset=["TÉCNICO"], keep="last")
    )

    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]

    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])

    resultado = pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)

    return resultado

def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_pendentes.xlsx" class="download-btn">📥 Baixar Excel Pendentes</a>'
    return href

kpi_css = """
<style>
.kpi-container {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.kpi-box {
    background-color: #007acc;
    color: white;
    border-radius: 10px;
    padding: 20px 30px;
    flex: 1;
    text-align: center;
    box-shadow: 0 4px 6px rgb(0 0 0 / 0.1);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.kpi-box.pending {
    background-color: #f39c12;
}
.kpi-box.percent {
    background-color: #27ae60;
}
.kpi-title {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.kpi-value {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
}
</style>
"""

st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

gerentes = sorted(df_tratado["GERENTE"].dropna().unique())
gerente_sel = st.selectbox("Filtrar por Gerente", ["-- Todos --"] + gerentes)

if gerente_sel != "-- Todos --":
    df_filtrado_ger = df_tratado[df_tratado["GERENTE"] == gerente_sel]
else:
    df_filtrado_ger = df_tratado.copy()

coordenadores = sorted(df_filtrado_ger["COORDENADOR"].dropna().unique())
coordenador_sel = st.multiselect("Filtrar por Coordenador", coordenadores)

df_filtrado = df_filtrado_ger.copy()
if coordenador_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()]

st.markdown(gerar_download_excel(df_pendentes), unsafe_allow_html=True)

total = len(df_filtrado)
pending = df_filtrado["DATA_INSPECAO"].isna().sum()
ok = total - pending
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendente = round(100 - pct_ok, 1)

st.markdown(kpi_css, unsafe_allow_html=True)

kpis_html = f"""
<div class="kpi-container">
    <div class="kpi-box percent">
        <div class="kpi-title">Inspeções OK</div>
        <div class="kpi-value">{ok}</div>
    </div>
    <div class="kpi-box pending">
        <div class="kpi-title">Pendentes</div>
        <div class="kpi-value">{pending}</div>
    </div>
    <div class="kpi-box percent">
        <div class="kpi-title">% OK</div>
        <div class="kpi-value">{pct_ok}%</div>
    </div>
    <div class="kpi-box pending">
        <div class="kpi-title">% Pendentes</div>
        <div class="kpi-value">{pct_pendente}%</div>
    </div>
</div>
"""

st.markdown(kpis_html, unsafe_allow_html=True)

if len(df_filtrado) > 0 and len(coordenadores) > 0:
    df_status_coord = df_filtrado.groupby("COORDENADOR").apply(
        lambda x: pd.Series({
            "Pendentes": x["DATA_INSPECAO"].isna().sum(),
            "OK": x["DATA_INSPECAO"].notna().sum()
        })
    ).reset_index()

    # Calcular porcentagem para cada coordenador
    df_status_coord["Total"] = df_status_coord["OK"] + df_status_coord["Pendentes"]
    df_status_coord["% OK"] = (df_status_coord["OK"] / df_status_coord["Total"] * 100).round(1)
    df_status_coord["% Pendentes"] = (df_status_coord["Pendentes"] / df_status_coord["Total"] * 100).round(1)

    # Preparar dados para gráfico de barras com % OK e % Pendentes
    df_melt = df_status_coord.melt(id_vars="COORDENADOR", value_vars=["% OK", "% Pendentes"],
                                  var_name="Status", value_name="Percentual")

    fig = px.bar(
        df_melt,
        x="COORDENADOR",
        y="Percentual",
        color="Status",
        color_discrete_map={"% OK": "#27ae60", "% Pendentes": "#f39c12"},
        labels={"Percentual": "% das Inspeções", "Status": "Status", "COORDENADOR": "Coordenador"},
        title="Percentual das Inspeções por Coordenador",
        text="Percentual"
    )
    fig.update_layout(barmode="stack", xaxis_tickangle=-45, yaxis=dict(range=[0,100]))
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Selecione um gerente e/ou coordenador para visualizar o gráfico.")

# --- Ajuste na exibição da tabela de pendentes com cor na coluna SALDO SGM TÉCNICO ---

def destacar_saldo(val):
    if pd.isna(val) or val.strip() == "":
        return ""
    if "Não tem no saldo" in val:
        return "background-color: #f8d7da; color: #721c24;"  # vermelho clarinho com texto vermelho escuro
    elif "Tem no saldo" in val:
        return "background-color: #fff3cd; color: #856404;"  # laranja clarinho com texto marrom escuro
    else:
        return ""

colunas_tabela = ["TÉCNICO", "COORDENADOR", "GERENTE", "PRODUTO_SIMILAR", "SALDO SGM TÉCNICO"]

df_pendentes_display = df_pendentes[colunas_tabela].fillna("")

st.markdown("### Pendentes")
st.write(df_pendentes_display.style.applymap(destacar_saldo, subset=["SALDO SGM TÉCNICO"]).hide_index())
