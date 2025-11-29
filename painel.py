import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client

# ======================================================
# 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATÓRIO SER A PRIMEIRA LINHA STREAMLIT)
# ======================================================
st.set_page_config(page_title="Painel Admin", page_icon="🚀", layout="wide")

# ======================================================
# 2. RECUPERAÇÃO DE SEGREDOS (DO STREAMLIT CLOUD)
# ======================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    ASAAS_KEY = st.secrets["ASAAS_KEY"]
    CPF_CLIENTE = st.secrets["CPF_CLIENTE"]
    # Converte o ID para string para evitar erros de tipo
    CLIENT_TEST_ID = str(st.secrets["CLIENT_TEST_ID"]) 
except Exception as e:
    st.error(f"Erro Crítico: Faltam chaves nos 'Secrets' do Streamlit Cloud. Detalhe: {e}")
    st.stop()

# ======================================================
# 3. CONEXÃO COM BANCO DE DADOS
# ======================================================
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase = init_connection()

if not supabase:
    st.error("Falha ao conectar com o Supabase. Verifique a URL e a KEY.")
    st.stop()

# ======================================================
# 4. FUNÇÕES DO SISTEMA (LÓGICA)
# ======================================================

def buscar_saldo():
    """Busca o saldo atual da conta Asaas"""
    url = "https://www.asaas.com/api/v3/finance/balance"
    headers = {"access_token": ASAAS_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('balance', 0.00)
        return 0.00
    except:
        return 0.00

@st.cache_data(ttl=60)
def get_all_creators():
    """Busca usuários para login"""
    try:
        data = supabase.table("creators").select("id, username, name, password_hash").execute().data
        if not data:
            return [], [], [], []
        usernames = [d['username'] for d in data]
        names = [d['name'] for d in data]
        hashed_passwords = [d['password_hash'] for d in data]
        return usernames, names, hashed_passwords, data
    except:
        return [], [], [], []

def fetch_filtered_data(table_name, creator_id):
    """Busca dados no banco (MVP: Traz tudo por enquanto)"""
    try:
        # No futuro, aqui entra o .eq('creator_id', creator_id)
        data = supabase.table(table_name).select("*").execute().data
        return data
    except:
        return []

# ======================================================
# 5. SISTEMA DE LOGIN E NAVEGAÇÃO
# ======================================================

usernames, names, hashed_passwords, creators_data = get_all_creators()

if not usernames:
    st.warning("Nenhum usuário 'creator' encontrado no banco de dados.")
    st.stop()

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 'cookie_vibbox', 'chave_assinatura', cookie_expiry_days=30)

name, authentication_status, username = authenticator.login('Acesso Restrito', 'main')

if authentication_status:
    # Login Sucesso
    creator_id = [d['id'] for d in creators_data if d['username'] == username][0]
    
    st.sidebar.success(f"Olá, {name}!")
    authenticator.logout('Sair', 'sidebar')
    
    aba = st.sidebar.radio("Menu", ["Dashboard", "Produtos", "Financeiro"])
    st.sidebar.divider()

    # --- ABA DASHBOARD ---
    if aba == "Dashboard":
        st.title("📊 Visão Geral")
        if st.button("Atualizar Dados"):
            st.rerun()
            
        dados_leads = fetch_filtered_data("usuarios", creator_id)
        
        if dados_leads:
            df = pd.DataFrame(dados_leads)
            total = len(df)
            vips = len(df[df['status'] == 'cliente_vip']) if 'status' in df.columns else 0
            faturamento = vips * 10.00 
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Leads Totais", total)
            c2.metric("Vendas VIP", vips)
            c3.metric("Faturamento (Est.)", f"R$ {faturamento:.2f}")
            
            st.divider()
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Ainda não há dados de clientes.")

    # --- ABA PRODUTOS ---
    elif aba == "Produtos":
        st.title("📦 Meus Produtos")
        st.info("Aqui ficará a gestão de produtos dinâmica.")

    # --- ABA FINANCEIRO ---
    elif aba == "Financeiro":
        st.title("💸 Financeiro")
        saldo = buscar_saldo()
        st.metric("Saldo Asaas Disponível", f"R$ {saldo:.2f}")
        
        st.divider()
        st.subheader("Configurar Conta de Saque")
        
        with st.form("form_banco"):
            st.caption("Preencha para onde o dinheiro deve ir.")
            banco = st.text_input("Banco")
            agencia = st.text_input("Agência")
            conta = st.text_input("Conta")
            tipo = st.selectbox("Tipo", ["corrente", "poupanca"])
            
            if st.form_submit_button("Salvar Dados"):
                try:
                    # Tenta converter o ID para número para salvar no banco
                    id_numerico = int(CLIENT_TEST_ID)
                    dados = {
                        "user_telegram_id": id_numerico,
                        "banco_nome": banco,
                        "agencia": agencia,
                        "conta": conta,
                        "tipo_conta": tipo
                    }
                    supabase.table("contas_bancarias").upsert(dados).execute()
                    st.success("Dados salvos!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# Tratamento de Login Falho
elif authentication_status == False:
    st.error('Usuário ou senha incorretos.')
elif authentication_status == None:
    st.warning('Por favor, faça login.')
