import os
import logging
import tempfile
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openrouter/auto"

TIPOS_DOCUMENTO = {
    "doc_procuracao": "Procuração",
    "doc_termo": "Termo de Declaração",
    "doc_contrato": "Contrato",
}

CAMPOS_DOCUMENTO = {
    "doc_procuracao": [
        ("outorgante_nome", "Nome completo do *Outorgante*:"),
        ("outorgante_cpf", "CPF do Outorgante:"),
        ("outorgante_qualificacao", "Qualificação do Outorgante (ex: brasileiro, policial militar, solteiro):"),
        ("outorgante_endereco", "Endereço completo do Outorgante:"),
        ("outorgado_nome", "Nome completo do *Outorgado* (advogado):"),
        ("outorgado_oab", "Número da OAB (ex: OAB/AL nº 15.787):"),
        ("outorgado_endereco", "Endereço profissional do Outorgado:"),
        ("tipo", "Tipo da procuração (*cível* ou *criminal*):"),
        ("numero_processo", "Número do processo (apenas se criminal, senão digite *não se aplica*):"),
        ("cidade", "Cidade e Estado:"),
    ],
    "doc_termo": [
        ("declarante_nome", "Nome completo do *Declarante*:"),
        ("declarante_cpf", "CPF do Declarante:"),
        ("declarante_endereco", "Endereço completo do Declarante:"),
        ("objeto_declaracao", "O que está sendo declarado:"),
        ("finalidade", "Finalidade da declaração (para qual fim será usada):"),
        ("cidade", "Cidade e Estado:"),
    ],
    "doc_contrato": [
        ("contratante_nome", "Nome completo ou razão social do *Contratante*:"),
        ("contratante_cpf", "CPF/CNPJ do Contratante:"),
        ("contratante_endereco", "Endereço do Contratante:"),
        ("contratado_nome", "Nome completo ou razão social do *Contratado*:"),
        ("contratado_cpf", "CPF/CNPJ do Contratado:"),
        ("contratado_endereco", "Endereço do Contratado:"),
        ("objeto", "Objeto do contrato (o que está sendo contratado):"),
        ("valor", "Valor e forma de pagamento:"),
        ("prazo", "Prazo de vigência do contrato:"),
        ("cidade", "Cidade e Estado:"),
    ],
}

PROMPTS_DOCUMENTO = {
    "doc_procuracao": """Gere uma Procuração formal em português brasileiro seguindo EXATAMENTE esta estrutura, sem adicionar nada além do que está aqui:

OUTORGANTE(s): {outorgante_nome}, {outorgante_qualificacao}, inscrito no CPF nº {outorgante_cpf}, residente e domiciliado em {outorgante_endereco}.

OUTORGADO(S): {outorgado_nome}, advogado(a), inscrito(a) na {outorgado_oab}, com endereço profissional sito à {outorgado_endereco}.

PODERES: Se o tipo for "cível", use exatamente: "Os da Cláusula AD JUDICIA e os especiais para: desistir, transigir, firmar compromissos, assinar documentos, podendo receber notificações, citações e intimações, carta precatória na forma da lei, levantamento de alvará judicial, e poderes especiais para representar o outorgante perante qualquer órgão da administração pública ou privada, praticar todos os demais atos necessários ao fiel desempenho do presente mandato, inclusive substabelecer, com ou sem reservas de poderes."
Se o tipo for "criminal", use o mesmo texto acima e adicione ao final: "nos autos do processo nº {numero_processo}."

{cidade}, _____ de ________________ de 20____.

__________________________________________________
{outorgante_nome}

NÃO adicione nenhum outro campo, assinatura ou texto além do que está neste modelo.""",

    "doc_termo": """Gere um Termo de Declaração formal completo em português brasileiro com base nos dados abaixo.
O documento deve seguir as normas jurídicas brasileiras, incluindo qualificação do declarante,
declaração clara e objetiva, e espaço para assinatura e testemunhas.

Dados:
Declarante: {declarante_nome}, CPF {declarante_cpf}, residente em {declarante_endereco}
Declaração: {objeto_declaracao}
Finalidade: {finalidade}
Local: {cidade}

Gere apenas o texto do documento, sem explicações adicionais.""",

    "doc_contrato": """Gere um Contrato formal completo em português brasileiro com base nos dados abaixo.
O documento deve seguir as normas jurídicas brasileiras, com cláusulas bem definidas sobre
objeto, obrigações das partes, valor, prazo, rescisão e foro competente.

Dados:
Contratante: {contratante_nome}, CPF/CNPJ {contratante_cpf}, endereço {contratante_endereco}
Contratado: {contratado_nome}, CPF/CNPJ {contratado_cpf}, endereço {contratado_endereco}
Objeto: {objeto}
Valor e Pagamento: {valor}
Prazo: {prazo}
Local: {cidade}

Gere apenas o texto do documento, sem explicações adicionais.""",
}


