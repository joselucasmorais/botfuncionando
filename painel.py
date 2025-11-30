import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client
from datetime import datetime

# ======================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ======================================================
st.set_page_config(page_title="PlayBot Creator", page_icon="🚀", layout="wide")

# ======================================================
# 2. SEGREDOS (DO STREAMLIT CLOUD)
# ======================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    # As chaves globais (ASAAS_KEY) ficam aqui como fallback, 
    # mas o ideal é buscar do cliente no banco.
except Exception as e:
    st.error(f"Erro nos Secrets: {e}")
    st.stop()

# ======================================================
# 3. CONEXÃO BANCO
# ======================================================
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase = init_connection()

# ======================================================
# 4. FUNÇÕES DE LÓGICA
# ======================================================
@st.cache_data(ttl=60)
def get_all_creators():
    try:
        # Busca usuários para login
        resp = supabase.table("creators").select("id, username, name, password_hash").execute()
        data = getattr(resp, "data", [])
        if not data: return [], [], [], []
        
        usernames = [d.get('username') for d in data]
        names = [d.get('name') for d in data]
        hashed_passwords = [d.get('password_hash') for d in data]
        return usernames, names, hashed_passwords, data
    except:
        return [], [], [], []

def get_creator_data(table, creator_id):
    """Busca dados de uma tabela filtrando pelo dono (creator_id)"""
    try:
        resp = supabase.table(table).select("*").eq("creator_id", creator_id).execute()
        return getattr(resp, "data", [])
    except:
        return []

# ======================================================
# 5. SISTEMA DE LOGIN
# ======================================================
usernames, names, hashed_passwords, creators_data = get_all_creators()

