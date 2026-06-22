import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode


from bot.memory import (
    get_or_create_session, add_message_to_history, 
    update_last_viewed_products, set_transient_context, clear_transient_context
)
from core.search_engine import classify_intent, mock_search_products, mock_search_policies
from bot.prompt_builder import build_final_prompt
from bot.llm_client import generate_response


# Importamos el token desde nuestro archivo de configuración
from config import TELEGRAM_TOKEN

# Configuración básica de logging para ver la actividad y errores en consola
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando inicial /start."""
    welcome_message = (
        "¡Hola! Soy Novac, tu asistente personal de compras inteligente. "
        "Estoy aquí para ayudarte a navegar por nuestro universo de productos.\n\n"
        "Conmigo podrás:\n"
        "🔍 Consultar nuestro catálogo digital rápidamente.\n"
        "👀 Recibir recomendaciones personalizadas.\n"
        "✅ Resolver tus dudas sobre nuestros servicios\n\n"
        "¡Encantado de conocernos!"

    )
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flujo direccional estricto para cada mensaje entrante."""
    user_message = update.message.text
    chat_id = str(update.message.chat_id)

    # 1. Recuperamos el estado de memoria del usuario
    session = get_or_create_session(chat_id)

    # 2. Enrutador Lógico
    intent = classify_intent(user_message)
    logging.info(f"Intención detectada para {chat_id}: {intent}")
    
    # 3. Recuperación Dirigida (RAG)
    if intent == "catalogo":
        productos_recuperados = mock_search_products(user_message)
        if productos_recuperados:
            # Solo sobrescribimos si encontramos algo nuevo, garantizando continuidad
            update_last_viewed_products(chat_id, productos_recuperados)
            
    elif intent == "politicas":
        politica_texto = mock_search_policies(user_message)
        if politica_texto:
            set_transient_context(chat_id, politica_texto)

    # Obtenemos la sesión actualizada después de la búsqueda
    session = get_or_create_session(chat_id)

    # 4. Ensamblaje del Prompt Estructurado
    prompt_maestro = build_final_prompt(
        user_message=user_message,
        chat_history=session["chat_history"],
        products_list=session["last_viewed_products"],
        transient_context=session["transient_context"]
    )

    # 5. Generación con el LLM
    logging.info(f"Consultando a Gemini para {chat_id}...")
    respuesta_llm = generate_response(prompt_maestro)

    # 6. Mantenimiento del Estado (La Regla de Oro)
    add_message_to_history(chat_id, "Cliente", user_message)
    add_message_to_history(chat_id, "Novac", respuesta_llm)
    clear_transient_context(chat_id) # Limpiamos inmediatamente la política inyectada

    # 7. Respuesta Final
    await update.message.reply_text(respuesta_llm, parse_mode=ParseMode.HTML)

def main():
    """Inicializa la aplicación y mantiene el bot en escucha."""
    # Construye la aplicación de Telegram con el Token
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Añade los handlers para responder a comandos y texto plano
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Inicia el ciclo de escucha de mensajes (long polling)
    logging.info("Iniciando el bot de Telegram...")
    application.run_polling()

if __name__ == '__main__':
    main()