import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# Estilo geral do app
st.markdown("""
<style>
.stApp { background-color: #d0f0c0; }
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
@keyframes blink {
  0% {opacity: 1;}
  50% {opacity: 0.4;}
  100% {opacity: 1;}
}
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
.kpi-box.pending { background-color: #f39c12; }
.kpi-box.percent { background-color: #27ae60; }
.kpi-title { font-size: 1.1rem; margin-bottom: 0.5rem; font-weight: 600; }
.kpi-value { font-size: 2.5rem; font-weight: 700; line-height: 1; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    return pd.read_excel(url, engine="openpyxl")

def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates("TÉCNICO", keep="last")
    tecnicos_com_inspecao = ultimas["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)].drop_duplicates("TÉCNICO")
    return pd.concat([ultimas, sem_data], ignore_index=True)

def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_epi.xlsx" class="download-btn">📥 Baixar Excel Completo</a>'
    return href

def status_saldo(x):
    if pd.isna(x):
        return "❌ SEM SALDO DE EPI"
    elif isinstance(x, str) and "não tem" in x.lower():
        return "❌ SEM SALDO DE EPI"
    else:
        return "✅ TEM SALDO DE EPI"

def status_inspecao(row):
    if pd.isna(row["DATA_INSPECAO"]):
        return "Pendente"
    else:
        return "OK"

def destaque_saldo(s):
    return ['background-color: #fff3cd; font-weight: bold' if v == "❌ SEM SALDO DE EPI" else '' for v in s]

# Início do app
df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)
st.title("Painel de Inspeções EPI")

# Filtros
gerentes = sorted(df_tratado["GERENTE"].dropna().unique())
gerente_sel = st.selectbox("Filtrar por Gerente", ["-- Todos --"] + gerentes)
df_filtrado_ger = df_tratado if gerente_sel == "-- Todos --" else df_tratado[df_tratado["GERENTE"] == gerente_sel]
coordenadores = sorted(df_filtrado_ger["COORDENADOR"].dropna().unique())
coordenador_sel = st.multiselect("Filtrar por Coordenador", coordenadores)
df_filtrado = df_filtrado_ger if not coordenador_sel else df_filtrado_ger[df_filtrado_ger["COORDENADOR"].isin(coordenador_sel)]

# Adiciona colunas de status
df_filtrado["STATUS INSPECAO"] = df_filtrado.apply(status_inspecao, axis=1)
df_filtrado["STATUS SALDO"] = df_filtrado["SALDO SGM TÉCNICO"].apply(status_saldo)

# Botão para download do dataset filtrado completo
st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)

# KPIs
total = len(df_filtrado)
pending = (df_filtrado["STATUS INSPECAO"] == "Pendente").sum()
ok = total - pending
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendente = round(100 - pct_ok, 1)

st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-box percent"><div class="kpi-title">Inspeções OK</div><div class="kpi-value">{ok}</div></div>
    <div class="kpi-box pending"><div class="kpi-title">Pendentes</div><div class="kpi-value">{pending}</div></div>
    <div class="kpi-box percent"><div class="kpi-title">% OK</div><div class="kpi-value">{pct_ok}%</div></div>
    <div class="kpi-box pending"><div class="kpi-title">% Pendentes</div><div class="kpi-value">{pct_pendente}%</div></div>
</div>
""", unsafe_allow_html=True)

# Gráfico percentual por coordenador
if len(df_filtrado) > 0 and len(coordenadores) > 0:
    df_status_coord = df_filtrado.groupby("COORDENADOR").apply(
        lambda x: pd.Series({
            "OK": (x["STATUS INSPECAO"] == "OK").sum(),
            "Pendentes": (x["STATUS INSPECAO"] == "Pendente").sum(),
            "Total": len(x)
        })
    ).reset_index()
    df_status_coord["% OK"] = (df_status_coord["OK"] / df_status_coord["Total"] * 100).round(1)
    df_status_coord["% Pendentes"] = (df_status_coord["Pendentes"] / df_status_coord["Total"] * 100).round(1)
    df_melt = df_status_coord.melt(id_vars="COORDENADOR", value_vars=["% OK", "% Pendentes"], var_name="Status", value_name="Percentual")
    fig = px.bar(df_melt, x="COORDENADOR", y="Percentual", color="Status",
                 color_discrete_map={"% OK": "#27ae60", "% Pendentes": "#f39c12"},
                 text="Percentual", title="📊 Percentual de Inspeções por Coordenador",
                 labels={"COORDENADOR": "Coordenador", "Percentual": "%"})
    fig.update_layout(barmode="stack", xaxis_tickangle=-45, yaxis_range=[0, 100])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Selecione um gerente e/ou coordenador para visualizar o gráfico.")

# Mostrar tabela completa com destaque para saldo
st.markdown("### Técnicos com status de inspeção e saldo de EPI")
if df_filtrado.empty:
    st.success("Nenhum técnico encontrado! 👏")
else:
    st.dataframe(
        df_filtrado[["TÉCNICO", "COORDENADOR", "GERENTE", "DATA_INSPECAO", "STATUS INSPECAO", "SALDO SGM TÉCNICO", "STATUS SALDO"]],
        use_container_width=True
    )
    st.write(df_filtrado.style.apply(destaque_saldo, subset=["STATUS SALDO"]), unsafe_allow_html=True)
