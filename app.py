import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 Painel de Checklists EPI")

# ===========================================================
# 📦 Função para carregar e tratar os dados
# ===========================================================
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    # Padroniza STATUS_CHECK_LIST
    if "STATUS_CHECK_LIST" in df.columns:
        df["STATUS_CHECK_LIST"] = (
            df["STATUS_CHECK_LIST"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "CHECK LIST OK": "OK",
                "CHECKLIST OK": "OK",
                "OK": "OK",
                "PENDENTE": "PENDENTE"
            })
        )
    else:
        st.warning("⚠️ A coluna 'STATUS_CHECK_LIST' não existe na base. Todos os registros foram marcados como 'PENDENTE'.")
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    return df

# ===========================================================
# 🔗 URL do Excel hospedado no GitHub (link RAW!)
# ===========================================================
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

df = carregar_dados(url)

# ===========================================================
# 🧮 Cálculos gerais
# ===========================================================
total = len(df)
qtd_ok = (df["STATUS_CHECK_LIST"] == "OK").sum()
qtd_pend = (df["STATUS_CHECK_LIST"] == "PENDENTE").sum()
perc_ok = round((qtd_ok / total) * 100, 1) if total > 0 else 0
perc_pend = round((qtd_pend / total) * 100, 1) if total > 0 else 0

# ===========================================================
# 💡 Cards gerais
# ===========================================================
col1, col2 = st.columns(2)
col1.metric("✅ % OK", f"{perc_ok}%", f"{qtd_ok} de {total}")
col2.metric("⚠️ % Pendentes", f"{perc_pend}%", f"{qtd_pend} de {total}")

# ===========================================================
# 📊 Gráfico de pizza geral
# ===========================================================
df_pizza = pd.DataFrame({
    "Status": ["OK", "PENDENTE"],
    "Quantidade": [qtd_ok, qtd_pend]
})
fig = px.pie(
    df_pizza,
    names="Status",
    values="Quantidade",
    color="Status",
    color_discrete_map={"OK": "mediumseagreen", "PENDENTE": "tomato"},
    title="Distribuição Geral de Checklists"
)
fig.update_traces(textinfo="percent+label", pull=[0.05, 0])
st.plotly_chart(fig, use_container_width=True)

# ===========================================================
# 📈 % por gerente e coordenador
# ===========================================================
if "GERENTE_IMEDIATO" in df.columns and "COORDENADOR_IMEDIATO" in df.columns:
    agrupado = (
        df.groupby(["GERENTE_IMEDIATO", "COORDENADOR_IMEDIATO", "STATUS_CHECK_LIST"])
        .size()
        .reset_index(name="QTD")
    )

    total_por_grupo = (
        agrupado.groupby(["GERENTE_IMEDIATO", "COORDENADOR_IMEDIATO"])["QTD"].sum().reset_index(name="TOTAL")
    )

    df_merged = pd.merge(agrupado, total_por_grupo, on=["GERENTE_IMEDIATO", "COORDENADOR_IMEDIATO"])
    df_merged["PERCENTUAL"] = (df_merged["QTD"] / df_merged["TOTAL"] * 100).round(1)

    fig2 = px.bar(
        df_merged,
        x="COORDENADOR_IMEDIATO",
        y="PERCENTUAL",
        color="STATUS_CHECK_LIST",
        barmode="group",
        facet_col="GERENTE_IMEDIATO",
        color_discrete_map={"OK": "mediumseagreen", "PENDENTE": "tomato"},
        title="% de Checklists OK x Pendentes por Gerente e Coordenador"
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("ℹ️ Colunas 'GERENTE_IMEDIATO' e 'COORDENADOR_IMEDIATO' não foram encontradas na base.")

# ===========================================================
# 📥 Botão para baixar pendentes
# ===========================================================
df_pendentes = df[df["STATUS_CHECK_LIST"] == "PENDENTE"]

if not df_pendentes.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_pendentes.to_excel(writer, index=False, sheet_name="Pendentes")
    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=output.getvalue(),
        file_name="Pendentes_EPI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spread
