import plotly.express as px
import streamlit as st
import pandas as pd

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

    # Cálculos
    total = len(df)
    if total > 0:
        qtd_ok = (df["STATUS_CHECK_LIST"] == "OK").sum()
        qtd_pend = (df["STATUS_CHECK_LIST"] == "PENDENTE").sum()
        perc_ok = round((qtd_ok / total) * 100, 1)
        perc_pend = round((qtd_pend / total) * 100, 1)
    else:
        qtd_ok = qtd_pend = perc_ok = perc_pend = 0

    # Cards de métricas
    col1, col2 = st.columns(2)
    col1.metric("✅ % OK", f"{perc_ok}%", f"{qtd_ok} de {total}")
    col2.metric("⚠️ % Pendentes", f"{perc_pend}%", f"{qtd_pend} de {total}")

    # Gráfico de pizza
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
        title="Distribuição de Checklists"
    )
    fig.update_traces(textinfo="percent+label", pull=[0.05, 0])

    st.plotly_chart(fig, use_container_width=True)

    return df
