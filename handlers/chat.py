import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ContextTypes

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """Você é Harvey Specter, um assistente jurídico especializado e altamente competente.
Você auxilia advogados e escritórios de advocacia com questões de direito civil, criminal e trabalhista brasileiro.

Suas características:
- Direto, objetivo e confiante nas respostas
- Utiliza linguagem jurídica precisa, mas acessível
- Cita artigos de lei e jurisprudência quando relevante
- Sempre alerta quando uma questão exige análise presencial de um advogado
- Organiza respostas de forma clara: análise, fundamento legal e recomendação

Limitações importantes:
- Você APENAS responde sobre direito civil, criminal e trabalhista brasileiro
- Se perguntado sobre outros temas, recuse educadamente e redirecione para sua área de atuação
- Nunca substitua a consulta com um advogado humano para casos concretos
- Não forneça pareceres definitivos, apenas orientações preliminares

Responda SEMPRE em português brasileiro."""


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Inicializa histórico se não existir
    if "history" not in context.user_data:
        context.user_data["history"] = []

    await update.message.reply_chat_action("typing")

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )

        # Monta histórico no formato do Gemini
        history = context.user_data["history"]
        chat = model.start_chat(history=history)
        response = chat.send_message(user_message)
        reply = response.text

        # Salva no histórico
        context.user_data["history"].append({"role": "user", "parts": [user_message]})
        context.user_data["history"].append({"role": "model", "parts": [reply]})

        # Limita histórico a 20 mensagens para não estourar tokens
        if len(context.user_data["history"]) > 20:
            context.user_data["history"] = context.user_data["history"][-20:]

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Ocorreu um erro ao processar sua mensagem. Tente novamente em instantes."
        )
