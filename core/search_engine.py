from data_parser import *

def buscador_productos(mensaje, NProductos = PRODUCTOS_CONSULTA, umbral = UMBRAL_PRODUCTOS):
    embedding_mensaje = model.encode(mensaje, convert_to_tensor=True)
    # Comparar con embeddings de productos
    similitudes_productos = util.cos_sim(embedding_mensaje, embeddings_productos)[0]
    orden_productos = similitudes_productos.argsort(descending=True)

    resultados = []
    for idx in orden_productos[:NProductos]:
        if similitudes_productos[idx] >= umbral:
            resultados.append(catalogo_resultados[idx])
        else:
            break
    return resultados

def buscador_politicas(mensaje, umbral = UMBRAL_POLITICAS):
    # Comparar con embeddings de políticas
    embedding_mensaje = model.encode(mensaje, convert_to_tensor=True)
    similitudes_politicas = util.cos_sim(embedding_mensaje, embeddings_politicas)[0]
    orden_politicas = similitudes_politicas.argsort(descending=True)
    resultados = []
    for idx in orden_politicas:
        if similitudes_politicas[idx] >= umbral:
            resultados.append(politicas_resultados[idx])
        else:
            break

    return resultados

def format_retrieved_products(products_list: list) -> str:
    """
    Convierte la lista de diccionarios de productos en texto estructurado.
    Movida a nivel de módulo (antes vivía dentro de classify_intent) para
    que prompt_builder.py pueda importarla sin ImportError.
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

def classify_intent(user_message: str):
    """
    Enrutador + recuperación en un solo paso.
    Retorna una tupla (contexto: str, productos: list):
      - contexto: texto ya formateado para inyectar en el prompt.
      - productos: lista de productos recuperados (solo poblada cuando
        gatilla la rama de catálogo; vacía en cualquier otro caso).
    """
    msg = user_message.lower()

    contexto = (
        "Se tiene para el usuario la siguiente información relevante con respecto a "
        "su petición, ordenada según la prioridad con la que se debe atender:\n\n"
    )

    # 1. Prioridad Máxima: Políticas
    politicas_encontradas = buscador_politicas(msg, umbral=UMBRAL_POLITICAS)
    if politicas_encontradas:
        texto_politicas = ""
        for p in politicas_encontradas:
            texto_politicas += f"- {p['tema']}: {p['contenido']}\n"
        contexto += f"A. Políticas atingentes a la petición (En orden de relevancia):\n{texto_politicas}\n"
        return contexto, []

    # 2. Prioridad Media: Búsqueda de productos en el catálogo
    productos_encontrados = buscador_productos(msg, NProductos=PRODUCTOS_CONSULTA, umbral=UMBRAL_PRODUCTOS)
    if productos_encontrados:
        contexto += f"B. Productos atingentes a la petición:\n{format_retrieved_products(productos_encontrados)}\n"
        return contexto, productos_encontrados

    # 3. Prioridad Baja: Saludos y continuidad
    return "No hay información relevante para la petición. Responder con un saludo o mensaje cordial y ofrecer ayuda adicional.", []