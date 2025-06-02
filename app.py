@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    # Identifica as colunas relevantes
    col_tec = [col for col in df.columns if 'TECNICO' in col.upper()]
    col_prod = [col for col in df.columns if 'PRODUTO' in col.upper()]
    col_data = [col for col in df.columns if 'INSPECAO' in col.upper()]

    if not col_tec or not col_prod or not col_data:
        st.error("❌ Verifique se o arquivo contém colunas de TÉCNICO, PRODUTO e INSPEÇÃO.")
        return pd.DataFrame()

    tecnico_col = col_tec[0]
    produto_col = col_prod[0]
    data_col = col_data[0]

    # Renomeia colunas padrão
    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'STATUS CHECK LIST'
    }, inplace=True)

    # Padroniza textos e datas
    df[tecnico_col] = df[tecnico_col].astype(str).str.strip().str.upper()
    df[produto_col] = df[produto_col].astype(str).str.strip().str.upper()
    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    # Cria chave única TÉCNICO|PRODUTO
    df['CHAVE'] = df[tecnico_col] + "|" + df[produto_col]

    # Divide os com e sem data
    df_com_data = df.dropna(subset=['Data_Inspecao']).copy()
    df_sem_data = df[df['Data_Inspecao'].isna()].copy()

    # Pega apenas a última inspeção por CHAVE
    df_com_data.sort_values('Data_Inspecao', ascending=False, inplace=True)
    df_ultimos = df_com_data.drop_duplicates(subset='CHAVE', keep='first')

    # Remove duplicados do sem data (garante um só por CHAVE)
    df_sem_data = df_sem_data.drop_duplicates(subset='CHAVE', keep='first')

    # Exclui pendentes que já têm inspeção registrada
    chaves_com_data = set(df_ultimos['CHAVE'])
    df_sem_data = df_sem_data[~df_sem_data['CHAVE'].isin(chaves_com_data)]

    # Junta tudo
    df_final = pd.concat([df_ultimos, df_sem_data], ignore_index=True)

    # Renomeia colunas
    df_final.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    # Padroniza STATUS
    if 'STATUS CHECK LIST' in df_final.columns:
        df_final['STATUS CHECK LIST'] = df_final['STATUS CHECK LIST'].astype(str).str.strip().str.upper()

    # Dias sem inspeção
    hoje = pd.Timestamp.now().normalize()
    df_final['Dias_Sem_Inspecao'] = (hoje - df_final['Data_Inspecao']).dt.days
    df_final['Vencido'] = df_final['Dias_Sem_Inspecao'] > 180

    return df_final.drop(columns=['CHAVE'])


duplicados = df.duplicated(subset=['TECNICO', 'PRODUTO'], keep=False)
if duplicados.any():
    st.warning("⚠️ Ainda há duplicatas de Técnico + Produto! 😱")
    st.dataframe(df[duplicados])
else:
    st.success("✅ Sem duplicatas! Cada Técnico + Produto aparece uma vez só.")