authenticator = stauth.Authenticate(
    names, usernames, hashed_passwords, 
    'cookie_playbot', 'chave_assinatura', cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Acesso PlayBot', 'main')

if authentication_status:
    # PEGA O ID DO CRIADOR LOGADO (ESSENCIAL!)
    creator_id = [d['id'] for d in creators_data if d['username'] == username][0]
    
    # --- BARRA LATERAL (MENU VIBX) ---
    st.sidebar.title(f"Olá, {name}!")
    st.sidebar.divider()
    
    menu = st.sidebar.radio(
        "Menu Principal",
        ["📊 Dashboard", "👥 Comunidades", "📦 Ofertas/Produtos", "💸 Financeiro", "⚙️ Configurações do Bot"]
    )
    
    st.sidebar.divider()
    authenticator.logout('Sair', 'sidebar')

    # ======================================================
    # TELA: DASHBOARD
    # ======================================================
    if menu == "📊 Dashboard":
        st.title("📊 Visão Geral")
        
        # Filtro de Data (Visual)
        col_d1, col_d2 = st.columns([3,1])
        periodo = col_d2.selectbox("Período", ["Hoje", "Últimos 7 dias", "Este Mês"])
        
        # Busca vendas reais desse cliente
        vendas = get_creator_data("vendas", creator_id)
        
        if vendas:
            df = pd.DataFrame(vendas)
            total_vendas = df['valor_total'].sum()
            qtd_vendas = len(df)
            # Líquido (Simulação: Total - 7%)
            liquido = total_vendas * 0.93 
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Vendas (Valor)", f"R$ {total_vendas:.2f}")
            c2.metric("Vendas (Qtd)", qtd_vendas)
            c3.metric("Líquido Estimado", f"R$ {liquido:.2f}")
            
            st.divider()
            st.subheader("Histórico Recente")
            st.dataframe(df[['created_at', 'produto_nome', 'valor_total', 'status']], use_container_width=True)
        else:
            st.info("Nenhuma venda registrada ainda. Configure seu bot e comece a vender!")

    # ======================================================
    # TELA: COMUNIDADES (GRUPOS)
    # ======================================================
    elif menu == "👥 Comunidades":
        st.title("👥 Suas Comunidades")
        st.markdown("Gerencie os grupos VIP onde o bot adicionará os clientes.")
        
        with st.expander("➕ Adicionar Nova Comunidade"):
            with st.form("add_comunidade"):
                nome_grupo = st.text_input("Nome do Grupo (ex: VIP Lorrana)")
                chat_id = st.text_input("ID do Telegram (ex: -100...)")
                if st.form_submit_button("Salvar"):
                    supabase.table("comunidades").insert({
                        "creator_id": creator_id,
                        "nome": nome_grupo,
                        "telegram_chat_id": chat_id
                    }).execute()
                    st.success("Grupo salvo!")
                    st.rerun()
        
        grupos = get_creator_data("comunidades", creator_id)
        if grupos:
            st.dataframe(pd.DataFrame(grupos)[['nome', 'telegram_chat_id']], use_container_width=True)

    # ======================================================
    # TELA: OFERTAS / PRODUTOS
    # ======================================================
    elif menu == "📦 Ofertas/Produtos":
        st.title("📦 Suas Ofertas")
        
        with st.expander("➕ Criar Nova Oferta"):
            with st.form("add_offer"):
                nome_prod = st.text_input("Nome da Oferta")
                preco = st.number_input("Preço (R$)", min_value=1.00)
                tipo = st.selectbox("Tipo", ["Pack (Pagamento Único)", "Assinatura Mensal"])
                link = st.text_input("Link do Canal/Grupo de Entrega")
                
                if st.form_submit_button("Criar Oferta"):
                    supabase.table("produtos").insert({
                        "creator_id": creator_id,
                        "nome": nome_prod,
                        "preco": preco,
                        "tipo": tipo,
                        "link_entrega": link
                    }).execute()
                    st.success("Oferta criada!")
                    st.rerun()
                    
        prods = get_creator_data("produtos", creator_id)
        if prods:
            st.dataframe(pd.DataFrame(prods)[['nome', 'preco', 'tipo', 'link_entrega']], use_container_width=True)

    # ======================================================
    # TELA: FINANCEIRO (SAQUE)
    # ======================================================
    elif menu == "💸 Financeiro":
        st.title("💸 Área de Saque")
        
        # 1. Cadastro da Conta Bancária
        st.subheader("Sua Conta Bancária")
        contas = get_creator_data("contas_bancarias", creator_id)
        
        if not contas:
            st.warning("Cadastre sua conta para receber.")
            with st.form("bank_form"):
                banco = st.text_input("Banco")
                agencia = st.text_input("Agência")
                conta = st.text_input("Conta")
                pix = st.text_input("Chave PIX")
                if st.form_submit_button("Salvar Conta"):
                    supabase.table("contas_bancarias").insert({
                        "creator_id": creator_id,
                        "banco_nome": banco, "agencia": agencia, "conta": conta, "pix_chave": pix
                    }).execute()
                    st.rerun()
        else:
            c = contas[0]
            st.success(f"Conta Cadastrada: {c['banco_nome']} - Ag: {c['agencia']} CC: {c['conta']}")
            if st.button("Editar Conta"):
                # Lógica de deletar para recriar (MVP)
                supabase.table("contas_bancarias").delete().eq("creator_id", creator_id).execute()
                st.rerun()

        st.divider()
        st.subheader("Solicitar Saque")
        valor_saque = st.number_input("Valor", min_value=0.0)
        if st.button("Solicitar Transferência"):
            st.info("Solicitação enviada! O processamento é automático em até 24h.")

    # ======================================================
    # TELA: CONFIGURAÇÕES DO BOT (CRUCIAL PARA O CLIENTE)
    # ======================================================
    elif menu == "⚙️ Configurações do Bot":
        st.title("⚙️ Configuração do Seu Robô")
        st.info("Aqui você conecta o seu Bot do Telegram e sua conta Asaas.")
        
        # Tenta buscar configuração existente
        configs = get_creator_data("config_bots", creator_id)
        
        with st.form("config_bot_form"):
            token_atual = configs[0]['telegram_token'] if configs else ""
            asaas_atual = configs[0]['asaas_key'] if configs else ""
            wallet_atual = configs[0]['wallet_id'] if configs else ""
            
            st.subheader("1. Telegram")
            token = st.text_input("Token do Bot (@BotFather)", value=token_atual, type="password")
            
            st.subheader("2. Financeiro (Asaas)")
            asaas = st.text_input("Chave de API do Asaas ($aact...)", value=asaas_atual, type="password")
            wallet = st.text_input("Wallet ID (Opcional - Para Split)", value=wallet_atual)
            
            if st.form_submit_button("Salvar Conexão"):
                dados_config = {
                    "creator_id": creator_id,
                    "telegram_token": token,
                    "asaas_key": asaas,
                    "wallet_id": wallet
                }
                
                # Verifica se já existe para atualizar ou criar
                if configs:
                    # Update
                    supabase.table("config_bots").update(dados_config).eq("creator_id", creator_id).execute()
                else:
                    # Insert
                    supabase.table("config_bots").insert(dados_config).execute()
                    
                st.success("✅ Robô Configurado! As alterações entram em vigor em instantes.")

# Se não estiver logado
elif authentication_status == False:
    st.error('Login incorreto')
elif authentication_status == None:
    st.warning('Faça login para acessar a PlayBot.')
