def classify_intent(user_message: str) -> str:
    msg = user_message.lower()
    
    # 1. Prioridad Máxima: Políticas
    if any(word in msg for word in ["devolución", "garantía", "reembolso", "política"]):
        return "politicas"
    
    # 2. Prioridad Media: Búsqueda de productos en el catálogo
    elif any(word in msg for word in ["zapatilla", "nike", "correr", "frío", "chaqueta", "parka", "adidas"]):
        return "catalogo"
        
    # 3. Prioridad Baja: Saludos y continuidad
    elif any(word in msg for word in ["hola", "gracias", "adios", "ok", "no", "si"]):
        return "continuidad"
    
    return "catalogo" # Por defecto

def mock_search_products(user_message: str) -> list:
    """
    Mock del motor de búsqueda híbrido (RAG).
    Devuelve listas de diccionarios estáticas simulando los resultados del JSON.
    """
    msg = user_message.lower()
    
    # Caso de prueba 1: Zapatillas
    if "zapatilla" in msg or "nike" in msg or "correr" in msg:
        return [
            {
                "id": "ZAP-001", 
                "nombre": "Nike Pegasus 40", 
                "precio": 120000, 
                "tallas": [40, 41, 42], 
                "descripcion": "Zapatillas de running neutras con excelente amortiguación."
            },
            {
                "id": "ZAP-002", 
                "nombre": "Adidas Runfalcon", 
                "precio": 45000, 
                "tallas": [39, 42, 43], 
                "descripcion": "Calzado ideal para iniciarse en el running, ligeras y transpirables."
            }
        ]
        
    # Caso de prueba 2: Abrigo / Frío
    elif "frío" in msg or "chaqueta" in msg or "parka" in msg:
        return [
            {
                "id": "ROPA-101", 
                "nombre": "Chaqueta North Face Resolve", 
                "precio": 95000, 
                "tallas": ["S", "M", "L"], 
                "descripcion": "Cortavientos impermeable para invierno extremo."
            }
        ]
        
    # Caso de prueba 3: No se encuentra nada
    else:
        return []

def mock_search_policies(user_message: str) -> str:
    """
    Mock de búsqueda semántica en políticas.
    """
    return (
        "POLÍTICA DE DEVOLUCIONES: Los clientes tienen 30 días para realizar cambios "
        "o devoluciones presentando la boleta original. El producto debe estar sellado. "
        "No aplican devoluciones en ropa interior ni artículos de uso personal."
    )

