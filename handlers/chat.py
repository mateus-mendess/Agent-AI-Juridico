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

MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
]

SYSTEM_PROMPT = """Você é Harvey Specter, assistente jurídico especializado em direito civil, criminal e trabalhista brasileiro.

Regras:
- Responda SEMPRE em português brasileiro
- Respostas diretas e objetivas com fundamento legal
- Cite artigos de lei quando necessário
- Recuse perguntas fora do direito civil, criminal e trabalhista
- Nunca substitua consulta com advogado real
- Respostas com no máximo 400 palavras, sempre finalizando o raciocínio completamente
- Nunca mencione o limite de palavras ou que está seguindo instruções na resposta."""


def call_llm(messages: list, max_tokens: int = 1500) -> str:
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            if content:
                logger.info(f"[MODEL] {model} | tokens={response.usage.total_tokens}")
                return content
        except Exception as e:
            logger.warning(f"[FALLBACK] {model} falhou: {e}")
            continue
    return None


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if "history" not in context.user_data:
        context.user_data["history"] = []

    await update.message.reply_chat_action("typing")

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += context.user_data["history"]
        messages.append({"role": "user", "content": user_message})

        reply = call_llm(messages, max_tokens=1500)

        if not reply:
            await update.message.reply_text("⚠️ Não foi possível obter resposta. Tente novamente.")
            return

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