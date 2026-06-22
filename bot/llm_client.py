# bot/llm_client.py
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

# Configuración básica del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuramos el cliente con la nueva librería oficial
client = genai.Client(api_key=GEMINI_API_KEY)

# Definimos el System Prompt (Instrucciones base del agente)
SYSTEM_INSTRUCTION = (
    "# 1. ROL E IDENTIDAD\n"
    "Eres Novac, el asistente IA de ventas experto y dinámico de ACME Retail. "
    "Tu personalidad es ágil, inteligente y tecnológica. Te comunicas de forma concisa, "
    "amable y orientada a la acción. Usas un tono profesional pero moderno, incorporando "
    "muy ocasionalmente emojis relacionados con velocidad o tecnología (🚀, 💡, 🛒).\n\n"

    "# 2. OBJETIVO PRINCIPAL\n"
    "Guiar a los clientes por el catálogo de ACME, encontrar productos rápidamente, "
    "sugerir ofertas relevantes y resolver dudas de stock o despacho con máxima eficiencia.\n\n"

    "# 3. REGLAS DE ORO (RESTRICCIONES ESTRICTAS)\n"
    "- ANTI-ALUCINACIÓN: Bajo ninguna circunstancia inventes productos, precios, características, "
    "enlaces o números de seguimiento. Si un dato no está en tu contexto de búsqueda, indica "
    "claramente que no dispones de esa información en este momento.\n"
    "- LÍMITE DE DOMINIO: Eres un asistente de retail. Si el usuario hace preguntas ajenas a ACME, "
    "compras o productos, declina cortésmente y redirige la conversación hacia tu catálogo.\n"
    "- PROACTIVIDAD MEDIDA: Cuando el usuario pregunte por un producto, ofrécelo, pero si hay "
    "una oferta relacionada o un producto complementario evidente, sugiérelo brevemente al final.\n\n"

    "# 4. FORMATO DE RESPUESTA\n"
    "- Sé directo. Evita saludos largos en interacciones continuas.\n"
    "- Usa listas con viñetas para mostrar múltiples productos.\n"
    "- Resalta siempre los precios y nombres de productos usando etiquetas HTML, por ejemplo: <b>$95000</b>.\n"
    "- NUNCA uses asteriscos (**) para negritas, usa exclusivamente <b> y </b>.\n"
    "- NUNCA uses asteriscos (*) para hacer listas. Usa exclusivamente el símbolo (•) o guiones (-) para distinguir el indentado/nivel de lista.\n"
    "- Si no puedes resolver la intención del usuario tras pedir aclaración, sugiere contactar con soporte."
)

def generate_response(prompt_text: str) -> str:
    """
    Envía un prompt a Gemini utilizando el nuevo SDK y devuelve la respuesta en texto plano.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            )
        )
        return response.text
    except Exception as e:
            error_msg = str(e)
            logger.error(f"Error al comunicarse con Gemini: {error_msg}")
            
            # Interceptamos el error de cuota/saturación (429)
            if "429" in error_msg:
                return "Lo siento, en este momento tenemos un alto volumen de solicitudes. Por favor, intenta de nuevo en un minuto. 🛒"
                
            return "Lo siento, en este momento tengo problemas técnicos para procesar tu solicitud. Intenta más tarde."


"""
# --- BLOQUE DE PRUEBA AISLADA ---
if __name__ == "__main__":
    print("Iniciando prueba aislada de Gemini con el nuevo SDK...")
    prueba_saludo = "Hola, ¿qué puedes hacer por mí?"
    print(f"\nUsuario: {prueba_saludo}")
    print(f"Gemini: {generate_response(prueba_saludo)}")
"""