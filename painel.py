import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# 🔐 CONFIGURAÇÃO DE CHAVES E ACESSO
# ======================================================
import streamlit as st

SUPABASE_URL = st.secrets["https://fygapkucfwgdynbiyfcz.supabase.co"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5Z2Fwa3VjZndnZHluYml5ZmN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDMwNTI0NywiZXhwIjoyMDc5ODgxMjQ3fQ.V_IpDzhosRCecUENzdAB3bzQrfg2BfjU-op_SyXLvqk"]

ASAAS_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjQ5NDI5MGU3LTU1NzktNGI3NS04MThkLWMzMjA0YTIxOGZmYzo6JGFhY2hfMWEyMjU1MmYtNjZkZS00NGM3LTkzNWUtYTMzMjAzZWM0NTI5"
# --- VARIÁVEL DE TESTE 
CLIENT_TEST_ID = 6519700996
# ======================================================

# Configuração da Página (LAYOUT TEM QUE SER A PRIMEIRA COISA)
st.set_page_config(page_title="Painel de Clientes", page_icon="🔒", layout="wide")

# --- CONEXÃO GERAL ---
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro Supabase: {e}")
        return None

supabase = init_connection()

# =======================
# Funções auxiliares
# =======================
# Implemente ou importe as funções a seguir no módulo
# def get_all_creators(): ...
# def fetch_filtered_data(table, creator_id): ...

def buscar_saldo():
    """Busca o saldo atual da conta Asaas da cliente"""
    url = "https://www.asaas.com/api/v3/finance/balance"
    headers = {"access_token": ASAAS_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('balance', 0.00)
        st.error(f"Erro {response.status_code} ao buscar saldo.")
        return 0.00
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão com Asaas: {e}")
        return 0.00
    except Exception as e:
        st.error(f"Erro de dados no saldo: {e}")
        return 0.00

# ======================================================
# 1. AUTENTICAÇÃO E INÍCIO DO FLUXO
# ======================================================
# --- FUNÇÕES DE LÓGICA DE NEGÓCIO ---

@st.cache_data(ttl=60)
def get_all_creators():
    """Busca utilizadores (criadores) do banco para autenticação"""
    try:
        data = supabase.table("creators").select("id, username, name, password_hash").execute().data
        usernames = [d['username'] for d in data]
        names = [d['name'] for d in data]
        hashed_passwords = [d['password_hash'] for d in data]
        return usernames, names, hashed_passwords, data
    except Exception as e:
        st.error(f"Erro ao buscar criadores: {e}")
        return [], [], [], []
usernames, names, hashed_passwords, creators_data = get_all_creators()
# O hash usado deve ser bcrypt
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 'autenticador', 'abcdef', cookie_expiry_days=30)

# Tenta fazer login
name, authentication_status, username = authenticator.login('Login do Cliente', 'main')

# 2. SE A AUTENTICAÇÃO FOR BEM SUCEDIDA: MOSTRA O DASHBOARD
if authentication_status:
    creator_id = [d['id'] for d in creators_data if d['username'] == username][0]
    
    st.sidebar.success(f"Logado como: {name}")
    authenticator.logout('Sair', 'sidebar')

    aba = st.sidebar.radio("Navegar", ["Dashboard", "Produtos", "Financeiro"])
    st.sidebar.divider()

    # --- ABA 1: DASHBOARD ---
    if aba == "Dashboard":
        st.title("🚀 Dashboard de Vendas")

        # Busca dados, agora filtrados
        df_usuarios_data = fetch_filtered_data("usuarios", creator_id)
        
        if df_usuarios_data:
            df = pd.DataFrame(df_usuarios_data)
            vips = len(df[df['status'] == 'cliente_vip'])
            faturamento = vips * 10.00 # Estimativa
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Clientes VIP", vips)
            col2.metric("Faturamento Estimado", f"R$ {faturamento:.2f}")
            col3.metric("Total de Leads", len(df))

            st.divider()
            st.subheader("📋 Clientes Registrados")
            st.dataframe(df[['nome', 'status', 'telegram_id', 'created_at']], use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para este criador.")

    # --- ABA 2: PRODUTOS (SIMPLIFICADO) ---
    elif aba == "Produtos":
        st.title("📦 Gestão de Produtos")
        st.warning("Aqui você adicionaria o formulário para a cliente gerir os produtos na tabela 'produtos'.")

    # --- ABA 3: FINANCEIRO (SAQUE SELF-SERVICE) ---
    elif aba == "Financeiro":
        st.title("💸 Gestão Financeira Self-Service")
        saldo = buscar_saldo()
        st.metric("Saldo Asaas", f"R$ {saldo:.2f}")

        # Formulário de cadastro da conta bancária
        st.subheader("⚙️ Cadastrar/Atualizar Conta de Saque")

        with st.form("form_cadastro_bancario"):
            st.caption("Você só precisa preencher isso uma vez.")
            CLIENT_ID_NUMERICO = int(CLIENT_TEST_ID)

            col_banco, col_ag = st.columns(2)
            banco_nome = col_banco.text_input("Banco (Nome ou Código)")
            agencia = col_ag.text_input("Agência")

            col_conta, col_tipo = st.columns(2)
            conta = col_conta.text_input("Conta (Número)")
            tipo_conta = col_tipo.selectbox("Tipo de Conta", ['corrente', 'poupanca'])

            submitted_cadastro = st.form_submit_button("Salvar/Atualizar Conta de Saque")
            if submitted_cadastro:
                dados_banco = {
                    "user_telegram_id": CLIENT_ID_NUMERICO,
                    "banco_nome": banco_nome,
                    "agencia": agencia,
                    "conta": conta,
                    "tipo_conta": tipo_conta
                }
                supabase.table("contas_bancarias").upsert(dados_banco).execute()
                st.success("✅ Dados bancários atualizados!")

        st.divider()
        st.info("Para sacar, preencha o formulário acima e clique em 'Realizar Saque'.")

# 3. SE A AUTENTICAÇÃO FALHAR OU NÃO TENTOU
elif authentication_status == False:
    st.error('Nome de utilizador/palavra-passe incorretos')
elif authentication_status is None:
    st.warning('Por favor, insira o seu nome de utilizador e palavra-passe para aceder ao Painel.')
   # Verifica se a conexão com Supabase foi inicializada
if supabase is None:
    st.error("Erro: conexão com Supabase não inicializada.")
    st.stop()














