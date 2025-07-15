import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# Estilos CSS personalizados
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

def filtrar_ultimas_inspecoes(df):
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
        workbook = writer.book
        worksheet = writer.sheets["Pendentes"]
        col_idx = df.columns.get_loc("SALDO SGM TÉCNICO")
        for row_num, val in enumerate(df["SALDO SGM TÉCNICO"], start=1):
            val_lower = str(val).strip().lower()
            if val_lower == "tem no saldo":
                fmt = workbook.add_format({'bg_color': '#fce5cd', 'font_color': '#b26a00'})
            elif val_lower in ["não tem no saldo", "nao tem no saldo"]:
                fmt = workbook.add_format({'bg_color': '#f8d7da', 'font_color': '#842029'})
            else:
                fmt = None
            worksheet.write(row_num, col_idx, val, fmt)
    dados = output.getvalue()
    b64 = base64.b64encode(dados).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_pendentes.xlsx" class="download-btn">📥 Baixar Excel Pendentes</a>'
    return href

def destaque_saldo(val):
    val_lower = str(val).strip().lower()
    if val_lower == "tem no saldo":
        return "background-color:#fce5cd; color:#b26a00; font-weight:bold;"
    elif val_lower in ["não tem no saldo", "nao tem no saldo"]:
        return "background-color:#f8d7da; color:#842029; font-weight:bold;"
    return ""

# --- App ---
st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes(df_raw)

# Filtros
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

# Pendentes
df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()].copy()
df_pendentes["SALDO SGM TÉCNICO"] = df_pendentes["SALDO SGM TÉCNICO"].fillna("Não tem no saldo").astype(str)

# Download
st.markdown(gerar_download_excel(df_pendentes), unsafe_allow_html=True)

# KPIs
total = len(df_filtrado)
pend = df_pendentes.shape[0]
ok = total - pend
pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = 100 - pct_ok

st.markdown("""
<style>
.kpi-container { display: flex; gap: 1rem; margin-top: 1rem; }
.kpi-box {
    flex: 1; padding: 1rem 1.5rem; border-radius: 10px;
    background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
}
.kpi-title { font-size: 1rem; color: #666; margin-bottom: 0.5rem; }
.kpi-value { font-size: 2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-container">
  <div class="kpi-box"><div class="kpi-title">Total OK</div><div class="kpi-value">{ok}</div></div>
  <div class="kpi-box"><div class="kpi-title">Pendentes</div><div class="kpi-value">{pend}</div></div>
  <div class="kpi-box"><div class="kpi-title">% OK</div><div class="kpi-value">{pct_ok}%</div></div>
  <div class="kpi-box"><div class="kpi-title">% Pendentes</div><div class="kpi-value">{pct_pend}%</div></div>
</div>
""", unsafe_allow_html=True)

# Gráfico por coordenador
if not df_pendentes.empty:
    df_coord = df_filtrado.groupby("COORDENADOR").agg(
        OK=("DATA_INSPECAO", "count"),
        Pendentes=("DATA_INSPECAO", lambda x: x.isna().sum())
    ).reset_index()
    df_coord["Total"] = df_coord["OK"] + df_coord["Pendentes"]
    df_coord["% OK"] = (df_coord["OK"] / df_coord["Total"] * 100).round(1)
    df_coord["% Pendentes"] = (df_coord["Pendentes"] / df_coord["Total"] * 100).round(1)

    df_melt = df_coord.melt(id_vars="COORDENADOR", value_vars=["% OK", "% Pendentes"],
                            var_name="Status", value_name="Percentual")

    fig = px.bar(
        df_melt, x="COORDENADOR", y="Percentual", color="Status",
        color_discrete_map={"% OK": "#27ae60", "% Pendentes": "#f39c12"},
        title="% Inspeções por Coordenador", barmode="stack", text="Percentual"
    )
    fig.update_traces(texttemplate='%{text}%', textposition='inside')
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# Tabela formatada
colunas_exibir = ["TÉCNICO", "FUNCAO", "PRODUTO_SIMILAR", "SALDO SGM TÉCNICO", "SUPERVISOR"]
df_pendentes_display = df_pendentes[colunas_exibir].fillna("").astype(str)

st.write("### Técnicos Pendentes e Saldo SGM Técnico")
st.write(
    df_pendentes_display.style
        .applymap(destaque_saldo, subset=["SALDO SGM TÉCNICO"])
        .hide_index()
)
