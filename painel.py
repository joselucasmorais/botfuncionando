import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client

# ======================================================
# 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATÓRIO SER A PRIMEIRA LINHA)
# ======================================================
st.set_page_config(page_title="Painel Admin", page_icon="🚀", layout="wide")

# ======================================================
# 2. RECUPERAÇÃO DE SEGREDOS (CÓDIGO LIMPO)
# ======================================================
try:
    # O Python vai buscar os valores na caixa "Secrets" do Streamlit Cloud.
    # Não coloque os links ou chaves aqui, apenas os nomes entre colchetes.
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    ASAAS_KEY = st.secrets["ASAAS_KEY"]
    CPF_CLIENTE = st.secrets["CPF_CLIENTE"]
    CLIENT_TEST_ID = st.secrets["CLIENT_TEST_ID"]
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
    st.error("Falha ao conectar com o Supabase. Verifique a URL e a KEY nos Secrets.")
    st.stop()

# ======================================================
# 4. FUNÇÕES DO SISTEMA (LÓGICA)
# ======================================================

def buscar_saldo():
    """Busca o saldo atual da conta Asaas"""
    if not ASAAS_KEY:
        st.warning("Chave do Asaas não configurada.")
        return 0.00
        
    url = "https://www.asaas.com/api/v3/finance/balance"
    headers = {"access_token": ASAAS_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('balance', 0.00)
        st.error(f"Erro {response.status_code} ao buscar saldo.")
        return 0.00
    except Exception as e:
        st.error(f"Erro ao conectar com Asaas: {e}")
        return 0.00

@st.cache_data(ttl=60)
def get_all_creators():
    """Busca usuários para login"""
    try:
        # Busca dados no Supabase
        resp = supabase.table("creators").select("id, username, name, password_hash").execute()
        # Tratamento seguro para diferentes versões da biblioteca
        data = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None)
        
        if not data:
            return [], [], [], []
            
        usernames = [d.get('username') for d in data]
        names = [d.get('name') for d in data]
        hashed_passwords = [d.get('password_hash') for d in data]
        return usernames, names, hashed_passwords, data
    except Exception as e:
        st.error(f"Erro ao buscar criadores no banco: {e}")
        return [], [], [], []

def fetch_filtered_data(table_name, creator_id):
    """Busca dados no banco filtrados"""
    try:
        resp = supabase.table(table_name).select("*").execute()
        data = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None)
        return data if data else []
    except:
        return []

# ======================================================
# 5. SISTEMA DE LOGIN E NAVEGAÇÃO
# ======================================================

usernames, names, hashed_passwords, creators_data = get_all_creators()

if not usernames:
    st.warning("Nenhum usuário encontrado na tabela 'creators' do Supabase.")
    st.stop()

# Configuração do Autenticador
authenticator = stauth.Authenticate(
    names, 
    usernames, 
    hashed_passwords, 
    'cookie_vibbox', 
    'chave_assinatura_secreta', 
    cookie_expiry_days=30
)

# Tela de Login
name, authentication_status, username = authenticator.login('Acesso Restrito', 'main')

# Lógica Pós-Login
if authentication_status:
    # Recupera o ID do criador logado
    matching_creator = [d for d in creators_data if d.get('username') == username]
    
    if matching_creator:
        creator_id = matching_creator[0].get('id')
    else:
        st.error("Erro ao identificar ID do usuário.")
        st.stop()
    
    st.sidebar.success(f"Olá, {name}!")
    authenticator.logout('Sair', 'sidebar')
    
    aba = st.sidebar.radio("Menu Principal", ["Dashboard", "Produtos", "Financeiro"])
    st.sidebar.divider()

    # --- ABA DASHBOARD ---
    if aba == "Dashboard":
        st.title("📊 Visão Geral")
        if st.button("Atualizar Dados"):
            st.rerun()
            
        dados_leads = fetch_filtered_data("usuarios", creator_id)
        
        if dados_leads:
            df = pd.DataFrame(dados_leads)
            
            # Verificações de segurança para colunas
            total = len(df)
            vips = len(df[df['status'] == 'cliente_vip']) if 'status' in df.columns else 0
            faturamento = vips * 10.00 
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Leads Totais", total)
            c2.metric("Vendas VIP", vips)
            c3.metric("Faturamento (Est.)", f"R$ {faturamento:.2f}")
            
            st.divider()
            
            # Mostra apenas colunas que existem
            cols_to_show = [c for c in ['nome', 'status', 'telegram_id', 'created_at'] if c in df.columns]
            st.dataframe(df[cols_to_show], use_container_width=True)
        else:
            st.info("Ainda não há dados de clientes.")

    # --- ABA PRODUTOS ---
    elif aba == "Produtos":
        st.title("📦 Meus Produtos")
        st.info("Aqui você poderá adicionar e editar seus produtos em breve.")

    # --- ABA FINANCEIRO ---
    elif aba == "Financeiro":
        st.title("💸 Financeiro")
        saldo = buscar_saldo()
        st.metric("Saldo Asaas Disponível", f"R$ {saldo:.2f}")
        
        st.divider()
        st.subheader("Configurar Conta de Saque")
        
        with st.form("form_banco"):
            st.caption("Dados para onde o dinheiro será enviado (PIX/TED).")
            banco = st.text_input("Banco")
            agencia = st.text_input("Agência")
            conta = st.text_input("Conta")
            tipo = st.selectbox("Tipo", ["corrente", "poupanca"])
            
            if st.form_submit_button("Salvar Dados"):
                try:
                    # Converte o ID do CLIENTE_TEST_ID (que vem como string dos secrets) para número
                    id_numerico = int(str(CLIENT_TEST_ID))
                    
                    dados = {
                        "user_telegram_id": id_numerico,
                        "banco_nome": banco,
                        "agencia": agencia,
                        "conta": conta,
                        "tipo_conta": tipo
                    }
                    supabase.table("contas_bancarias").upsert(dados).execute()
                    st.success("Dados bancários salvos com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# Mensagens de Erro de Login
elif authentication_status == False:
    st.error('Usuário ou senha incorretos.')
elif authentication_status == None:
    st.warning('Por favor, faça login para acessar o sistema.')
