import os
import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client

# ======================================================
# CONFIGURAÇÃO DE CHAVES E ACESSO (usar Streamlit Secrets ou variáveis de ambiente)
# ======================================================
# No Streamlit Cloud: Settings → Secrets
# Exemplo de keys no Secrets:
# SUPABASE_URL = "https://<seu-projeto>.supabase.co"
# SUPABASE_KEY = "eyJ..."
# ASAAS_KEY = "seu_asaas_key_aqui"

SUPABASE_URL = st.secrets.get("https://fygapkucfwgdynbiyfcz.supabase.co/") 
SUPABASE_KEY = st.secrets.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5Z2Fwa3VjZndnZHluYml5ZmN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDMwNTI0NywiZXhwIjoyMDc5ODgxMjQ3fQ.V_IpDzhosRCecUENzdAB3bzQrfg2BfjU-op_SyXLvqk") or os.environ.get("SUPABASE_KEY")
ASAAS_KEY = st.secrets.get("$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjQ5NDI5MGU3LTU1NzktNGI3NS04MThkLWMzMjA0YTIxOGZmYzo6JGFhY2hfMWEyMjU1MmYtNjZkZS00NGM3LTkzNWUtYTMzMjAzZWM0NTI5") 
CLIENT_TEST_ID = st.secrets.get("CLIENT_TEST_ID") or os.environ.get("CLIENT_TEST_ID") or 6519700996

# Validação imediata das credenciais
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("SUPABASE_URL ou SUPABASE_KEY não configurados. Configure em Streamlit Secrets ou variáveis de ambiente.")
    st.stop()

# Configuração da Página (LAYOUT TEM QUE SER A PRIMEIRA COISA)
st.set_page_config(page_title="Painel de Clientes", page_icon="🔒", layout="wide")

# --- CONEXÃO GERAL ---
@st.cache_resource
def init_connection(url: str, key: str):
    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error(f"Erro ao inicializar Supabase: {e}")
        return None

supabase = init_connection(SUPABASE_URL, SUPABASE_KEY)

# Verifica se a conexão com Supabase foi inicializada
if supabase is None:
    st.error("Erro: conexão com Supabase não inicializada.")
    st.stop()

# =======================
# Funções auxiliares
# =======================
def fetch_filtered_data(table: str, creator_id):
    """Busca dados filtrados por creator_id. Retorna lista (ou [])"""
    try:
        resp = supabase.table(table).select("*").eq("creator_id", creator_id).execute()
        # Dependendo da versão do client, o resultado pode estar em resp.data ou resp.get('data')
        data = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None)
        if data is None:
            return []
        return data
    except Exception as e:
        st.error(f"Erro ao buscar dados da tabela {table}: {e}")
        return []

def buscar_saldo():
    """Busca o saldo atual da conta Asaas da cliente"""
    if not ASAAS_KEY:
        st.warning("ASAAS_KEY não configurada. Saldo indisponível.")
        return 0.00

    url = "https://www.asaas.com/api/v3/finance/balance"
    headers = {"access_token": ASAAS_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
@st.cache_data(ttl=60)
def get_all_creators():
    """Busca utilizadores (criadores) do banco para autenticação"""
    try:
        resp = supabase.table("creators").select("id, username, name, password_hash").execute()
        data = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None)
        if not data:
            return [], [], [], []
        usernames = [d.get('username') for d in data]
        names = [d.get('name') for d in data]
        hashed_passwords = [d.get('password_hash') for d in data]
        return usernames, names, hashed_passwords, data
    except Exception as e:
        st.error(f"Erro ao buscar criadores: {e}")
        return [], [], [], []

usernames, names, hashed_passwords, creators_data = get_all_creators()

# Se não houver criadores cadastrados, interrompe com mensagem clara
if not creators_data:
    st.warning("Nenhum criador encontrado no banco. Verifique a tabela 'creators' no Supabase.")
    st.stop()

# O stauth aceita listas, mas precisamos garantir que não estão vazias
try:
    authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 'autenticador', 'abcdef', cookie_expiry_days=30)
except Exception as e:
    st.error(f"Erro ao inicializar o autenticador: {e}")
    st.stop()

# Tenta fazer login
name, authentication_status, username = authenticator.login('Login do Cliente', 'main')

# 2. SE A AUTENTICAÇÃO FOR BEM SUCEDIDA: MOSTRA O DASHBOARD
if authentication_status:
    # Proteção contra IndexError: busca segura do creator_id
    matching = [d for d in creators_data if d.get('username') == username]
    if not matching:
        st.error("Usuário autenticado não encontrado na lista de criadores.")
        st.stop()
    creator_id = matching[0].get('id')

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
            # Proteções caso colunas não existam
            if 'status' in df.columns:
                vips = len(df[df['status'] == 'cliente_vip'])
            else:
                vips = 0
            faturamento = vips * 10.00  # Estimativa

            col1, col2, col3 = st.columns(3)
            col1.metric("Clientes VIP", vips)
            col2.metric("Faturamento Estimado", f"R$ {faturamento:.2f}")
            col3.metric("Total de Leads", len(df))

            st.divider()
            st.subheader("📋 Clientes Registrados")
            # Proteção para colunas exibidas
            display_cols = [c for c in ['nome', 'status', 'telegram_id', 'created_at'] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True)
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
            try:
                CLIENT_ID_NUMERICO = int(CLIENT_TEST_ID)
            except Exception:
                CLIENT_ID_NUMERICO = CLIENT_TEST_ID

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
                try:
                    supabase.table("contas_bancarias").upsert(dados_banco).execute()
                    st.success("✅ Dados bancários atualizados!")
                except Exception as e:
                    st.error(f"Erro ao salvar dados bancários: {e}")

        st.divider()
        st.info("Para sacar, preencha o formulário acima e clique em 'Realizar Saque'.")

# 3. SE A AUTENTICAÇÃO FALHAR OU NÃO TENTOU
elif authentication_status == False:
    st.error('Nome de utilizador/palavra-passe incorretos')
elif authentication_status is None:
    st.warning('Por favor, insira o seu nome de utilizador e palavra-passe para aceder ao Painel.')
