import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #d0f0c0; }
    .download-btn {
        font-size:18px; color:#fff !important; background-color:#005a9c;
        padding:10px 15px; border-radius:5px; text-decoration:none !important;
        animation: blink 1.5s infinite; display: inline-block; margin-bottom: 20px; font-weight: 700;
    }
    @keyframes blink {
      0% {opacity: 1;}
      50% {opacity: 0.4;}
      100% {opacity: 1;}
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
    ultimas_por_tecnico = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]
    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])
    resultado = pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)
    return resultado

def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    b64 = base64.b64encode(output.getvalue()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="pendentes_epi.xlsx" class="download-btn">📥 Baixar Excel</a>'
    return href

def color_saldo(val):
    val_lower = str(val).strip().lower()
    if val_lower == "tem no saldo":
        return 'background-color: #fce5cd; color: #b26a00; font-weight: bold;'
    elif val_lower in ["não tem no saldo", "nao tem no saldo"]:
        return 'background-color: #f8d7da; color: #842029; font-weight: bold;'
    else:
        return ""

st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# Filtros
gerentes = sorted(df_tratado["GERENTE"].dropna().unique())
gerente_sel = st.selectbox("Filtrar por Gerente", ["-- Todos --"] + gerentes)
df_filtrado = df_tratado[df_tratado["GERENTE"] == gerente_sel] if gerente_sel != "-- Todos --" else df_tratado.copy()

coordenadores = sorted(df_filtrado["COORDENADOR"].dropna().unique())
coord_sel = st.multiselect("Filtrar por Coordenador", coordenadores)
if coord_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coord_sel)]

# Técnicos pendentes
df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()].copy()
df_pendentes["SALDO SGM TÉCNICO"] = df_pendentes["SALDO SGM TÉCNICO"].fillna("Não tem no saldo").astype(str)

# Botão para alternar modo de visualização
modo = st.radio("Modo de visualização dos Pendentes:", ["Todos", "Somente com saldo", "Somente sem saldo"])

if modo == "Somente com saldo":
    df_pendentes = df_pendentes[df_pendentes["SALDO SGM TÉCNICO"].str.lower().str.strip() == "tem no saldo"]
elif modo == "Somente sem saldo":
    df_pendentes = df_pendentes[df_pendentes["SALDO SGM TÉCNICO"].str.lower().str.strip().isin(["não tem no saldo", "nao tem no saldo"])]

# Indicadores
total = len(df_filtrado)
pendentes = df_filtrado["DATA_INSPECAO"].isna().sum()
ok = total - pendentes
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendentes = 100 - pct_ok

st.markdown(f"""
<div style='display: flex; gap: 1.5rem; margin-bottom: 2rem;'>
  <div style='flex:1; background:#27ae60; color:white; padding:20px; border-radius:10px; text-align:center'>
    <div style='font-size:1.1rem'>Inspeções OK</div>
    <div style='font-size:2.5rem; font-weight:700'>{ok}</div>
  </div>
  <div style='flex:1; background:#f39c12; color:white; padding:20px; border-radius:10px; text-align:center'>
    <div style='font-size:1.1rem'>Pendentes</div>
    <div style='font-size:2.5rem; font-weight:700'>{pendentes}</div>
  </div>
  <div style='flex:1; background:#2980b9; color:white; padding:20px; border-radius:10px; text-align:center'>
    <div style='font-size:1.1rem'>% OK</div>
    <div style='font-size:2.5rem; font-weight:700'>{pct_ok}%</div>
  </div>
  <div style='flex:1; background:#c0392b; color:white; padding:20px; border-radius:10px; text-align:center'>
    <div style='font-size:1.1rem'>% Pendentes</div>
    <div style='font-size:2.5rem; font-weight:700'>{pct_pendentes}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Gráfico por Coordenador
if not df_filtrado.empty and not df_filtrado["COORDENADOR"].isna().all():
    df_status_coord = df_filtrado.groupby("COORDENADOR").apply(
        lambda x: pd.Series({
            "Pendentes": x["DATA_INSPECAO"].isna().sum(),
            "OK": x["DATA_INSPECAO"].notna().sum()
        })
    ).reset_index()

    df_status_coord["Total"] = df_status_coord["OK"] + df_status_coord["Pendentes"]
    df_status_coord["% OK"] = (df_status_coord["OK"] / df_status_coord["Total"] * 100).round(1)
    df_status_coord["% Pendentes"] = (df_status_coord["Pendentes"] / df_status_coord["Total"] * 100).round(1)

    df_melt = df_status_coord.melt(id_vars="COORDENADOR", value_vars=["% OK", "% Pendentes"],
                                    var_name="Status", value_name="Percentual")

    fig = px.bar(
        df_melt, x="COORDENADOR", y="Percentual", color="Status",
        color_discrete_map={"% OK": "#27ae60", "% Pendentes": "#f39c12"},
        title="% Inspeções por Coordenador", text="Percentual", barmode="stack"
    )
    fig.update_traces(texttemplate='%{text}%', textposition='inside')
    fig.update_layout(yaxis=dict(range=[0, 100]))

    st.plotly_chart(fig, use_container_width=True)

# Botão de download
st.markdown(gerar_download_excel(df_pendentes), unsafe_allow_html=True)

# Tabela
st.write("### Técnicos Pendentes e Saldo SGM Técnico")

colunas_exibir = ["TÉCNICO", "FUNCAO", "PRODUTO_SIMILAR", "SALDO SGM TÉCNICO", "SUPERVISOR"]
df_exibir = df_pendentes[colunas_exibir].fillna("").astype(str)
st.dataframe(df_exibir.style.applymap(color_saldo, subset=["SALDO SGM TÉCNICO"]), use_container_width=True)
