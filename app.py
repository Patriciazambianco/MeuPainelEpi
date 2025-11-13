import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    # Padroniza status
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
        st.warning("⚠️ Coluna 'STATUS_CHECK_LIST' não encontrada. Todos os registros marcados como 'PENDENTE'.")
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    # Garante existência das colunas de hierarquia
    for col in ["GERENTE_IMEDIATO", "COORDENADOR_IMEDIATO"]:
        if col not in df.columns:
            df[col] = "NÃO INFORMADO"

    return df

# ======= LEITURA =======
url = "https://link_para_sua_planilha.xlsx"  # <-- Substitua aqui!
df = carregar_dados(url)

# ======= MÉTRICAS GERAIS =======
total = len(df)
qtd_ok = (df["STATUS_CHECK_LIST"] == "OK").sum()
qtd_pend = (df["STATUS_CHECK_LIST"] == "PENDENTE").sum()

perc_ok = round((qtd_ok / total) * 100, 1) if total > 0 else 0
perc_pend = round((qtd_pend / total) * 100, 1) if total > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ % OK Geral", f"{perc_ok}%", f"{qtd_ok} de {total}")
col2.metric("⚠️ % Pendentes", f"{perc_pend}%", f"{qtd_pend} de {total}")

# ======= GRÁFICO DE PIZZA =======
df_pizza = pd.DataFrame({
    "Status": ["OK", "PENDENTE"],
    "Quantidade": [qtd_ok, qtd_pend]
})
fig_pizza = px.pie(
    df_pizza,
    names="Status",
    values="Quantidade",
    color="Status",
    color_discrete_map={"OK": "mediumseagreen", "PENDENTE": "tomato"},
    title="Distribuição Geral de Checklists"
)
fig_pizza.update_traces(textinfo="percent+label", pull=[0.05, 0])
st.plotly_chart(fig_pizza, use_container_width=True)

# ======= AGRUPAMENTO POR GERENTE E COORDENADOR =======
st.subheader("📊 Percentual por Gerente e Coordenador")

df_group = (
    df.groupby(["GERENTE_IMEDIATO", "COORDENADOR_IMEDIATO", "STATUS_CHECK_LIST"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# Garante colunas mesmo se faltarem
if "OK" not in df_group.columns:
    df_group["OK"] = 0
if "PENDENTE" not in df_group.columns:
    df_group["PENDENTE"] = 0

df_group["TOTAL"] = df_group["OK"] + df_group["PENDENTE"]
df_group["%OK"] = round((df_group["OK"] / df_group["TOTAL"]) * 100, 1)
df_group["%PENDENTE"] = round((df_group["PENDENTE"] / df_group["TOTAL"]) * 100, 1)

# Gráfico de barras
fig_bar = px.bar(
    df_group,
    x="COORDENADOR_IMEDIATO",
    y="%OK",
    color="GERENTE_IMEDIATO",
    title="✅ % OK por Coordenador e Gerente",
    barmode="group",
    text="%OK",
)
fig_bar.update_layout(yaxis_title="% OK", xaxis_title="Coordenador", xaxis_tickangle=-30)
st.plotly_chart(fig_bar, use_container_width=True)

# ======= BOTÃO PARA DOWNLOAD =======
pendentes = df[df["STATUS_CHECK_LIST"] == "PENDENTE"]

st.subheader("⬇️ Download de Pendências")
st.write(f"Total de pendências: **{len(pendentes)}**")

if len(pendentes) > 0:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pendentes.to_excel(writer, index=False, sheet_name="Pendentes")
    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=output.getvalue(),
        file_name="Pendentes_Checklist.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("🎉 Nenhum registro pendente encontrado!")

# ======= MOSTRA A TABELA FINAL =======
st.dataframe(df)
