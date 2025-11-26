import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Painel Check List EPI", layout="wide")
st.title("🦺 Check List EPI - Técnicos OK x Pendentes")


# ========================================================
# CARREGAR DADOS
# ========================================================
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

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
        st.warning("⚠️ A coluna 'STATUS_CHECK_LIST' não existe na base.")
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    return df


url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados(url)



def graf_pizza_plotly(ok, pend, titulo):
    total = ok + pend
    ok_perc = round((ok / total) * 100, 1) if total > 0 else 0
    pend_perc = round((pend / total) * 100, 1) if total > 0 else 0

    fig = go.Figure(
        data=[go.Pie(
            labels=["OK", "Pendente"],
            values=[ok, pend],
            hole=0.55,
            textinfo="percent",
            texttemplate="%{percent:.1%}",
            marker=dict(colors=["mediumseagreen", "tomato"])
        )]
    )

    fig.update_layout(
        title=titulo,
        title_font_size=14,
        height=250,
        width=250,
        showlegend=True,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig



st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())

gerente_sel = st.sidebar.selectbox("👩‍💼 Gerente", gerentes)
coord_sel = st.sidebar.selectbox("🧑‍🏭 Coordenador", coordenadores)

df_f = df.copy()
if gerente_sel != "Todos":
    df_f = df_f[df_f["GERENTE"] == gerente_sel]
if coord_sel != "Todos":
    df_f = df_f[df_f["COORDENADOR"] == coord_sel]



total = len(df_f)
qtd_ok = (df_f["STATUS_CHECK_LIST"] == "OK").sum()
qtd_pend = (df_f["STATUS_CHECK_LIST"] == "PENDENTE").sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("✅ OK", qtd_ok)
col2.metric("⚠️ Pendentes", qtd_pend)
col3.metric("📊 % OK", f"{(qtd_ok/total*100):.1f}%" if total else "0%")
col4.metric("📉 % Pendentes", f"{(qtd_pend/total*100):.1f}%" if total else "0%")



st.subheader("📌 Status por Gerente")

cont_g = (
    df_f.groupby(["GERENTE", "STATUS_CHECK_LIST"])["TECNICO"]
    .nunique()
    .unstack(fill_value=0)
    .reset_index()
)

if not cont_g.empty:
    cols = st.columns(3)
    idx = 0

    for _, row in cont_g.iterrows():
        gerente = row["GERENTE"]
        ok_val = int(row.get("OK", 0))
        pend_val = int(row.get("PENDENTE", 0))

        with cols[idx % 3]:
            st.plotly_chart(
                graf_pizza_plotly(ok_val, pend_val, f"{gerente}"),
                use_container_width=False
            )
        idx += 1
else:
    st.info("Nenhum gerente encontrado.")



st.subheader("📌 Status por Coordenador")

cont_c = (
    df_f.groupby(["COORDENADOR", "STATUS_CHECK_LIST"])["TECNICO"]
    .nunique()
    .unstack(fill_value=0)
    .reset_index()
)

if not cont_c.empty:
    cols = st.columns(3)
    idx = 0

    for _, row in cont_c.iterrows():
        coord = row["COORDENADOR"]
        ok_val = int(row.get("OK", 0))
        pend_val = int(row.get("PENDENTE", 0))

        with cols[idx % 3]:
            st.plotly_chart(
                graf_pizza_plotly(ok_val, pend_val, f"{coord}"),
                use_container_width=False
            )
        idx += 1
else:
    st.info("Nenhum coordenador encontrado.")



df_pend = df_f[df_f["STATUS_CHECK_LIST"] == "PENDENTE"]

st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pend[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS_CHECK_LIST"]])

if not df_pend.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_pend.to_excel(writer, index=False, sheet_name="Pendentes")
    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=output.getvalue(),
        file_name="Pendentes_EPI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.success("🎉 Nenhum pendente encontrado!")
