import logging
import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from handlers.chat import handle_chat
from handlers.resumo import handle_resumo
from handlers.documento import handle_documento_menu, handle_documento_callback, handle_documento_input

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 ChatBot Jurídico", callback_data="menu_chat")],
        [InlineKeyboardButton("📄 Resumir Documento", callback_data="menu_resumo")],
        [InlineKeyboardButton("📝 Gerar Documento", callback_data="menu_documento")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚖️ *Harvey Specter — Assistente Jurídico*\n\n"
        "Olá! Sou seu assistente jurídico especializado em direito civil, criminal e trabalhista brasileiro.\n\n"
        "Como posso ajudá-lo hoje?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_chat":
        context.user_data["mode"] = "chat"
        await query.edit_message_text(
            "💬 *Modo ChatBot Jurídico ativado*\n\n"
            "Pode me fazer sua pergunta jurídica. Digite /menu para voltar ao menu principal.",
            parse_mode="Markdown"
        )
    elif query.data == "menu_resumo":
        context.user_data["mode"] = "resumo"
        await query.edit_message_text(
            "📄 *Resumo de Documento*\n\n"
            "Envie o documento (PDF ou Word) que deseja resumir. Digite /menu para voltar.",
            parse_mode="Markdown"
        )
    elif query.data == "menu_documento":
        await handle_documento_menu(update, context)
    else:
        await handle_documento_callback(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("💬 ChatBot Jurídico", callback_data="menu_chat")],
        [InlineKeyboardButton("📄 Resumir Documento", callback_data="menu_resumo")],
        [InlineKeyboardButton("📝 Gerar Documento", callback_data="menu_documento")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚖️ *Menu Principal*\n\nEscolha uma opção:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "chat")

    if mode == "resumo":
        await update.message.reply_text("📄 Por favor, envie um arquivo PDF ou Word para resumir.")
        return

    if mode and mode.startswith("doc_"):
        await handle_documento_input(update, context)
        return

    await handle_chat(update, context)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "")
    if mode == "resumo":
        await handle_resumo(update, context)
    else:
        await update.message.reply_text(
            "📄 Deseja resumir este documento? Use /menu e selecione *Resumir Documento* primeiro.",
            parse_mode="Markdown"
        )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot iniciado!")
    app.run_polling()


if __name__ == "__main__":
    main()
