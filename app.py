import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# Estilo visual
st.markdown("""
    <style>
    .stApp { background-color: #d0f0c0; }
    @keyframes blink {
      0% {opacity: 1;}
      50% {opacity: 0.4;}
      100% {opacity: 1;}
    }
    .download-btn {
        font-size:18px; color:#fff !important; background-color:#005a9c;
        padding:10px 15px; border-radius:5px; text-decoration:none !important;
        animation: blink 1.5s infinite; display: inline-block; margin-bottom: 20px; font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
    tecnicos_com_inspecao = ultimas["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]
    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])
    return pd.concat([ultimas, sem_data_unicos], ignore_index=True)

def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    b64 = base64.b64encode(output.getvalue()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_pendentes.xlsx" class="download-btn">📥 Baixar Excel Pendentes</a>'

st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# Filtros
gerentes = sorted(df_tratado["GERENTE"].dropna().unique())
gerente_sel = st.selectbox("Filtrar por Gerente", ["-- Todos --"] + gerentes)

df_filtrado_ger = df_tratado if gerente_sel == "-- Todos --" else df_tratado[df_tratado["GERENTE"] == gerente_sel]

coordenadores = sorted(df_filtrado_ger["COORDENADOR"].dropna().unique())
coordenador_sel = st.multiselect("Filtrar por Coordenador", coordenadores)

df_filtrado = df_filtrado_ger if not coordenador_sel else df_filtrado_ger[df_filtrado_ger["COORDENADOR"].isin(coordenador_sel)]

df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()]
df_pendentes["SALDO SGM TÉCNICO"] = df_pendentes["SALDO SGM TÉCNICO"].fillna("Não tem no saldo")

st.markdown(gerar_download_excel(df_pendentes), unsafe_allow_html=True)

# KPIs
total = len(df_filtrado)
ok = df_filtrado["DATA_INSPECAO"].notna().sum()
pending = total - ok
pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = 100 - pct_ok

st.markdown("""
<style>
.kpi-container {
    display: flex; gap: 1rem; margin-top: 1rem;
}
.kpi-box {
    flex: 1;
    background: #005a9c;
    color: white;
    padding: 1rem;
    border-radius: 10px;
    font-size: 1.3rem;
    text-align: center;
}
.kpi-box.orange { background: #f39c12; }
.kpi-box.green { background: #27ae60; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-container">
  <div class="kpi-box green">✔️ OK: {ok}</div>
  <div class="kpi-box orange">⚠️ Pendentes: {pending}</div>
  <div class="kpi-box green">✅ % OK: {pct_ok}%</div>
  <div class="kpi-box orange">❌ % Pendentes: {pct_pend}%</div>
</div>
""", unsafe_allow_html=True)

# Gráfico
if len(df_filtrado) and len(coordenadores):
    df_status = df_filtrado.groupby("COORDENADOR").apply(lambda x: pd.Series({
        "OK": x["DATA_INSPECAO"].notna().sum(),
        "Pendentes": x["DATA_INSPECAO"].isna().sum()
    })).reset_index()

    df_status["% OK"] = round(df_status["OK"] / (df_status["OK"] + df_status["Pendentes"]) * 100, 1)
    df_status["% Pendentes"] = 100 - df_status["% OK"]
    df_plot = df_status.melt(id_vars="COORDENADOR", value_vars=["% OK", "% Pendentes"], var_name="Status", value_name="Percentual")

    fig = px.bar(df_plot, x="COORDENADOR", y="Percentual", color="Status",
                 color_discrete_map={"% OK": "#27ae60", "% Pendentes": "#f39c12"},
                 text="Percentual", barmode="stack", title="% Inspeções por Coordenador")
    fig.update_traces(texttemplate='%{text}%', textposition="inside")
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Selecione um gerente e coordenador para visualizar o gráfico.")

# Tabela sem a coluna SALDO SGM TÉCNICO
st.write("### Técnicos Pendentes")
colunas = ["TÉCNICO", "FUNCAO", "PRODUTO_SIMILAR", "SUPERVISOR"]
st.dataframe(df_pendentes[colunas].fillna(""), use_container_width=True)
