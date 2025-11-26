import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(layout="wide")

# ----------------------------------
# EXEMPLO DE DADOS (troque pelo seu)
# ----------------------------------
df_status = pd.DataFrame({
    "Status": ["OK", "Pendente"],
    "Quantidade": [320, 80]
})

# Calcula porcentagem
df_status["Perc"] = df_status["Quantidade"] / df_status["Quantidade"].sum()

# ----------------------------------
# FUNÇÃO DO GRÁFICO
# ----------------------------------
def plot_pizza_menor(df):
    fig, ax = plt.subplots(figsize=(3, 3))  # 🔥 menor ainda

    wedges, texts, autotexts = ax.pie(
        df["Quantidade"],
        autopct=lambda p: f"{p:.1f}%",  # mostra %
        startangle=90,
        textprops={'fontsize': 8}  # fonte pequena p/ caber
    )

    # Ajuste para texto da % não sumir
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(8)
        autotext.set_weight("bold")

    ax.axis('equal')
    return fig

# ----------------------------------
# LAYOUT
# ----------------------------------
st.title("Dashboard - Gráficos Compactos")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Status Geral")
    st.pyplot(plot_pizza_menor(df_status))

with col2:
    st.subheader("Por Gerente")
    st.pyplot(plot_pizza_menor(df_status))

with col3:
    st.subheader("Por Coordenador")
    st.pyplot(plot_pizza_menor(df_status))
