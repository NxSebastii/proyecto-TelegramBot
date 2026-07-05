# bot/prompt_builder.py
from core.search_engine import format_retrieved_products

def build_final_prompt(user_message: str, chat_history: list, productos_recientes: list, politicas_recientes: list, transient_context: str) -> str:
    """Ensambla el historial, productos/políticas recientes, el contexto recuperado y el mensaje en un Prompt Maestro."""

    # 1. Formateamos el historial
    history_text = "HISTORIAL RECIENTE:\n"
    if not chat_history:
        history_text += "(No hay historial previo)\n"
    else:
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"

    # 2. Productos vistos en turnos anteriores (persiste aunque la búsqueda
    # de este turno no encuentre nada nuevo), para resolver referencias
    # como "el más barato" o "el segundo".
    productos_text = ""
    if productos_recientes:
        productos_text = (
            "PRODUCTOS MOSTRADOS RECIENTEMENTE AL CLIENTE (usa esta lista si el cliente "
            "se refiere a 'el más barato', 'el primero', 'el segundo', 'ese', etc. sin "
            "nombrar el producto de nuevo):\n"
            f"{format_retrieved_products(productos_recientes)}\n"
        )

    # 3. Políticas consultadas en turnos anteriores (mismo motivo: para
    # responder preguntas de seguimiento como "¿cuáles son esas condiciones?"
    # sin depender de que la búsqueda semántica la vuelva a encontrar).
    politicas_text = ""
    if politicas_recientes:
        texto_politicas = "".join(f"- {p['tema']}: {p['contenido']}\n" for p in politicas_recientes)
        politicas_text = (
            "POLÍTICAS CONSULTADAS RECIENTEMENTE (usa esto si el cliente sigue preguntando "
            "sobre la misma política sin mencionar palabras clave nuevas):\n"
            f"{texto_politicas}\n"
        )

    # 4. Añadimos contexto temporal (búsqueda de este turno) si existe
    transient_text = ""
    if transient_context:
        transient_text = f"INFORMACIÓN OPERATIVA RELEVANTE (búsqueda de este turno):\n{transient_context}\n"

    # 5. Instrucciones: numeradas y breves (mejor seguimiento en modelos flash/free tier)
    instrucciones = (
        "INSTRUCCIONES:\n"
        "1. Usa SOLO la información de arriba. No inventes productos, precios, políticas "
        "ni detalles que no estén en el texto.\n"
        "2. Si arriba se indica que NINGÚN producto cumple lo pedido, dilo directamente como "
        "un hecho confirmado (ej. \"no tenemos ese producto en esa talla/color\"). "
        "NUNCA lo presentes como si te faltara información.\n"
        "3. Si el cliente se refiere a un producto anterior (\"el más barato\", \"el "
        "primero\", \"ese\", \"el segundo\") y la INFORMACIÓN OPERATIVA de este turno no "
        "trae productos nuevos, resuélvelo usando PRODUCTOS MOSTRADOS RECIENTEMENTE.\n"
        "4. Menciona los productos por su NOMBRE, integrados en la conversación, numerados "
        "dentro de la misma oración (no en formato de lista con saltos de línea). Ejemplo:\n"
        "   Cliente: \"Muéstrame opciones para caminar en ciudad.\"\n"
        "   Respuesta esperada: \"Encontré dos opciones relevantes: 1) Adidas Runfalcon, "
        "orientada a caminata, trote suave y uso diario; 2) Nike Pegasus 41, pensada para "
        "running urbano y entrenamiento diario.\"\n"
        "5. Si tu respuesta menciona UN SOLO producto, NO lo numeres (nada de \"1)\"): "
        "menciónalo directamente en la oración.\n"
        "6. Si no tienes más detalle del que aparece arriba sobre una política (ej. no se "
        "especifican las 'condiciones comerciales vigentes' exactas), dilo directamente y "
        "sugiere que el cliente contacte soporte para más detalle. NO inventes ejemplos ni "
        "categorías que no estén en el texto (ej. no asumas que se relacionan con "
        "\"promociones\" si el texto no lo dice).\n"
        "7. Si el mensaje trae varias preguntas, responde cada una.\n"
    )

    # 6. Ensamblaje final
    prompt_maestro = (
        f"{history_text}\n"
        f"---------------------\n"
        f"{productos_text}"
        f"{politicas_text}"
        f"{transient_text}"
        f"---------------------\n"
        f"NUEVO MENSAJE DEL CLIENTE: {user_message}\n\n"
        f"{instrucciones}"
    )

    return prompt_maestro