# main.py
import logging

# Importamos la función main() de tu módulo de Telegram
# Le ponemos un alias (run_bot) para que sea más claro
from bot.telegram_app import main as run_bot

# Importamos la función para interactuar con Gemini
from bot.llm_client import generate_response

# Configuración global de logging para todo el proyecto
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """
    Punto de entrada principal del sistema.
    En el futuro, aquí inicializaremos los modelos de embeddings
    y conectaremos el núcleo de búsqueda antes de levantar el bot.
    """
    logging.info("Iniciando el Agente Virtual de Retail (Modo Pruebas)...")
    
    # --- BLOQUE DE PRUEBA DE GEMINI ---
    logging.info("Verificando conexión con la API de Gemini...")
    try:
        test_prompt = "Responde con un 'Hola, estoy en línea' si me escuchas."
        test_response = generate_response(test_prompt)
        
        # NUEVO: Verificamos que la respuesta no sea nuestro mensaje de error del bloque except
        if "Lo siento, en este momento tengo problemas" in test_response:
            raise ValueError("La API devolvió el mensaje de error de contingencia.")
            
        logging.info(f"Gemini respondió correctamente: {test_response}")
    except Exception as e:
        logging.error(f"Fallo crítico: No se pudo conectar con Gemini. Detalle: {e}")
        return 
    # -----------------------------------

    # Levantamos el bot de Telegram solo si Gemini respondió con éxito
    try:
        logging.info("Iniciando conexión con Telegram...")
        run_bot()
    except KeyboardInterrupt:
        logging.info("Bot detenido manualmente por el usuario.")
    except Exception as e:
        logging.error(f"Error crítico al ejecutar el bot: {e}")

if __name__ == '__main__':
    main()