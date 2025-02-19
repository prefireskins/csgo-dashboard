import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# 📌 Configuração do layout da página
st.set_page_config(page_title="CSGOEmpire Dashboard", layout="wide")

# 📌 Configurar credenciais do Google Sheets (usando caminho absoluto)
import json
import streamlit as st
from google.oauth2.service_account import Credentials

# Lendo credenciais dos Secrets do Streamlit
secrets_dict = st.secrets["gcp_service_account"]
CREDENTIALS = Credentials.from_service_account_info(json.loads(json.dumps(secrets_dict)))
                                                    
# 📌 Conectar ao Google Sheets
gc = gspread.authorize(CREDENTIALS)
SHEET_ID = "1HO2lFyTNKFIm1jH6a3YA-Cus4wHY21TKrCuHdI_6DBw"
planilha = gc.open_by_key(SHEET_ID)
aba = planilha.sheet1  # Usa a primeira aba da planilha

# 📌 Função para carregar os dados do Google Sheets
def carregar_dados():
    dados = aba.get_all_records()
    return pd.DataFrame(dados)

# 📌 Função para salvar os dados no Google Sheets
def salvar_dados(df):
    aba.clear()  # Limpa os dados antigos
    aba.update([df.columns.values.tolist()] + df.values.tolist())  # Atualiza com os novos dados

# 📌 Inicializar DataFrame na sessão
if "df" not in st.session_state:
    st.session_state.df = carregar_dados()

df = st.session_state.df  # Trabalhar com os dados salvos na sessão
# Criar colunas vazias se não existirem
colunas_necessarias = [
    "Data de Compra", "Skin", "Qualidade", "Preço de Compra (USD)", 
    "Data de Venda", "Preço de Venda (USD)", "Lucro (USD)", "Lucro (%)", "Status"
]

for col in colunas_necessarias:
    if col not in df.columns:
        df[col] = None  # Adiciona a coluna vazia caso não exista

# Agora podemos converter datas sem erro
df["Data de Venda"] = pd.to_datetime(df["Data de Venda"], errors="coerce")

# 📌 Estilo personalizado para melhorar o visual
st.markdown(
    """
    <style>
        .big-font {
            font-size:20px !important;
            font-weight: bold;
            color: #FFA500;
        }
        .metric-box {
            background-color: #1E1E1E;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 18px;
            color: white;
        }
        .stButton>button {
            background-color: #FFA500 !important;
            color: white !important;
            border-radius: 10px;
            font-size: 16px;
            padding: 10px;
        }
        .stDownloadButton>button {
            background-color: #007bff !important;
            color: white !important;
            border-radius: 10px;
            font-size: 16px;
            padding: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 📌 Atualizar Lucro ao Registrar Venda
def atualizar_venda(index):
    row = df.loc[index]
    if pd.notna(row["Preço de Venda (USD)"]) and row["Preço de Venda (USD)"] and pd.notna(row["Preço de Compra (USD)"]):
        preco_venda = float(row["Preço de Venda (USD)"])
        preco_compra = float(row["Preço de Compra (USD)"])
        lucro_valor = preco_venda - preco_compra
        lucro_percentual = (lucro_valor / preco_compra) * 100 if preco_compra > 0 else 0
        df.at[index, "Lucro (USD)"] = lucro_valor
        df.at[index, "Lucro (%)"] = f"{lucro_percentual:.2f}%"
        df.at[index, "Data de Venda"] = datetime.datetime.today().date()
        df.at[index, "Status"] = "Vendida"

# 📌 Função para excluir item
def excluir_item(index):
    df.drop(index, inplace=True)
    df.reset_index(drop=True, inplace=True)

# 📌 Cálculo de Lucro por Semana
if "Data de Venda" not in df.columns:
    df["Data de Venda"] = None  # Criar a coluna vazia se não existir

df["Data de Venda"] = pd.to_datetime(df["Data de Venda"], errors="coerce")

lucro_por_semana = df.groupby(df["Data de Venda"].dt.to_period("W"))[["Lucro (USD)", "Preço de Compra (USD)"]].sum()
lucro_por_semana["Lucro (%)"] = (lucro_por_semana["Lucro (USD)"] / lucro_por_semana["Preço de Compra (USD)"]) * 100
lucro_por_semana = lucro_por_semana.fillna(0)

# 📌 Métricas Destacadas
lucro_total = df["Lucro (USD)"].sum() if not df.empty else 0
valor_total_disponivel = df[df["Status"] == "Disponível"]["Preço de Compra (USD)"].sum() if not df.empty else 0
ultima_venda = df["Data de Venda"].max().strftime('%d/%m/%Y') if pd.notna(df["Data de Venda"].max()) else "Nenhuma venda ainda"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-box">💰 <br> <b>Lucro Total</b> <br> USD {lucro_total:.2f}</div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-box">📦 <br> <b>Itens Disponíveis</b> <br> {df[df["Status"] == "Disponível"].shape[0]}</div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-box">📅 <br> <b>Última Venda</b> <br> {ultima_venda}</div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-box">📊 <br> <b>Valor Total em Skins</b> <br> USD {valor_total_disponivel:.2f}</div>', unsafe_allow_html=True)

# 📌 Exibir Lucro por Semana
st.subheader("📅 Lucro por Semana")
st.write(lucro_por_semana)

# 📌 Filtros e Ordenação
st.sidebar.subheader("🔍 Filtros e Ordenação")
status_filtro = st.sidebar.selectbox("Filtrar por status:", ["Todos", "Disponível", "Vendida"])
ordenar_por = st.sidebar.selectbox("Ordenar por:", ["Data de Compra", "Lucro (USD)", "Preço de Compra (USD)"])

if status_filtro != "Todos":
    df = df[df["Status"] == status_filtro]

df = df.sort_values(by=ordenar_por, ascending=False)

# 📌 Adicionar Nova Skin
st.subheader("➕ Adicionar Nova Skin")
with st.form("nova_skin"):
    data_compra = st.date_input("📅 Data de Compra")
    skin_nome = st.text_input("🔫 Nome da Skin")
    qualidade = st.selectbox("⭐ Qualidade", ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"])
    preco_compra = st.number_input("💰 Preço de Compra (USD)", min_value=0.0, format="%.2f")
    submit_skin = st.form_submit_button("Adicionar")
    
    if submit_skin and skin_nome:
        nova_linha = pd.DataFrame({
            "Data de Compra": [str(data_compra)],
            "Skin": [skin_nome],
            "Qualidade": [qualidade],
            "Preço de Compra (USD)": [preco_compra],
            "Data de Venda": [None],
            "Preço de Venda (USD)": [None],
            "Lucro (USD)": [None],
            "Lucro (%)": [None],
            "Status": ["Disponível"]
        })
        st.session_state.df = pd.concat([st.session_state.df, nova_linha], ignore_index=True)
        salvar_dados(st.session_state.df)
        st.success(f"✅ Nova skin adicionada: {skin_nome} ({qualidade})!")

# 📌 Tabela Interativa
st.subheader("📌 Histórico de Compras e Vendas")
st.dataframe(df.style.format({"Lucro (USD)": "${:.2f}", "Preço de Compra (USD)": "${:.2f}"}))

# 📌 Salvar Alterações
if st.button("✅ Salvar Alterações"):
    salvar_dados(df)
    st.success("✅ Dados atualizados!")
    st.rerun()
