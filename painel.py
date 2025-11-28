import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client

# ======================================================
# 🔐 CONFIGURAÇÃO DE CHAVES E ACESSO
# ======================================================
SUPABASE_URL = "https://fygapkucfwgdynbiyfcz.supabase.co/" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5Z2Fwa3VjZndnZHluYml5ZmN6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzMDUyNDcsImV4cCI6MjA3OTg4MTI0N30.ZTxjl8OYB-9nZtBEhTq8iNIIOFNUyJHBH58VK_XPS1E"
ASAAS_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjQ5NDI5MGU3LTU1NzktNGI3NS04MThkLWMzMjA0YTIxOGZmYzo6JGFhY2hfMWEyMjU1MmYtNjZkZS00NGM3LTkzNWUtYTMzMjAzZWM0NTI5"
CPF_CLIENTE = "141.214.394.22" 
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
    except:
        return None

supabase = init_connection()

# --- FUNÇÕES DE BUSCA (get_all_creators) ---
# ... (manter a função get_all_creators e buscar_saldo aqui) ...

# ======================================================
# 1. AUTENTICAÇÃO E INÍCIO DO FLUXO
# ======================================================

usernames, names, hashed_passwords, creators_data = get_all_creators()

# NOTE: Use o hash do bcrypt, mesmo que o nome da variável seja 'hashed_passwords'
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 'autenticador', 'abcdef', cookie_expiry_days=30)

# Tenta fazer login
name, authentication_status, username = authenticator.login('Login do Cliente', 'main')

# 2. SE A AUTENTICAÇÃO FOR BEM SUCEDIDA: MOSTRA O DASHBOARD
if authentication_status:
    # O restante do código do Dashboard (Abas 1, 2, 3) está aqui, INDENTADO.
    # Se você colou o último bloco de código completo, essa parte está OK.
    
    # ... (começa o código do Dashboard) ...
    pass
    
# 3. SE A AUTENTICAÇÃO FALHAR OU NÃO TENTOU
def buscar_saldo():      # <--- CORRETO!
    """Busca o saldo atual da conta Asaas da cliente"""
    url = "https://www.asaas.com/api/v3/finance/balance"
    headers = {"access_token": ASAAS_KEY}
    try:
        response = requests.get(url, headers=headers)
if response.status_code == 200:
            return response.json().get('balance', 0.00)
        st.error(f"Erro {response.status_code} ao buscar saldo.")
        return 0.00 # Linha de retorno do try/if
    except requests.exceptions.RequestException as e:
        # Erro de conexão
        st.error(f"Erro de conexão com Asaas: {e}")
        return 0.00
    except Exception as e:
        # Erro geral de JSON/parsing
        st.error(f"Erro de dados no saldo: {e}")
        return 0.00

# ======================================================
# 1. AUTENTICAÇÃO E INÍCIO DO FLUXO
# ======================================================

usernames, names, hashed_passwords, creators_data = get_all_creators()
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 'autenticador', 'abcdef', cookie_expiry_days=30)

# Tenta fazer login
name, authentication_status, username = authenticator.login('Login do Cliente', 'main')

# 2. SE A AUTENTICAÇÃO FOR BEM SUCEDIDA: MOSTRA O DASHBOARD
if authentication_status:
    creator_id = [d['id'] for d in creators_data if d['username'] == username][0]
    
    st.sidebar.success(f"Logado como: {name}")
    authenticator.logout('Sair', 'sidebar') # Botão de Logout

    # --- ABA DE NAVEGAÇÃO ---
    aba = st.sidebar.radio("Navegar", ["Dashboard", "Produtos", "Financeiro"])
    st.sidebar.divider()
    
    # --- ABA 1: DASHBOARD ---
if aba == "Dashboard":
        st.title("🚀 Dashboard de Vendas")
        
        # Busca dados, agora filtrados (MVP: A busca não está filtrando por creator_id ainda, mas o sistema está pronto)
        df_usuarios_data = fetch_filtered_data("usuarios", creator_id)
        
        # O restante do código do dashboard (cálculos, gráficos e tabelas)
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
def buscar_saldo():      # <-- CORRETO!
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
        # Erro de conexão
        st.error(f"Erro de conexão com Asaas: {e}")
        return 0.00
    except Exception as e:
        # Erro geral de JSON/parsing
        st.error(f"Erro de dados no saldo: {e}")
        return 0.00

        # 2. FORMULÁRIO DE CADASTRO DA CONTA BANCÁRIA
        st.subheader("⚙️ Cadastrar/Atualizar Conta de Saque")

        with st.form("form_cadastro_bancario"):
            st.caption("Você só precisa preencher isso uma vez.")
            
            # Use CLIENT_TEST_ID temporário, pois o creator_id do Streamlit é um texto
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
                # Salva os dados na tabela contas_bancarias
                supabase.table("contas_bancarias").upsert(dados_banco).execute()
                st.success("✅ Dados bancários atualizados!")

        st.divider()
        st.info("Para sacar, preencha o formulário acima e clique em 'Realizar Saque'.")
        
# 3. SE A AUTENTICAÇÃO FALHAR OU NÃO TENTOU
elif authentication_status == False:
    st.error('Nome de utilizador/palavra-passe incorretos')
elif authentication_status == None:
    st.warning('Por favor, insira o seu nome de utilizador e palavra-passe para aceder ao Painel.')