def criar_docx(tipo: str, conteudo: str, dados: dict) -> str:
    doc = Document()

    section = doc.sections[0]
    section.left_margin = Inches(1.2)
    section.right_margin = Inches(1.2)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)

    # Título
    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run(TIPOS_DOCUMENTO[tipo].upper())
    run.bold = True
    run.font.size = Pt(14)

    doc.add_paragraph()

    # Conteúdo gerado pela IA
    for linha in conteudo.split("\n"):
        if linha.strip():
            p = doc.add_paragraph(linha)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for run in p.runs:
                run.font.size = Pt(12)
        else:
            doc.add_paragraph()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)
    return tmp.name


async def handle_documento_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📜 Procuração", callback_data="doc_procuracao")],
        [InlineKeyboardButton("📋 Termo de Declaração", callback_data="doc_termo")],
        [InlineKeyboardButton("📃 Contrato", callback_data="doc_contrato")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_voltar")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "📝 *Geração de Documentos*\n\nQual documento deseja gerar?",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📝 *Geração de Documentos*\n\nQual documento deseja gerar?",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


async def handle_documento_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    doc_tipo = query.data

    if doc_tipo == "menu_voltar":
        keyboard = [
            [InlineKeyboardButton("💬 ChatBot Jurídico", callback_data="menu_chat")],
            [InlineKeyboardButton("📄 Resumir Documento", callback_data="menu_resumo")],
            [InlineKeyboardButton("📝 Gerar Documento", callback_data="menu_documento")],
        ]
        await query.edit_message_text(
            "⚖️ *Menu Principal*\n\nEscolha uma opção:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if doc_tipo not in CAMPOS_DOCUMENTO:
        return

    context.user_data["mode"] = doc_tipo
    context.user_data["doc_campos"] = CAMPOS_DOCUMENTO[doc_tipo].copy()
    context.user_data["doc_dados"] = {}
    context.user_data["doc_tipo"] = doc_tipo

    campo_key, campo_label = context.user_data["doc_campos"][0]
    context.user_data["doc_campo_atual"] = 0

    await query.edit_message_text(
        f"📝 *{TIPOS_DOCUMENTO[doc_tipo]}*\n\n"
        f"Vou precisar de algumas informações. Você pode digitar /menu a qualquer momento para cancelar.\n\n"
        f"1/{len(context.user_data['doc_campos'])} — {campo_label}",
        parse_mode="Markdown"
    )


async def handle_documento_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc_tipo = context.user_data.get("doc_tipo")
    campos = context.user_data.get("doc_campos", [])
    dados = context.user_data.get("doc_dados", {})
    idx = context.user_data.get("doc_campo_atual", 0)

    if idx >= len(campos):
        return

    campo_key, _ = campos[idx]
    dados[campo_key] = update.message.text
    context.user_data["doc_dados"] = dados

    idx += 1
    context.user_data["doc_campo_atual"] = idx

    if idx < len(campos):
        _, proximo_label = campos[idx]
        await update.message.reply_text(
            f"{idx + 1}/{len(campos)} — {proximo_label}",
            parse_mode="Markdown"
        )
    else:
        # Todos os campos coletados — gera o documento
        await update.message.reply_text("⏳ Gerando documento, aguarde...")
        await update.message.reply_chat_action("typing")

        try:
            prompt = PROMPTS_DOCUMENTO[doc_tipo].format(**dados)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            conteudo = response.choices[0].message.content
            usage = response.usage
            logger.info(
                f"[TOKENS/DOC] input={usage.prompt_tokens} | "
                f"output={usage.completion_tokens} | "
                f"total={usage.total_tokens}"
            )

            docx_path = criar_docx(doc_tipo, conteudo, dados)

            nome_arquivo = f"{TIPOS_DOCUMENTO[doc_tipo].replace(' ', '_')}.docx"
            with open(docx_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=nome_arquivo,
                    caption=f"✅ *{TIPOS_DOCUMENTO[doc_tipo]}* gerado com sucesso!\n\n"
                            "⚠️ Revise o documento antes de assinar. Este é um modelo gerado por IA.",
                    parse_mode="Markdown"
                )

            os.unlink(docx_path)

        except Exception as e:
            await update.message.reply_text(
                "⚠️ Erro ao gerar o documento. Tente novamente."
            )

        finally:
            context.user_data.clear()
