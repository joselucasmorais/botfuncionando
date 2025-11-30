import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================================================
# 🔐 SUAS CONFIGURAÇÕES
# ======================================================
TOKEN_TELEGRAM = "8412461693:AAF4QR2QgJXGgu7q-_x6c0UvY8PQVdj2OdI"
ASAAS_KEY = "$aact_prod_s000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OmUwMzM5MmIyLTE5OGYtNDJiOS05ZDA0LTFiZTgwNTMxYzZjNTo6JGFhY2hfOTA4MDQ4ZTktODYxMS00NTM4LTliNTQtZmZmM2NiZmRhODJj"
CPF_TESTE = "075.213.784.07"
# ======================================================

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
            return None, None, f"Erro CPF: {cli_data.get('errors')[0]['description']}"
        else:
            return None, None, "Erro ao criar cliente"

        # 2. Cria Cobrança
        payload_pix = {
            "customer": cliente_id, "billingType": "PIX", "value": valor,
            "dueDate": "2025-12-30", "description": "Produto VIP Bot"
        }
        res_pix = requests.post(f"{url}/payments", json=payload_pix, headers=headers)
        pix_data = res_pix.json()
        
        if 'id' not in pix_data:
            return None, None, f"Erro Pix: {pix_data.get('errors')[0]['description']}"
            
        pagamento_id = pix_data['id'] # Guardamos esse ID para checar depois!

        # 3. Pega QR Code
        res_qr = requests.get(f"{url}/payments/{pagamento_id}/pixQrCode", headers=headers)
        return res_qr.json(), pagamento_id, None

    except Exception as e:
        return None, None, str(e)

def checar_status_pagamento(pagamento_id):
    """Pergunta ao Asaas se o pix já foi pago"""
    url = f"https://www.asaas.com/api/v3/payments/{pagamento_id}"
    headers = {"access_token": ASAAS_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        dados = response.json()
        return dados.get('status') # Retorna 'PENDING', 'RECEIVED' ou 'CONFIRMED'
    except:
        return "ERRO"

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
        # O erro real está aqui se a coluna não existir
        st.error(f"Erro ao buscar criadores no banco: {e}") 
        return [], [], [], []

# ... (Linhas 90 a 120 ok) ...

# Tenta fazer login
name, authentication_status, username = authenticator.login('Acesso Restrito', 'main')

# 2. SE A AUTENTICAÇÃO FOR BEM SUCEDIDA: MOSTRA O DASHBOARD
if authentication_status:
    # FILTRO: Busca o ID do criador que acabou de logar
    # Note: Aqui o código usa 'username'
    matching_creator = [d for d in creators_data if d.get('username') == username]
    
    if matching_creator:
        creator_id = matching_creator[0].get('id')
    else:
        st.error("Erro ao identificar ID do usuário.")
        st.stop()
    
    # ... (Restante do código continua igual, mas agora deve encontrar o creator_id) ...
