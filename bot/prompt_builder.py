# bot/prompt_builder.py
from core.search_engine import format_retrieved_products

def build_final_prompt(user_message: str, chat_history: list, productos_recientes: list, transient_context: str) -> str:
    """Ensambla el historial, los productos vistos recientemente, el contexto recuperado y el mensaje en un Prompt Maestro."""

    # 1. Formateamos el historial
    history_text = "HISTORIAL RECIENTE:\n"
    if not chat_history:
        history_text += "(No hay historial previo)\n"
    else:
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"

    # 2. Productos que el cliente ya vio en turnos anteriores. Esto se
    # incluye SIEMPRE que exista (no solo cuando la búsqueda de este turno
    # encontró algo nuevo), para poder resolver referencias como "el más
    # barato" o "el segundo" sin tener que volver a buscar en el catálogo.
    productos_text = ""
    if productos_recientes:
        productos_text = (
            "PRODUCTOS MOSTRADOS RECIENTEMENTE AL CLIENTE (usa esta lista si el cliente "
            "se refiere a 'el más barato', 'el primero', 'el segundo', 'ese', etc. sin "
            "nombrar el producto de nuevo):\n"
            f"{format_retrieved_products(productos_recientes)}\n"
        )

    # 3. Añadimos contexto temporal (políticas o catálogo recién buscado) si existe
    transient_text = ""
    if transient_context:
        transient_text = f"INFORMACIÓN OPERATIVA RELEVANTE (búsqueda de este turno):\n{transient_context}\n"

    # 4. Instrucciones: numeradas y breves (mejor seguimiento en modelos flash/free tier)
    instrucciones = (
        "INSTRUCCIONES:\n"
        "1. Usa SOLO la información de arriba. No inventes productos, precios ni datos.\n"
        "2. Si arriba se indica que NINGÚN producto cumple lo pedido, dilo directamente como "
        "un hecho confirmado (ej. \"no tenemos ese producto en esa talla/color\"). "
        "NUNCA lo presentes como si te faltara información.\n"
        "3. Si el cliente se refiere a un producto anterior (\"el más barato\", \"el "
        "primero\", \"ese\", \"el segundo\") y la INFORMACIÓN OPERATIVA de este turno no "
        "trae productos nuevos, resuélvelo usando PRODUCTOS MOSTRADOS RECIENTEMENTE — NO "
        "asumas que se refiere a otra cosa del catálogo general.\n"
        "4. Menciona los productos por su NOMBRE, integrados en la conversación, numerados "
        "dentro de la misma oración (no en formato de lista con saltos de línea). Ejemplo:\n"
        "   Cliente: \"Muéstrame opciones para caminar en ciudad.\"\n"
        "   Respuesta esperada: \"Encontré dos opciones relevantes: 1) Adidas Runfalcon, "
        "orientada a caminata, trote suave y uso diario; 2) Nike Pegasus 41, pensada para "
        "running urbano y entrenamiento diario.\"\n"
        "5. Si tu respuesta menciona UN SOLO producto, NO lo numeres (nada de \"1)\"): "
        "menciónalo directamente en la oración.\n"
        "6. Si el mensaje trae varias preguntas, responde cada una.\n"
    )

    # 5. Ensamblaje final
    prompt_maestro = (
        f"{history_text}\n"
        f"---------------------\n"
        f"{productos_text}"
        f"{transient_text}"
        f"---------------------\n"
        f"NUEVO MENSAJE DEL CLIENTE: {user_message}\n\n"
        f"{instrucciones}"
    )

    return prompt_maestro