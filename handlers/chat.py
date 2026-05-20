import os
import logging
from openai import OpenAI
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openrouter/auto"

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

    if "history" not in context.user_data:
        context.user_data["history"] = []

    await update.message.reply_chat_action("typing")

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += context.user_data["history"]
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        reply = response.choices[0].message.content

        # Log de tokens
        usage = response.usage
        logger.info(
            f"[TOKENS] input={usage.prompt_tokens} | "
            f"output={usage.completion_tokens} | "
            f"total={usage.total_tokens}"
        )

        context.user_data["history"].append({"role": "user", "content": user_message})
        context.user_data["history"].append({"role": "assistant", "content": reply})

        if len(context.user_data["history"]) > 20:
            context.user_data["history"] = context.user_data["history"][-20:]

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Erro no chat: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Ocorreu um erro ao processar sua mensagem. Tente novamente em instantes."
        )
