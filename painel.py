import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
from supabase import create_client
from datetime import datetime

# ======================================================
# 1. CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM
# ======================================================
st.set_page_config(page_title="PlayBot Admin", page_icon="⚡", layout="wide")

# --- CSS PERSONALIZADO (A MÁGICA VISUAL) ---
st.markdown("""
<style>
    /* Fundo geral mais limpo */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Estilo dos Cartões de Métricas (Cards) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        color: #333;
    }
    
    /* Títulos mais bonitos */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #1f1f1f;
    }
    
    /* Botões mais modernos (Roxos estilo SaaS) */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }
    
    /* Remover menu padrão do Streamlit (Hambúrguer) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar mais limpa */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# 2. SEGREDOS & CONEXÃO
# ======================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception as e:
    st.error("Erro crítico: Configure os Secrets no Streamlit Cloud.")
    st.stop()

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase = init_connection()

# ======================================================
# 3. FUNÇÕES (LÓGICA)
# ======================================================
@st.cache_data(ttl=60)
def get_all_creators():
    try:
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
    try:
        resp = supabase.table(table).select("*").eq("creator_id", creator_id).execute()
        return getattr(resp, "data", [])
    except:
        return []

# ======================================================
# 4. FLUXO PRINCIPAL
# ======================================================
usernames, names, hashed_passwords, creators_data = get_all_creators()

if not usernames:
    st.warning("Sistema em manutenção (Sem usuários).")
    st.stop()

authenticator = stauth.Authenticate(
    names, usernames, hashed_passwords, 
    'playbot_cookie', 'assinatura_segura', cookie_expiry_days=30
)

# TELA DE LOGIN CENTRALIZADA
if st.session_state.get('authentication_status') is not True:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## ⚡ Acesso PlayBot")
        name, authentication_status, username = authenticator.login('Entrar', 'main')

if st.session_state.get('authentication_status'):
    # LÓGICA DO USUÁRIO LOGADO
    creator_id = [d['id'] for d in creators_data if d['username'] == username][0]
    user_name_display = [d['name'] for d in creators_data if d['username'] == username][0]

    # --- SIDEBAR (MENU LATERAL) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/906/906343.png", width=50) # Ícone Genérico (Trocar pelo seu Logo)
        st.markdown(f"### Olá, **{user_name_display}**")
        st.caption(f"ID: {creator_id}")
        st.markdown("---")
        
        menu = st.radio(
            "NAVEGAÇÃO",
            ["📊 Dashboard", "👥 Comunidades", "📦 Ofertas", "💸 Financeiro", "⚙️ Configurações"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        authenticator.logout('Sair da Conta', 'sidebar')

    # ======================================================
    # TELA: DASHBOARD
    # ======================================================
    if menu == "📊 Dashboard":
        st.title("Visão Geral")
        st.markdown("Acompanhe o desempenho do seu negócio em tempo real.")
        
        # Filtros de data simulados (Visual)
        col_f1, col_f2 = st.columns([4, 1])
        with col_f2:
            st.selectbox("Período", ["Hoje", "Últimos 7 dias", "Este Mês"])
        
        st.divider()

        # Busca dados reais
        vendas = get_creator_data("vendas", creator_id)
        
        # Processamento de Métricas
        total_vendas = 0.00
        qtd_vendas = 0
        ticket_medio = 0.00
        
        if vendas:
            df = pd.DataFrame(vendas)
            total_vendas = df['valor_total'].sum()
            qtd_vendas = len(df)
            if qtd_vendas > 0:
                ticket_medio = total_vendas / qtd_vendas

        # CARTÕES DE MÉTRICAS (Agora estilizados pelo CSS lá em cima)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faturamento Total", f"R$ {total_vendas:.2f}", "+12%")
        c2.metric("Vendas Aprovadas", qtd_vendas)
        c3.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        c4.metric("Leads Ativos", "154", "Novo") # Simulado por enquanto

        st.markdown("### 📈 Performance de Vendas")
        # Gráfico Simulado (Placeholder bonito) se não tiver dados
        if vendas:
            st.bar_chart(df, x='created_at', y='valor_total', color="#7F00FF") # Roxo
        else:
            chart_data = pd.DataFrame({'Vendas': [0, 0, 0]}, index=["Ontem", "Hoje", "Amanhã"])
            st.line_chart(chart_data)
            st.info("Faça sua primeira venda para ver o gráfico subir! 🚀")

    # ======================================================
    # TELA: COMUNIDADES
    # ======================================================
    elif menu == "👥 Comunidades":
        st.title("Gestão de Comunidades")
        
        with st.container(): # Agrupa num "Card" visual
            col_add, col_btn = st.columns([3, 1])
            with col_add:
                st.markdown("### Seus Grupos VIP")
                st.caption("Adicione os canais onde o bot deve entregar o conteúdo.")
            with col_btn:
                # Expander que parece um modal
                with st.expander("➕ Nova Comunidade"):
                    with st.form("add_group"):
                        nome = st.text_input("Nome do Grupo")
                        chat_id = st.text_input("ID do Telegram")
                        if st.form_submit_button("Salvar"):
                            supabase.table("comunidades").insert({"creator_id": creator_id, "nome": nome, "telegram_chat_id": chat_id}).execute()
                            st.success("Salvo!")
                            st.rerun()

        grupos = get_creator_data("comunidades", creator_id)
        if grupos:
            st.dataframe(
                pd.DataFrame(grupos)[['nome', 'telegram_chat_id', 'created_at']], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Nenhum grupo cadastrado.")

    # ======================================================
    # TELA: OFERTAS
    # ======================================================
    elif menu == "📦 Ofertas":
        st.title("Catálogo de Produtos")
        
        tabs = st.tabs(["📦 Produtos Ativos", "➕ Criar Novo"])
        
        with tabs[0]:
            prods = get_creator_data("produtos", creator_id)
            if prods:
                for p in prods:
                    # Cria um "Card" para cada produto usando colunas
                    with st.container():
                        c_img, c_info, c_action = st.columns([1, 4, 1])
                        c_img.write("📦") # Placeholder para ícone
                        c_info.markdown(f"**{p['nome']}**")
                        c_info.caption(f"R$ {p['preco']:.2f} | Tipo: {p.get('tipo', 'N/A')}")
                        if c_action.button("🗑️", key=f"del_{p['id']}"):
                            supabase.table("produtos").delete().eq("id", p['id']).execute()
                            st.rerun()
                        st.divider()
            else:
                st.info("Nenhum produto à venda.")

        with tabs[1]:
            with st.form("new_offer"):
                nome = st.text_input("Nome da Oferta")
                preco = st.number_input("Preço (R$)", min_value=1.00, step=0.50)
                tipo = st.selectbox("Tipo", ["Assinatura", "Pack Único"])
                link = st.text_input("Link de Convite (Telegram)")
                if st.form_submit_button("Criar Oferta"):
                    supabase.table("produtos").insert({
                        "creator_id": creator_id,
                        "nome": nome, "preco": preco, "tipo": tipo, "link_entrega": link
                    }).execute()
                    st.success("Criado com sucesso!")
                    st.rerun()

    # ======================================================
    # TELA: FINANCEIRO
    # ======================================================
    elif menu == "💸 Financeiro":
        st.title("Carteira Digital")
        
        # Simulação de saldo (No futuro vem do Asaas)
        col_money, col_actions = st.columns([2, 1])
        with col_money:
            st.metric("Saldo Disponível", "R$ 0,00", delta_color="normal")
            st.caption("Valores disponíveis para saque imediato.")
        
        with col_actions:
            if st.button("🏦 Solicitar Saque", type="primary"):
                st.toast("Módulo de saque em manutenção no MVP.")

        st.markdown("### Dados Bancários")
        contas = get_creator_data("contas_bancarias", creator_id)
        if contas:
            c = contas[0]
            st.success(f"Conta Ativa: {c['banco_nome']} • Ag {c['agencia']} • CC {c['conta']}")
        else:
            with st.expander("Cadastrar Conta Bancária", expanded=True):
                with st.form("bank_add"):
                    banco = st.text_input("Banco")
                    agencia = st.text_input("Agência")
                    conta = st.text_input("Conta")
                    pix = st.text_input("Chave PIX")
                    if st.form_submit_button("Salvar"):
                        supabase.table("contas_bancarias").insert({
                            "creator_id": creator_id, "banco_nome": banco, "agencia": agencia, "conta": conta, "pix_chave": pix
                        }).execute()
                        st.rerun()

    # ======================================================
    # TELA: CONFIGURAÇÕES
    # ======================================================
    elif menu == "⚙️ Configurações":
        st.title("Configurações do Bot")
        
        configs = get_creator_data("config_bots", creator_id)
        
        with st.form("config_bot"):
            st.subheader("Conexão Telegram & Asaas")
            t_token = st.text_input("Token do Bot (@BotFather)", value=configs[0]['telegram_token'] if configs else "", type="password")
            a_key = st.text_input("Chave Asaas ($aact...)", value=configs[0]['asaas_key'] if configs else "", type="password")
            
            if st.form_submit_button("Atualizar Conexão"):
                dados = {
                    "creator_id": creator_id,
                    "telegram_token": t_token,
                    "asaas_key": a_key
                }
                if configs:
                    supabase.table("config_bots").update(dados).eq("creator_id", creator_id).execute()
                else:
                    supabase.table("config_bots").insert(dados).execute()
                st.success("Configurações salvas!")

elif authentication_status == False:
    st.error('Login falhou. Verifique usuário e senha.')
