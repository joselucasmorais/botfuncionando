import logging
import time
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================================================
# 🔐 SUAS CONFIGURAÇÕES
# ======================================================
TOKEN_TELEGRAM = "8412461693:AAF4QR2QgJXGgu7q-_x6c0UvY8PQVdj2OdI"
ASAAS_KEY = "$aact_prod_s000MzkwODA2MWY2OGM3MDU2NWM3MzJlNzZmNGZhZGY6OmUwMzM5MmIyLTE5OGYtNDJiOS05ZDA0LTFiZTgwNTMxYzZjNTo6JGFhY2hfOTA4MDQ4ZTktODYxMS00NTM4LTliNTQtZmZmM2NiZmRhODJj"
CPF_TESTE = "075.213.784.07"
# ======================================================
# Logging
logging.basicConfig(level=logging.INFO)

# Variável simples para guardar o ID do pagamento temporariamente
pagamentos_pendentes = {}

def gerar_pix_asaas(user_id, nome_usuario, valor):
    url = "https://www.asaas.com/api/v3"
    headers = {"access_token": ASAAS_KEY, "Content-Type": "application/json"}

    try:
        # 1. Cria/Busca Cliente
        payload_cliente = {
            "name": f"{nome_usuario} (Telegram)",
            "cpfCnpj": CPF_TESTE,
            "externalReference": str(user_id)
        }
        res_cli = requests.post(f"{url}/customers", json=payload_cliente, headers=headers)
        cli_data = res_cli.json()
        
        if 'id' in cli_data:
            cliente_id = cli_data['id']
        elif cli_data.get('code') == 'invalid_customer':
            return None, None, "Erro CPF: {cli_data.get('errors')[0]['description']}"
        else:
            return None, None, "Erro ao criar cliente"

        # 2. Cria Cobrança
        payload_pix = {
            "customer": cliente_id, "billingType": "PIX", "value": valor,
            "dueDate": "2025-12-30", "description": "Produto VIP Bot"
        }
        res_pix = requests.post(f"{url}/payments", json=payload_pix, headers=headers)
        return res_pix, pagamento_id, None

    except Exception as e:
        return None, None, str(e)

def checar_status_pagamento(pagamento_id):
    try:
        # CORREÇÃO AQUI: Buscamos as colunas que devem existir no seu banco.
        resp = supabase.table("creators").select("id, username, name, password_hash").execute() 
        data = getattr(resp, "data", [])
        
        if not data: return [], [], []
            
        # Utilizamos d.get() para evitar NameError
        usernames = [d.get('username') for d in data]
        names = [d.get('name') for d in data]
        hashed_passwords = [d.get('password_hash') for d in data]
        return usernames, names, hashed_passwords, data
    except Exception as e:
        return [], [], [], []

async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    teclado = [[InlineKeyboardButton("💎 Comprar VIP (R$ 5,00)", callback_data='comprar_vip')]]
    await update.message.reply_text(f"Olá {user.first_name}! Bora vender?", reply_markup=InlineKeyboardMarkup(teclado))

async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ... (Linhas anteriores ok) ...

@st.cache_data(ttl=60)
def get_all_creators():
    """Busca usuários para login (Corrigido para usar username)"""
    try:
        # CORREÇÃO AQUI: Buscamos as colunas que devem existir no seu banco.
        resp = supabase.table("creators").select("id, username, name, password_hash").execute() 
        data = getattr(resp, "data", [])
        
        if not data: return [], [], [], []
            
        # Utilizamos d.get() para evitar NameError
        usernames = [d.get('username') for d in data]
        names = [d.get('name') for d in data]
        hashed_passwords = [d.get('password_hash') for d in data]
        return usernames, names, hashed_passwords, data
    except Exception as e:
        return [], [], [], []

# Corrigido: Adicionado a animação.
#  Simulando um erro ao fazer login.
if authentication_status:
    # 2. SE A AUTENTICAÇÃO FOR BEM SUCEDIDA: MOSTRA O DASHBOARD
    #  ... (Código anterior para mostrar o dashboard) ...

    st.stop()
