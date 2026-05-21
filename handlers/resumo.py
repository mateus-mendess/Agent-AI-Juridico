import os
import logging
import tempfile
from openai import OpenAI
from telegram import Update
from telegram.ext import ContextTypes
import PyPDF2
import docx

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

RESUMO_PROMPT = """Você é Harvey Specter, um assistente jurídico especializado.
Faça um resumo FIEL e CONCISO do documento jurídico abaixo em português brasileiro.

Regras:
- Resuma APENAS o que está no documento, sem adicionar informações externas
- Máximo de 400 palavras
- Destaque: objetivo do documento, partes envolvidas, poderes/objeto e observações relevantes
- Não invente cláusulas, prazos ou riscos que não estejam no documento
- Sempre finalize o raciocínio completamente, nunca corte no meio de uma frase
- Nunca mencione o limite de palavras na resposta"""


def extract_text_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def extract_text_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

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


async def handle_resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name.lower()

    if not (file_name.endswith(".pdf") or file_name.endswith(".docx") or file_name.endswith(".doc")):
        await update.message.reply_text(
            "⚠️ Formato não suportado. Envie um arquivo *PDF* ou *Word (.docx)*.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("📄 Processando documento, aguarde...")
    await update.message.reply_chat_action("typing")

    try:
        file = await context.bot.get_file(document.file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        if file_name.endswith(".pdf"):
            text = extract_text_pdf(tmp_path)
        else:
            text = extract_text_docx(tmp_path)

        os.unlink(tmp_path)

        if not text.strip():
            await update.message.reply_text("⚠️ Não foi possível extrair texto do documento.")
            return

        if len(text) > 30000:
            text = text[:30000] + "\n\n[Documento truncado para análise]"

        reply = call_llm([
            {"role": "system", "content": RESUMO_PROMPT},
            {"role": "user", "content": text}
        ], max_tokens=1500)

        await update.message.reply_text(f"📋 Resumo Jurídico\n\n{reply}")

    except Exception as e:
        logger.error(f"Erro no resumo: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Erro ao processar o documento. Tente novamente.")
