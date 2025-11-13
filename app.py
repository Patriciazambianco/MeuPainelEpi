import streamlit as st
import pandas as pd
import plotly.express as px

# 🎨 CONFIGURAÇÃO GERAL
st.set_page_config(page_title="Check List EPI - Técnicos OK/Pendentes", layout="wide")

# 💅 CSS personalizado
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(120deg, #f8fbff, #f3e5f5);
    }
    h1 {
        text-align: center;
        color: #1b5e20;
        font-weight: 800;
        font-size: 2.2rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    .metric-card {
        padding: 13px;
        border-radius: 13px;
        color: white;
        font-weight: bold;
        text-align: center;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: scale(1.05);
    }
    .ok-card {background: linear-gradient(135deg, #2ecc71, #27ae60);}
    .pendente-card {background: linear-gradient(135deg, #e74c3c, #c0392b);}
    </style>
""", unsafe_allow_html=True)

# 🧠 TÍTULO
st.title("🦺 Check List EPI - Técnicos OK e Pendentes")

# 🚀 FUNÇÃO DE CARGA E ANÁLISE
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

# 🔗 URL DO ARQUIVO
url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

# 🧩 CARREGAMENTO
df = carregar_dados(url)

# 📊 CÁLCULOS
total = len(df)
if total > 0:
    qtd_ok = (df["STATUS_CHECK_LIST"] == "OK").sum()
    qtd_pend = (df["STATUS_CHECK_LIST"] == "PENDENTE").sum()
    perc_ok = round((qtd_ok / total) * 100, 1)
    perc_pend = round((qtd_pend / total) * 100, 1)
else:
    qtd_ok = qtd_pend = perc_ok = perc_pend = 0

# 🎯 MÉTRICAS COLORIDAS
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class='metric-card ok-card'>
        <h3>✅ % OK</h3>
        <h2>{perc_ok:.1f}%</h2>
        <p>{qtd_ok} de {total}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-card pendente-card'>
        <h3>⚠️ % Pendentes</h3>
        <h2>{perc_pend:.1f}%</h2>
        <p>{qtd_pend} de {total}</p>
    </div>
    """, unsafe_allow_html=True)

# 🥧 GRÁFICO DE PIZZA
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
    title="Distribuição Geral dos Checklists"
)
fig.update_traces(textinfo="percent+label", pull=[0.05, 0])
fig.update_layout(title_font=dict(size=20, color="#1b5e20"))

st.plotly_chart(fig, use_container_width=True)

# 📋 TABELA OPCIONAL
st.markdown("### 📋 Prévia dos Dados (5 primeiras linhas)")
st.dataframe(df.head())
