import logging
import time
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode


from bot.memory import (
    get_or_create_session, add_message_to_history,
    update_last_viewed_products, set_transient_context, clear_transient_context
)
from core.search_engine import classify_intent
from bot.prompt_builder import build_final_prompt
from bot.llm_client import generate_response


# Importamos el token desde nuestro archivo de configuración
from config import TELEGRAM_TOKEN

def get_user_logger(chat_id: int):
    # Aseguramos que la carpeta de logs exista
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    logger_name = f"user_{chat_id}"
    user_logger = logging.getLogger(logger_name)
    
    # Evitamos añadir múltiples handlers si el logger ya existe
    if not user_logger.handlers:
        user_logger.setLevel(logging.INFO)
        # Cada usuario tendrá su archivo en la carpeta /logs/
        file_handler = logging.FileHandler(f"logs/chat_{chat_id}.log", encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        user_logger.addHandler(file_handler)
        
    return user_logger

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando inicial /start."""

    chat_id = update.message.chat_id
    user_logger = get_user_logger(chat_id)
    user_logger.info(f"[ChatID: {chat_id}] ------------------------------------------")
    user_logger.info(f"[ChatID: {chat_id}] Usuario inició el bot.")

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

    user_logger = get_user_logger(chat_id)

    # === 0. INICIO END-TO-END ===
    start_time_total = time.perf_counter()
    user_logger.info(f"[ChatID: {chat_id}] ------------------------------------------")
    user_logger.info(f"[ChatID: {chat_id}] 1. Recepción: '{user_message}'")


    # 1. Recuperamos el estado de memoria del usuario
    session = get_or_create_session(chat_id)

    # 2. Enrutador + Recuperación Dirigida (RAG) — ahora unificados en classify_intent
    start_time_rag = time.perf_counter()

    contexto_recuperado, productos_recuperados = classify_intent(user_message)
    if contexto_recuperado:
        set_transient_context(chat_id, contexto_recuperado)
    if productos_recuperados:
        # Solo sobrescribimos si encontramos algo nuevo, garantizando continuidad
        update_last_viewed_products(chat_id, productos_recuperados)

    # Obtenemos la sesión actualizada después de la búsqueda
    session = get_or_create_session(chat_id)

    # Medición latencia RAG
    end_time_rag = time.perf_counter()
    latencia_rag = (end_time_rag - start_time_rag) * 1000
    user_logger.info(f"[ChatID: {chat_id}] 2. Latencia RAG: {latencia_rag:.2f} ms")

    # 4. Ensamblaje del Prompt Estructurado
    prompt_maestro = build_final_prompt(
        user_message=user_message,
        chat_history=session["chat_history"],
        #products_list=session["last_viewed_products"],
        transient_context=session["transient_context"]
    )

    # 5. Generación con el LLM
    user_logger.info(f"[ChatID: {chat_id}] 3. Generando respuesta con Gemini...")
    start_time_llm = time.perf_counter()
    respuesta_llm = await generate_response(prompt_maestro)
    user_logger.info(f"[ChatID: {chat_id}] Respuesta Novac: {respuesta_llm}")
    end_time_llm = time.perf_counter()
    latencia_llm = (end_time_llm - start_time_llm) * 1000
    user_logger.info(f"[ChatID: {chat_id}] 4. Latencia Inferencia LLM: {latencia_llm:.2f} ms")


    # 6. Mantenimiento del Estado (La Regla de Oro)
    add_message_to_history(chat_id, "Cliente", user_message)
    add_message_to_history(chat_id, "Novac", respuesta_llm)
    clear_transient_context(chat_id) # Limpiamos inmediatamente la política inyectada

    # 7. Respuesta Final
    await update.message.reply_text(respuesta_llm, parse_mode=ParseMode.HTML)

    # 8. Cálculo final de latencia
    end_time_total = time.perf_counter()
    latencia_total = (end_time_total - start_time_total) * 1000
    user_logger.info(f"[ChatID: {chat_id}] 5. Latencia TOTAL End-to-End: {latencia_total:.2f} ms")
    user_logger.info(f"[ChatID: {chat_id}] ------------------------------------------")

def main():
    """Inicializa la aplicación y mantiene el bot en escucha."""
    # Construye la aplicación de Telegram con el Token
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Añade los handlers para responder a comandos y texto plano
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Inicia el ciclo de escucha de mensajes (long polling)
    application.run_polling()

if __name__ == '__main__':
    main()