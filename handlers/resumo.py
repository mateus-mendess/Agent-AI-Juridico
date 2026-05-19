import os
import tempfile
import google.generativeai as genai
from telegram import Update
from telegram.ext import ContextTypes
import PyPDF2
import docx

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

RESUMO_PROMPT = """Você é Harvey Specter, um assistente jurídico especializado.
Analise o documento jurídico a seguir e forneça um resumo estruturado em português brasileiro contendo:

1. **Tipo de Documento**
2. **Partes Envolvidas**
3. **Objeto/Finalidade**
4. **Principais Obrigações e Direitos**
5. **Prazos Importantes** (se houver)
6. **Cláusulas de Destaque**
7. **Riscos Jurídicos Identificados**
8. **Recomendações**

Seja objetivo e use linguagem jurídica precisa."""


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

        # Extrai texto conforme tipo
        if file_name.endswith(".pdf"):
            text = extract_text_pdf(tmp_path)
        else:
            text = extract_text_docx(tmp_path)

        os.unlink(tmp_path)

        if not text.strip():
            await update.message.reply_text("⚠️ Não foi possível extrair texto do documento. Verifique se o arquivo não está protegido ou escaneado.")
            return

        # Limita o texto para não estourar tokens (aprox. 30k caracteres)
        if len(text) > 30000:
            text = text[:30000] + "\n\n[Documento truncado para análise]"

        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(f"{RESUMO_PROMPT}\n\n---\n\n{text}")

        await update.message.reply_text(
            f"📋 *Resumo Jurídico*\n\n{response.text}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Erro ao processar o documento. Tente novamente ou verifique o arquivo."
        )
