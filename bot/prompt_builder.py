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
        "3. Integra la descripción de forma natural en la conversación. No enumeres atributos "
        "en formato de lista.\n"
        "4. Si el cliente se refiere a un producto puntual (\"el segundo\", \"el más barato\"), "
        "identifícalo con la lista numerada del contexto.\n"
        "5. Si el mensaje trae varias preguntas, responde cada una.\n"
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