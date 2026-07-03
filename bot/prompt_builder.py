# bot/prompt_builder.py
from core.search_engine import format_retrieved_products, buscador_productos, PRODUCTOS_CONSULTA, UMBRAL_PRODUCTOS

def build_final_prompt(user_message: str, chat_history: list, products_list: list, transient_context: str) -> str:
    """Ensambla el historial, los productos, las políticas y el mensaje en un Prompt Maestro."""
    
    # 1. Formateamos el historial
    history_text = "HISTORIAL RECIENTE:\n"
    if not chat_history:
        history_text += "(No hay historial previo)\n"
    else:
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"
            
    # 2. Añadimos contexto temporal (ej. políticas) si existe
    transient_text = ""
    if transient_context:
        transient_text = f"INFORMACIÓN OPERATIVA RELEVANTE:\n{transient_context}\n"
    
    # 4. Ensamblaje final con instrucciones estrictas de anclaje
    prompt_maestro = (
        f"{history_text}\n"
        f"---------------------\n"
        f"{transient_text}"
        f"---------------------\n"
        f"NUEVO MENSAJE DEL CLIENTE: {user_message}\n\n"
        f"INSTRUCCIÓN OBLIGATORIA: Redacta tu respuesta basándote EXCLUSIVAMENTE en el Catálogo "
        f"Recuperado y la Información Operativa proporcionada arriba. Si la respuesta no está "
        f"en este texto, indica que no tienes la información."
    )
    
    return prompt_maestro