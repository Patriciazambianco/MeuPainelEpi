import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Painel de Inspeções EPI", layout="wide")

def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Status_Tecnicos')
    output.seek(0)
    return output

# 🟡 Carregar dados do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)
df.columns = df.columns.str.upper().str.strip()

# 🟡 Padroniza nomes e status
df = df.rename(columns={"STATUS CHECK LIST": "STATUS", "DATA INSPECAO": "DATA_INSPECAO"})
df["STATUS"] = df["STATUS"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# 🟡 Última inspeção por técnico + produto
df_ultimas = df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False]) \
               .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# 🟡 Garante base com todos os técnicos + produtos
df_tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "GERENTE", "COORDENADOR"]].drop_duplicates()
df_final = pd.merge(df_tecnicos_produtos, df_ultimas[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
                    on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

# 🟡 Define status geral por técnico
def classificar_status(status_list):
    if pd.isna(status_list).all():
        return "SEM INSPECAO"
    status_set = set(status_list)
    if "PENDENTE" in status_set:
        return "PENDENTE"
    elif "OK" in status_set:
        return "OK"
    else:
        return "SEM INSPECAO"

status_tecnicos = df_final.groupby(["TECNICO", "GERENTE", "COORDENADOR"])["STATUS"] \
                          .apply(classificar_status).reset_index(name="STATUS_RESUMO")

# 🟡 Filtros interativos
col1, col2 = st.columns(2)
gerentes = sorted(status_tecnicos['GERENTE'].dropna().unique())
coordenadores = sorted(status_tecnicos['COORDENADOR'].dropna().unique())

with col1:
    gerente_selecionado = st.selectbox("Filtrar por GERENTE:", ["Todos"] + gerentes)
with col2:
    coordenador_selecionado = st.selectbox("Filtrar por COORDENADOR:", ["Todos"] + coordenadores)

df_filtrado = status_tecnicos.copy()
if gerente_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_selecionado]
if coordenador_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_selecionado]

# 🟡 Cálculo dos KPIs certinho
total = len(df_filtrado)
ok = (df_filtrado["STATUS_RESUMO"] == "OK").sum()
pendente = (df_filtrado["STATUS_RESUMO"] == "PENDENTE").sum()
sem = (df_filtrado["STATUS_RESUMO"] == "SEM INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pendente = round(pendente / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

# 🟢 Cards de indicadores estilosos
st.markdown(f"""
<style>
.kpi-container {{
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}
.kpi-box {{
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: bold;
    text-align: center;
    min-width: 200px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}}
.green {{ background-color: #d4edda; color: #155724; }}
.orange {{ background-color: #fff3cd; color: #856404; }}
.gray {{ background-color: #e2e3e5; color: #6c757d; }}
</style>

<div class="kpi-container">
  <div class="kpi-box green">✔️ Técnicos OK: {ok} ({pct_ok}%)</div>
  <div class="kpi-box orange">⚠️ Técnicos Pendentes: {pendente} ({pct_pendente}%)</div>
  <div class="kpi-box gray">❓ Sem Inspeção: {sem} ({pct_sem}%)</div>
</div>
""", unsafe_allow_html=True)

# 🟡 Tabela de técnicos
st.dataframe(df_filtrado)

# ⬇️ Botão para baixar
excel = gerar_excel_download(df_filtrado)
st.download_button(
    label="⬇️ Baixar Status Técnicos",
    data=excel,
    file_name="status_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
