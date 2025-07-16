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

# URL do Excel no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

# Carregar e tratar dados
df = pd.read_excel(url)
df = df.rename(columns=lambda x: x.upper().strip())

# Renomeia colunas
df = df.rename(columns={
    "STATUS CHECK LIST": "STATUS",
    "GERENTE": "GERENTE",
    "COORDENADOR": "COORDENADOR",
    "TECNICO": "TECNICO",
    "PRODUTO_SIMILAR": "PRODUTO_SIMILAR",
    "DATA INSPECAO": "DATA_INSPECAO"
})

# Padroniza valores
df["STATUS"] = df["STATUS"].astype(str).str.strip().str.upper()
df["STATUS"] = df["STATUS"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors='coerce')

# Última inspeção por técnico + produto
df_ultimas = df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False]) \
               .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# Resumo por técnico
status_por_tecnico = df_ultimas.groupby("TECNICO")["STATUS"].apply(list).reset_index()

def resumo_status(lista):
    s = set(lista)
    if "PENDENTE" in s:
        return "PENDENTE"
    elif "OK" in s:
        return "OK"
    else:
        return "SEM INSPECAO"

status_por_tecnico["STATUS_RESUMO"] = status_por_tecnico["STATUS"].apply(resumo_status)

# Garantir todos os técnicos (inclusive sem inspeção)
todos_tecnicos = pd.DataFrame(df["TECNICO"].unique(), columns=["TECNICO"])
status_tecnicos = todos_tecnicos.merge(status_por_tecnico[["TECNICO", "STATUS_RESUMO"]], on="TECNICO", how="left")
status_tecnicos["STATUS_RESUMO"] = status_tecnicos["STATUS_RESUMO"].fillna("SEM INSPECAO")

# Juntar com GERENTE/COORDENADOR
info_tecnicos = df[["TECNICO", "GERENTE", "COORDENADOR"]].drop_duplicates()
status_tecnicos = status_tecnicos.merge(info_tecnicos, on="TECNICO", how="left")

# Trata campos nulos pra não sumirem nos filtros
status_tecnicos["GERENTE"] = status_tecnicos["GERENTE"].fillna("Não informado")
status_tecnicos["COORDENADOR"] = status_tecnicos["COORDENADOR"].fillna("Não informado")

# Filtros
col1, col2 = st.columns(2)
gerentes = sorted(status_tecnicos['GERENTE'].unique())
coordenadores = sorted(status_tecnicos['COORDENADOR'].unique())

with col1:
    gerente_selecionado = st.selectbox("Filtrar por GERENTE:", ["Todos"] + gerentes)
with col2:
    coordenador_selecionado = st.selectbox("Filtrar por COORDENADOR:", ["Todos"] + coordenadores)

df_filtrado = status_tecnicos.copy()
if gerente_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_selecionado]
if coordenador_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_selecionado]

# Cálculo certo: 1 linha por técnico
df_filtrado = df_filtrado.drop_duplicates(subset=["TECNICO"])

# KPIs
total = df_filtrado["TECNICO"].nunique()
ok = df_filtrado[df_filtrado["STATUS_RESUMO"] == "OK"]["TECNICO"].nunique()
pendente = df_filtrado[df_filtrado["STATUS_RESUMO"] == "PENDENTE"]["TECNICO"].nunique()
sem_inspecao = df_filtrado[df_filtrado["STATUS_RESUMO"] == "SEM INSPECAO"]["TECNICO"].nunique()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pendente = round(pendente / total * 100, 1) if total else 0
pct_sem = round(sem_inspecao / total * 100, 1) if total else 0

# KPIs estilosos 😎
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
  <div class="kpi-box gray">❓ Sem Inspeção: {sem_inspecao} ({pct_sem}%)</div>
</div>
""", unsafe_allow_html=True)

# Tabela e botão de download
st.dataframe(df_filtrado)

excel = gerar_excel_download(df_filtrado)
st.download_button(
    label="⬇️ Baixar Status Técnicos",
    data=excel,
    file_name="status_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
