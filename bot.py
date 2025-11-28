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
    user_id = query.from_user.id

    if query.data == 'comprar_vip':
        await query.edit_message_text("⏳ Criando PIX...")
        
        # Gera o Pix
        dados_qr, pag_id, erro = gerar_pix_asaas(user_id, query.from_user.first_name, 5.00)
        
        if erro:
            await query.edit_message_text(f"❌ Erro: {erro}")
        else:
            # Salva o ID do pagamento para checar depois
            pagamentos_pendentes[user_id] = pag_id
            
            copia_e_cola = dados_qr['payload']
            msg = "✅ **PIX GERADO!**\nCopie o código abaixo e pague no seu banco:"
            await query.message.reply_text(msg, parse_mode='Markdown')
            await query.message.reply_text(f"`{copia_e_cola}`", parse_mode='Markdown')
            
            # CRIA O BOTÃO DE CHECAR PAGAMENTO
            botao_checar = [[InlineKeyboardButton("✅ JÁ PAGUEI (LIBERAR ACESSO)", callback_data='checar_pagamento')]]
            await query.message.reply_text("Depois de pagar, clique abaixo:", reply_markup=InlineKeyboardMarkup(botao_checar))

    elif query.data == 'checar_pagamento':
        # Pega o ID do pagamento que salvamos
        pag_id = pagamentos_pendentes.get(user_id)
        
        if not pag_id:
            await query.message.reply_text("Não achei nenhum pagamento pendente pra você.")
            return

        status = checar_status_pagamento(pag_id)
        
        if status == 'RECEIVED' or status == 'CONFIRMED':
            await query.edit_message_text("🎉 **PAGAMENTO CONFIRMADO!**\n\nVocê agora é VIP! 💎\n(Aqui você entregaria o link do grupo ou o produto)")
        else:
            await query.message.reply_text(f"🔍 O Banco disse que ainda está: **{status}**.\nSe já pagou, espere 30 segundos e tente de novo!")

def main():
    print("🤖 BOT PRONTO COM VERIFICAÇÃO!")
    app = Application.builder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", inicio))
    app.add_handler(CallbackQueryHandler(botoes))
    app.run_polling()

if __name__ == "__main__":
    main()
