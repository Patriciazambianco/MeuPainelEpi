@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    col_tec = [col for col in df.columns if 'TECNICO' in col.upper()]
    col_prod = [col for col in df.columns if 'PRODUTO' in col.upper()]
    col_data = [col for col in df.columns if 'INSPECAO' in col.upper()]

    if not col_tec or not col_prod or not col_data:
        st.error("❌ Verifique se o arquivo contém colunas de TÉCNICO, PRODUTO e INSPEÇÃO.")
        return pd.DataFrame()

    tecnico_col, produto_col, data_col = col_tec[0], col_prod[0], col_data[0]

    df.rename(columns={'GERENTE': 'GERENTE_IMEDIATO', 'SITUAÇÃO CHECK LIST': 'STATUS CHECK LIST'}, inplace=True)
    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    df_com_data = df.dropna(subset=['Data_Inspecao']).copy()
    df_sem_data = df[df['Data_Inspecao'].isna()].copy()

    df_com_data.sort_values('Data_Inspecao', ascending=True, inplace=True)
    ultimos = df_com_data.groupby([tecnico_col, produto_col], as_index=False).last()

    base_sem_data = df_sem_data[[tecnico_col, produto_col]].drop_duplicates()
    base_sem_data = base_sem_data.merge(ultimos[[tecnico_col, produto_col]], on=[tecnico_col, produto_col], how='left', indicator=True)
    base_sem_data = base_sem_data[base_sem_data['_merge'] == 'left_only'].drop(columns=['_merge'])

    pendentes_unicos = df_sem_data.merge(base_sem_data, on=[tecnico_col, produto_col]).drop_duplicates(subset=[tecnico_col, produto_col])
    df_resultado = pd.concat([ultimos, pendentes_unicos], ignore_index=True)

    df_resultado.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)

    if 'STATUS CHECK LIST' in df_resultado.columns:
        df_resultado['STATUS CHECK LIST'] = df_resultado['STATUS CHECK LIST'].str.upper()

    hoje = pd.Timestamp.now().normalize()
    df_resultado['Dias_Sem_Inspecao'] = (hoje - df_resultado['Data_Inspecao']).dt.days
    df_resultado['Vencido'] = df_resultado['Dias_Sem_Inspecao'] > 180

    return df_resultado
