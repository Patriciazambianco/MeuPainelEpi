import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI com Gráficos", layout="wide")

# Simula os dados como se viessem do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)
df.columns = df.columns.str.upper().str.strip()
df = df.rename(columns={"STATUS CHECK LIST": "STATUS", "DATA INSPECAO": "DATA_INSPECAO"})
df["STATUS"] = df["STATUS"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS"].replace({"CHECK LIST OK": "OK", "PENDENTE": "PENDENTE"})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Pegar a última inspeção por TECNICO + PRODUTO
ultimas = df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
ultimas = ultimas.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

base_tecnicos = df[["TECNICO", "PRODUTO_SIMILAR", "GERENTE", "COORDENADOR"]].drop_duplicates()
df_final = pd.merge(base_tecnicos, ultimas[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
                    on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

def classificar_status(status_list):
    if pd.isna(status_list).all():
        return "SEM INSPECAO"
    s = set(status_list)
    if "PENDENTE" in s:
        return "PENDENTE"
    elif "OK" in s:
        return "OK"
    else:
        return "SEM INSPECAO"

# Corrige: conta um status por técnico (após agrupar por TECNICO)
status_tecnicos = df_final.groupby(["TECNICO", "GERENTE", "COORDENADOR"])["STATUS"] \
                          .apply(classificar_status).reset_index(name="STATUS_RESUMO")

# KPIs
ok = (status_tecnicos["STATUS_RESUMO"] == "OK").sum()
pend = (status_tecnicos["STATUS_RESUMO"] == "PENDENTE").sum()
sem = (status_tecnicos["STATUS_RESUMO"] == "SEM INSPECAO").sum()
total = ok + pend + sem

st.markdown("## Indicadores Gerais")
col1, col2, col3 = st.columns(3)
col1.metric("Técnicos OK", ok, f"{ok/total:.0%}" if total else "0%")
col2.metric("Pendentes", pend, f"{pend/total:.0%}" if total else "0%")
col3.metric("Sem inspeção", sem, f"{sem/total:.0%}" if total else "0%")

# Gráfico de pizza
status_count = status_tecnicos["STATUS_RESUMO"].value_counts().reset_index()
status_count.columns = ["STATUS", "QTD"]
fig_pizza = px.pie(status_count, names="STATUS", values="QTD", title="Distribuição de Status")
st.plotly_chart(fig_pizza, use_container_width=True)

# Ranking por coordenador (não gerente)
ranking = status_tecnicos.groupby("COORDENADOR")["STATUS_RESUMO"].value_counts().unstack().fillna(0)
fig_ranking = px.bar(ranking, title="Ranking por Coordenador", barmode="group")
st.plotly_chart(fig_ranking, use_container_width=True)

# Exibir tabela final
st.markdown("### Detalhamento por Técnico")
st.dataframe(status_tecnicos)

# Botão de download
def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Status_Tecnicos')
    output.seek(0)
    return output

excel = gerar_excel_download(status_tecnicos)
st.download_button(
    label="⬇️ Baixar Excel com Status",
    data=excel,
    file_name="status_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
