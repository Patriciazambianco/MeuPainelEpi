import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Painel de Inspeções EPI", layout="wide")

def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendentes_SemInspecao')
    output.seek(0)
    return output

url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

# Leitura do Excel
df = pd.read_excel(url)

# Normaliza nomes das colunas
df = df.rename(columns=lambda x: x.upper().strip())

# Renomeia as colunas certas
df = df.rename(columns={
    "STATUS CHECK LIST": "STATUS",
    "COORDENADOR": "COORDENADOR",
    "GERENTE": "GERENTE",
    "TECNICO": "TECNICO",
    "PRODUTO_SIMILAR": "PRODUTO_SIMILAR",
    "DATA INSPECAO": "DATA_INSPECAO"
})

# Padroniza valores da coluna STATUS
df["STATUS"] = df["STATUS"].astype(str).str.strip().str.upper()
df["STATUS"] = df["STATUS"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# Converte DATA_INSPECAO para datetime
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors='coerce')

# Ordena para pegar a última inspeção
df = df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])

# Últimas inspeções (com data)
df_ultimas = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first").reset_index(drop=True)

# Base com todas as combinações técnico + produto
df_base = df[["TECNICO", "PRODUTO_SIMILAR"]].drop_duplicates()

# Merge LEFT para trazer todos técnicos+produtos, mesmo sem inspeção
df_final = pd.merge(df_base, df_ultimas, on=["TECNICO", "PRODUTO_SIMILAR"], how="left", suffixes=('', '_ULTIMA'))

# Substitui STATUS NaN por 'SEM INSPECAO'
df_final["STATUS"] = df_final["STATUS"].fillna("SEM INSPECAO")

# Filtros
col1, col2 = st.columns(2)
gerentes = sorted(df_final['GERENTE'].dropna().unique().tolist())
coordenadores = sorted(df_final['COORDENADOR'].dropna().unique().tolist())

with col1:
    gerente_selecionado = st.selectbox("Filtrar por GERENTE:", ["Todos"] + gerentes)
with col2:
    coordenador_selecionado = st.selectbox("Filtrar por COORDENADOR:", ["Todos"] + coordenadores)

df_filtrado = df_final.copy()
if gerente_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_selecionado]
if coordenador_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_selecionado]

# Agrupa por Técnico e Status
tabela_tecnicos = df_filtrado.groupby(["TECNICO", "STATUS"]).size().unstack(fill_value=0)

# Marca técnicos com cada status
tabela_tecnicos["Tem_OK"] = tabela_tecnicos.get("OK", 0) > 0
tabela_tecnicos["Tem_PENDENTE"] = tabela_tecnicos.get("PENDENTE", 0) > 0
tabela_tecnicos["Tem_SEM_INSPECAO"] = tabela_tecnicos.get("SEM INSPECAO", 0) > 0

total = tabela_tecnicos.shape[0]

# Contagens exclusivas
pendentes = tabela_tecnicos[tabela_tecnicos["Tem_PENDENTE"] == True].shape[0]
ok_sem_pend = tabela_tecnicos[
    (tabela_tecnicos["Tem_OK"] == True) & (tabela_tecnicos["Tem_PENDENTE"] == False)
].shape[0]
sem_inspecao = tabela_tecnicos[tabela_tecnicos["Tem_SEM_INSPECAO"] == True].shape[0]

# Percentuais
pct_ok = round(ok_sem_pend / total * 100, 1) if total > 0 else 0
pct_pend = round(pendentes / total * 100, 1) if total > 0 else 0
pct_sem = round(sem_inspecao / total * 100, 1) if total > 0 else 0

# Exibe KPIs com estilo
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
  <div class="kpi-box green">✔️ Técnicos OK: {ok_sem_pend} ({pct_ok}%)</div>
  <div class="kpi-box orange">⚠️ Técnicos Pendentes: {pendentes} ({pct_pend}%)</div>
  <div class="kpi-box gray">❓ Sem Inspeção: {sem_inspecao} ({pct_sem}%)</div>
</div>
""", unsafe_allow_html=True)

# Exibe técnicos pendentes e sem inspeção na tabela
tecnicos_pendentes_sem = tabela_tecnicos[
    (tabela_tecnicos["Tem_PENDENTE"] == True) | (tabela_tecnicos["Tem_SEM_INSPECAO"] == True)
].reset_index()

df_pendentes_sem = pd.merge(tecnicos_pendentes_sem[["TECNICO"]], df_filtrado, on="TECNICO", how="left")

with st.expander("📋 Ver Técnicos Pendentes e Sem Inspeção"):
    st.dataframe(df_pendentes_sem)

# Botão para baixar pendentes e sem inspeção em Excel
excel_download = gerar_excel_download(df_pendentes_sem)
st.download_button(
    label="⬇️ Baixar Pendentes e Sem Inspeção em Excel",
    data=excel_download,
    file_name="pendentes_sem_inspecao_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
