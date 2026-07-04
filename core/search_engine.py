from core.data_parser import *
from core.filtros import extraer_restricciones, TOLERANCIA_PRECIO_APROXIMADO

def puntaje_hibrido(similitudes_semanticas, tokens_consulta, tokens_corpus):
    """
    Combina, ítem por ítem, la similitud semántica (embeddings) con la
    proporción de palabras de la consulta que aparecen literalmente en el
    texto del ítem (palabra clave). El resultado es un puntaje ponderado
    por PESO_SEMANTICO / PESO_PALABRA_CLAVE.
    """
    puntajes = []
    for idx, tokens_item in enumerate(tokens_corpus):
        score_semantico = similitudes_semanticas[idx].item()
        coincidencias = tokens_consulta & tokens_item
        score_palabra_clave = len(coincidencias) / len(tokens_consulta) if tokens_consulta else 0.0
        puntajes.append(PESO_SEMANTICO * score_semantico + PESO_PALABRA_CLAVE * score_palabra_clave)
    return puntajes


def cumple_restricciones(producto: dict, restricciones: dict) -> bool:
    """
    Retorna True si el producto cumple TODAS las restricciones explícitas
    detectadas en la consulta. Una restricción en None significa que el
    usuario no la mencionó, así que no se filtra por ese campo.
    """
    if restricciones["marca"] and producto["marca"].lower() != restricciones["marca"]:
        return False

    if restricciones["color"]:
        colores_producto = [c.lower() for c in producto.get("colores", [])]
        if restricciones["color"] not in colores_producto:
            return False

    if restricciones["talla"] and restricciones["talla"] not in producto.get("tallas", []):
        return False

    if restricciones["precio_valor"] is not None:
        precio = producto["precio"]
        if restricciones["precio_es_maximo"]:
            if precio > restricciones["precio_valor"]:
                return False
        else:
            tolerancia = restricciones["precio_valor"] * TOLERANCIA_PRECIO_APROXIMADO
            if abs(precio - restricciones["precio_valor"]) > tolerancia:
                return False

    return True


def _rankear_productos(mensaje):
    """
    Calcula el ranking híbrido completo de productos para un mensaje.
    Función interna: la usan tanto buscador_productos (interfaz simple)
    como buscar_productos_con_diagnostico (para classify_intent).
    """
    embedding_mensaje = model.encode(mensaje, convert_to_tensor=True)
    similitudes_semanticas = util.cos_sim(embedding_mensaje, embeddings_productos)[0]
    tokens_consulta = tokenizar(mensaje)
    puntajes = puntaje_hibrido(similitudes_semanticas, tokens_consulta, tokens_productos)
    orden_productos = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)
    return orden_productos, puntajes


def buscador_productos(mensaje, NProductos = PRODUCTOS_CONSULTA, umbral = UMBRAL_PRODUCTOS):
    orden_productos, puntajes = _rankear_productos(mensaje)
    restricciones = extraer_restricciones(mensaje)

    resultados = []
    for idx in orden_productos:
        if puntajes[idx] < umbral:
            break  # el resto del orden tiene aún menos puntaje, no hay más candidatos válidos

        if not cumple_restricciones(catalogo_resultados[idx], restricciones):
            continue  # relevante semánticamente, pero no cumple una restricción explícita

        resultados.append(catalogo_resultados[idx])
        if len(resultados) >= NProductos:
            break

    return resultados


def buscar_productos_con_diagnostico(mensaje, NProductos = PRODUCTOS_CONSULTA, umbral = UMBRAL_PRODUCTOS):
    """
    Igual que buscador_productos, pero además indica SI hubo candidatos
    semánticamente relevantes que quedaron descartados solo por las
    restricciones explícitas (marca/color/talla/precio). Esto permite
    diferenciar "no hay nada relacionado con la consulta" de "sí existe
    la categoría, pero ningún producto cumple lo que pidió el cliente".
    """
    orden_productos, puntajes = _rankear_productos(mensaje)
    restricciones = extraer_restricciones(mensaje)

    candidatos_relevantes = [idx for idx in orden_productos if puntajes[idx] >= umbral]

    resultados = []
    for idx in candidatos_relevantes:
        if cumple_restricciones(catalogo_resultados[idx], restricciones):
            resultados.append(catalogo_resultados[idx])
            if len(resultados) >= NProductos:
                break

    return {
        "productos": resultados,
        "hubo_candidatos_relevantes": bool(candidatos_relevantes),
        "descartado_por_restriccion": bool(candidatos_relevantes) and not resultados,
        "restricciones": restricciones,
    }

def buscador_politicas(mensaje, umbral = UMBRAL_POLITICAS):
    embedding_mensaje = model.encode(mensaje, convert_to_tensor=True)
    similitudes_semanticas = util.cos_sim(embedding_mensaje, embeddings_politicas)[0]
    tokens_consulta = tokenizar(mensaje)

    puntajes = puntaje_hibrido(similitudes_semanticas, tokens_consulta, tokens_politicas)
    orden_politicas = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)

    resultados = []
    for idx in orden_politicas:
        if puntajes[idx] >= umbral:
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
    diagnostico = buscar_productos_con_diagnostico(msg, NProductos=PRODUCTOS_CONSULTA, umbral=UMBRAL_PRODUCTOS)

    if diagnostico["productos"]:
        contexto += f"B. Productos atingentes a la petición:\n{format_retrieved_products(diagnostico['productos'])}\n"
        return contexto, diagnostico["productos"]

    if diagnostico["descartado_por_restriccion"]:
        restricciones_detectadas = ", ".join(
            f"{clave}={valor}" for clave, valor in diagnostico["restricciones"].items() if valor
        )
        contexto_sin_stock = (
            "IMPORTANTE: SÍ existen productos relacionados con la categoría que pide el cliente, "
            "pero NINGUNO cumple con las restricciones específicas que mencionó "
            f"({restricciones_detectadas}). Esto es información real y confirmada, NO una falta de "
            "datos: comunícale directamente al cliente que no hay stock con esas características "
            "exactas (nunca respondas como si no tuvieras la información)."
        )
        return contexto_sin_stock, []

    # 3. Prioridad Baja: Saludos y continuidad
    return "No hay información relevante para la petición. Responder con un saludo o mensaje cordial y ofrecer ayuda adicional.", []