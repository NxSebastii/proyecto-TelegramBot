# Nuestro diccionario principal en RAM
session_state = {}

def get_or_create_session(chat_id: str) -> dict:
    """Recupera la sesión de un usuario usando chat_id como clave primaria."""
    chat_id_str = str(chat_id)
    if chat_id_str not in session_state:
        session_state[chat_id_str] = {
            "chat_history": [],           # Lista de diccionarios (rol y mensaje)
            "last_viewed_products": [],   # Lista de productos recuperados (max 5)
            "last_viewed_policies": [],   # Lista de políticas recuperadas (max 3)
            "transient_context": ""       # Texto temporal (ej. políticas)
        }
    return session_state[chat_id_str]

def add_message_to_history(chat_id: str, role: str, content: str):
    """
    Añade un mensaje al historial. 
    Límite estricto: mantiene un máximo de 6 mensajes para no saturar los tokens.
    """
    session = get_or_create_session(chat_id)
    session["chat_history"].append({"role": role, "content": content})
    
    # Recorte automático como definiste en tu plan
    if len(session["chat_history"]) > 6:
        session["chat_history"].pop(0)

def update_last_viewed_products(chat_id: str, new_products: list):
    """
    Añade nuevos productos a la memoria sin borrar los anteriores, 
    evitando duplicados y manteniendo un máximo de 5 para no saturar tokens.
    """
    session = get_or_create_session(chat_id)
    current_products = session["last_viewed_products"]
    
    for new_prod in new_products:
        # Evitamos agregar el mismo producto dos veces revisando su ID
        if not any(p.get("id") == new_prod.get("id") for p in current_products):
            current_products.append(new_prod)
            
    # Mantenemos solo los 5 más recientes (recortando los más viejos al inicio de la lista)
    session["last_viewed_products"] = current_products[-5:]

def update_last_viewed_policies(chat_id: str, new_policies: list):
    """
    Añade nuevas políticas a la memoria sin borrar las anteriores,
    evitando duplicados (por tema) y manteniendo un máximo de 3.
    Esto permite responder preguntas de seguimiento sobre la misma política
    ("¿cuáles son esas condiciones?") sin necesitar que la búsqueda semántica
    la vuelva a encontrar en cada turno.
    """
    session = get_or_create_session(chat_id)
    current_policies = session["last_viewed_policies"]

    for new_pol in new_policies:
        if not any(p.get("tema") == new_pol.get("tema") for p in current_policies):
            current_policies.append(new_pol)

    session["last_viewed_policies"] = current_policies[-3:]

def set_transient_context(chat_id: str, context_text: str):
    """Inyecta información temporal, como un extracto del manual operativo."""
    session = get_or_create_session(chat_id)
    session["transient_context"] = context_text

def clear_transient_context(chat_id: str):
    """
    REGLA DE ORO: Limpia el contexto temporal. 
    Evita que las políticas consultadas ayer contaminen la búsqueda de hoy.
    """
    session = get_or_create_session(chat_id)
    session["transient_context"] = ""

def clear_session(chat_id: str):
    """Borra completamente la memoria de un usuario (Para tu comando /limpiar)."""
    chat_id_str = str(chat_id)
    if chat_id_str in session_state:
        del session_state[chat_id_str]