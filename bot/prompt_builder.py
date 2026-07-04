# bot/prompt_builder.py

def build_final_prompt(user_message: str, chat_history: list, transient_context: str) -> str:
    """Ensambla el historial, el contexto recuperado y el mensaje en un Prompt Maestro."""

    # 1. Formateamos el historial
    history_text = "HISTORIAL RECIENTE:\n"
    if not chat_history:
        history_text += "(No hay historial previo)\n"
    else:
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"

    # 2. Añadimos contexto temporal (políticas o catálogo recuperado) si existe
    transient_text = ""
    if transient_context:
        transient_text = f"INFORMACIÓN OPERATIVA RELEVANTE:\n{transient_context}\n"

    # 3. Instrucciones: numeradas y breves (mejor seguimiento en modelos flash/free tier)
    instrucciones = (
        "INSTRUCCIONES:\n"
        "1. Usa SOLO la información de arriba. No inventes productos, precios ni datos.\n"
        "2. Si arriba se indica que NINGÚN producto cumple lo pedido, dilo directamente como "
        "un hecho confirmado (ej. \"no tenemos ese producto en esa talla/color\"). "
        "NUNCA lo presentes como si te faltara información.\n"
        "3. Menciona los productos por su NOMBRE, integrados en la conversación, numerados "
        "dentro de la misma oración (no en formato de lista con saltos de línea). Ejemplo:\n"
        "   Cliente: \"Muéstrame opciones para caminar en ciudad.\"\n"
        "   Respuesta esperada: \"Encontré dos opciones relevantes: 1) Adidas Runfalcon, "
        "orientada a caminata, trote suave y uso diario; 2) Nike Pegasus 41, pensada para "
        "running urbano y entrenamiento diario.\"\n"
        "4. Si el cliente se refiere a un producto puntual (\"el segundo\", \"el más barato\"), "
        "identifícalo usando esa misma numeración.\n"
        "5. Si la INFORMACIÓN OPERATIVA de arriba no trae productos ni políticas nuevas "
        "(por ejemplo, solo indica que debes saludar), revisa el HISTORIAL RECIENTE antes de "
        "asumir que no sabes nada: si el cliente venía hablando de un producto o tema "
        "específico, continúa esa conversación de forma natural en vez de pedirle que repita "
        "lo que ya dijo.\n"
        "6. Si el mensaje trae varias preguntas, responde cada una.\n"
    )

    # 4. Ensamblaje final
    prompt_maestro = (
        f"{history_text}\n"
        f"---------------------\n"
        f"{transient_text}"
        f"---------------------\n"
        f"NUEVO MENSAJE DEL CLIENTE: {user_message}\n\n"
        f"{instrucciones}"
    )

    return prompt_maestro