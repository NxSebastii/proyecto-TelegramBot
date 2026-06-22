# bot/prompt_builder.py

def format_retrieved_products(products_list: list) -> str:
    """
    Convierte la lista de diccionarios de productos en texto estructurado.
    Evita inyectar JSON crudo para ahorrar tokens y mejorar la comprensión del LLM.
    """
    if not products_list:
        return "No hay productos en el contexto actual."
    
    formatted_text = "CATÁLOGO RECUPERADO (Únicos productos que puedes ofrecer):\n"
    for i, prod in enumerate(products_list):
        nombre = prod.get('nombre', 'Producto sin nombre')
        precio = prod.get('precio', 'Precio no disponible')
        tallas = prod.get('tallas', [])
        descripcion = prod.get('descripcion', '')
        
        # El formato numerado es clave para resolver referencias como "el segundo"
        formatted_text += f"{i + 1}. Producto: {nombre}\n"
        formatted_text += f"   - Precio: ${precio}\n"
        formatted_text += f"   - Tallas disponibles: {', '.join(map(str, tallas))}\n"
        formatted_text += f"   - Descripción: {descripcion}\n\n"
        
    return formatted_text

def build_final_prompt(user_message: str, chat_history: list, products_list: list, transient_context: str) -> str:
    """Ensambla el historial, los productos, las políticas y el mensaje en un Prompt Maestro."""
    
    # 1. Formateamos el historial
    history_text = "HISTORIAL RECIENTE:\n"
    if not chat_history:
        history_text += "(No hay historial previo)\n"
    else:
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"
            
    # 2. Formateamos los productos
    products_text = format_retrieved_products(products_list)
    
    # 3. Añadimos contexto temporal (ej. políticas) si existe
    transient_text = ""
    if transient_context:
        transient_text = f"INFORMACIÓN OPERATIVA RELEVANTE:\n{transient_context}\n"
    
    # 4. Ensamblaje final con instrucciones estrictas de anclaje
    prompt_maestro = (
        f"{history_text}\n"
        f"---------------------\n"
        f"{transient_text}"
        f"{products_text}"
        f"---------------------\n"
        f"NUEVO MENSAJE DEL CLIENTE: {user_message}\n\n"
        f"INSTRUCCIÓN OBLIGATORIA: Redacta tu respuesta basándote EXCLUSIVAMENTE en el Catálogo "
        f"Recuperado y la Información Operativa proporcionada arriba. Si la respuesta no está "
        f"en este texto, indica que no tienes la información."
    )
    
    return prompt_maestro