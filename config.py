import os
from dotenv import load_dotenv

# Carga las variables desde un archivo .env en la raíz del proyecto
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("Falta el TELEGRAM_TOKEN en las variables de entorno. Revisa tu archivo .env")