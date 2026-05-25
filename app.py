import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io

st.set_page_config(page_title="ETL - Assinaturas Pendentes", layout="wide", page_icon="📊")


def converter_data_excel(valor):
    if pd.isna(valor):
        return valor

    val_str = str(valor).strip()
    try:
        num = float(val_str.replace(',', '.'))
        data = pd.to_datetime('1899-12-30') + pd.to_timedelta(num, unit='D')
        return data.strftime('%d/%m/%Y')
    except ValueError:
        return val_str


@st.cache_data
def processar_dados(file):
    try:
        df = pd.read_csv(file, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        file.seek(0)
        df = pd.read_csv(file, sep=';', encoding='latin1')

    df = df.replace(u'\xa0', u' ', regex=True)

    df['ID'] = df['ID'].ffill()

    df_cpfs = df[df['Profissional'].astype(str).str.contains('CPF:', na=False)][['ID', 'Profissional']]
    df_cpfs = df_cpfs.rename(columns={'Profissional': 'CPF'})
    df_cpfs['CPF'] = df_cpfs['CPF'].str.replace('CPF:', '').str.strip()

    df['Profissional'] = df['Profissional'].apply(lambda x: np.nan if str(x).startswith('CPF:') else x)
    df['Profissional'] = df['Profissional'].ffill()

    colunas_para_preencher = ['Vínculo (RH)', 'Qtd Doc. Pendente', 'Data Última Assinatura', 'Liberação']
    df[colunas_para_preencher] = df[colunas_para_preencher].ffill()

    df['Data Última Assinatura'] = df['Data Última Assinatura'].apply(converter_data_excel)

    # --- CORREÇÃO DOS DECIMAIS (.0) ---
    # Convertendo para numérico e depois forçando o tipo 'Int64' (Inteiro que aceita nulos)
    df['ID'] = pd.to_numeric(df['ID'], errors='coerce').astype('Int64')
    df['Qtd Doc. Pendente'] = pd.to_numeric(df['Qtd Doc. Pendente'], errors='coerce').astype('Int64')

    df['Vínculo (RH)'] = df['Vínculo (RH)'].str.strip().replace('---', 'Externo')

    df = pd.merge(df, df_cpfs, on='ID', how='left')
    df = df.dropna(subset=['CBO - Unidade - Ativo no CNES'])

    def extrair_dados_cbo(texto):
        try:
            partes = str(texto).split(' - ')
            unidade = partes[2].strip() if len(partes) >= 3 else np.nan
            ativo_cnes = partes[3].strip() if len(partes) >= 4 else np.nan
            return pd.Series([unidade, ativo_cnes])
        except:
            return pd.Series([np.nan, np.nan])

    df[['Unidade', 'Ativo no CNES']] = df['CBO - Unidade - Ativo no CNES'].apply(extrair_dados_cbo)

    colunas_finais = [
        'ID', 'CPF', 'Profissional', 'Vínculo (RH)', 'Unidade', 'Ativo no CNES',
        'Qtd Doc. Pendente', 'Data Última Assinatura', 'Liberação'
    ]
    return df[colunas_finais]


def colorir_cnes(val):
    if val == 'Sim':
        return 'color: #198754; font-weight: bold;'
    elif val == 'Não':
        return 'color: #dc3545; font-weight: bold;'
    return ''


# --- INTERFACE STREAMLIT ---

st.title("📊 Painel ETL: Assinaturas Pendentes")

st.sidebar.header("📂 Entrada de Dados")
uploaded_file = st.sidebar.file_uploader("Suba o arquivo CSV aqui", type=["csv"])

if uploaded_file is not None:
    with st.spinner("Estruturando os dados..."):
        df_limpo = processar_dados(uploaded_file)

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtros")

    unidades_disponiveis = sorted(df_limpo['Unidade'].dropna().unique().tolist())
    vinculos_disponiveis = sorted(df_limpo['Vínculo (RH)'].dropna().unique().tolist())

    unidades_selecionadas = st.sidebar.multiselect("Filtrar por Unidade", options=unidades_disponiveis)
    vinculos_selecionados = st.sidebar.multiselect("Filtrar por Vínculo", options=vinculos_disponiveis)

    df_filtrado = df_limpo.copy()
    if unidades_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['Unidade'].isin(unidades_selecionadas)]
    if vinculos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['Vínculo (RH)'].isin(vinculos_selecionados)]

    df_unicos = df_filtrado.drop_duplicates(subset=['ID'])
    soma_docs = df_unicos['Qtd Doc. Pendente'].sum()
    soma_formatada = f"{soma_docs:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    col1, col2 = st.columns(2)
    col1.metric("👥 Total de Linhas (Lotações)", len(df_filtrado))
    col2.metric("📑 Soma de Docs. Pendentes (Únicos)", soma_formatada)

    st.divider()

    st.subheader("📈 Ranking de Pendências por Unidade")
    df_grafico_base = df_filtrado.drop_duplicates(subset=['ID', 'Unidade'])
    df_agrupado = df_grafico_base.groupby('Unidade', as_index=False)['Qtd Doc. Pendente'].sum()
    df_agrupado = df_agrupado.rename(columns={'Qtd Doc. Pendente': 'Docs_Pendentes'})

    grafico = alt.Chart(df_agrupado).mark_bar(color='#1f77b4').encode(
        x=alt.X('Unidade:N', sort='-y', title='Unidade de Saúde', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Docs_Pendentes:Q', title='Qtd de Documentos'),
        tooltip=[alt.Tooltip('Unidade:N', title='Unidade'),
                 alt.Tooltip('Docs_Pendentes:Q', title='Documentos Pendentes')]
    ).properties(height=400)

    st.altair_chart(grafico, use_container_width=True)

    st.divider()

    st.subheader("📋 Detalhamento dos Registros")

    # Configuração de formatação extra para garantir que o Streamlit não coloque vírgula de milhar no ID
    formatacao = {'ID': '{:.0f}'}

    st.dataframe(
        df_filtrado.style.map(colorir_cnes, subset=['Ativo no CNES']).format(formatacao, na_rep=''),
        use_container_width=True,
        hide_index=True
    )

    # --- EXPORTAÇÃO DUPLA (CSV e EXCEL) ---
    st.sidebar.divider()
    st.sidebar.header("📥 Exportar Dados")

    # 1. Download CSV
    csv = df_filtrado.to_csv(sep=';', index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📄 Baixar em CSV",
        data=csv,
        file_name="assinaturas_filtradas.csv",
        mime="text/csv",
        use_container_width=True
    )

    # 2. Download Excel
    buffer = io.BytesIO()  # Cria um arquivo Excel na memória
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name='Filtrados')

    st.sidebar.download_button(
        label="📊 Baixar em Excel (.xlsx)",
        data=buffer,
        file_name="assinaturas_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    st.info("👈 Faça o upload do arquivo `.csv` na barra lateral para iniciar.")