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
    """
    embedding_mensaje = model.encode(mensaje, convert_to_tensor=True)
    similitudes_semanticas = util.cos_sim(embedding_mensaje, embeddings_productos)[0]
    tokens_consulta = tokenizar(mensaje)
    puntajes = puntaje_hibrido(similitudes_semanticas, tokens_consulta, tokens_productos)
    orden_productos = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)
    return orden_productos, puntajes


def _rankear_politicas(mensaje):
    """
    Calcula el ranking híbrido completo de políticas para un mensaje.
    """
    embedding_mensaje = model.encode(mensaje, convert_to_tensor=True)
    similitudes_semanticas = util.cos_sim(embedding_mensaje, embeddings_politicas)[0]
    tokens_consulta = tokenizar(mensaje)
    puntajes = puntaje_hibrido(similitudes_semanticas, tokens_consulta, tokens_politicas)
    orden_politicas = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)
    return orden_politicas, puntajes


def buscador_productos(mensaje, NProductos = PRODUCTOS_CONSULTA, umbral = UMBRAL_PRODUCTOS):
    """
    Interfaz simple: SIEMPRE retorna una lista de productos (posiblemente
    vacía). La usan telegram_app.py y cualquier otro lugar que solo
    necesite los resultados, sin el diagnóstico de restricciones.
    """
    orden_productos, puntajes = _rankear_productos(mensaje)
    restricciones = extraer_restricciones(mensaje)

    resultados = []
    for idx in orden_productos:
        if puntajes[idx] < umbral:
            break

        if not cumple_restricciones(catalogo_resultados[idx], restricciones):
            continue

        resultados.append(catalogo_resultados[idx])
        if len(resultados) >= NProductos:
            break

    return resultados


def buscar_productos_con_diagnostico(mensaje, NProductos = PRODUCTOS_CONSULTA, umbral = UMBRAL_PRODUCTOS):
    """
    Igual que buscador_productos, pero además informa:
      - puntaje_maximo: el mejor puntaje híbrido obtenido (0.0 si el
        catálogo está vacío), usado por classify_intent para comparar
        contra el puntaje de políticas y decidir cuál rama es más relevante.
      - hubo_candidatos_relevantes / descartado_por_restriccion: para
        diferenciar "no hay nada relacionado" de "hay categoría pero nada
        cumple las restricciones explícitas".
    """
    orden_productos, puntajes = _rankear_productos(mensaje)
    restricciones = extraer_restricciones(mensaje)

    puntaje_maximo = puntajes[orden_productos[0]] if orden_productos else 0.0
    candidatos_relevantes = [idx for idx in orden_productos if puntajes[idx] >= umbral]

    resultados = []
    for idx in candidatos_relevantes:
        if cumple_restricciones(catalogo_resultados[idx], restricciones):
            resultados.append(catalogo_resultados[idx])
            if len(resultados) >= NProductos:
                break

    return {
        "productos": resultados,
        "puntaje_maximo": puntaje_maximo,
        "hubo_candidatos_relevantes": bool(candidatos_relevantes),
        "descartado_por_restriccion": bool(candidatos_relevantes) and not resultados,
        "restricciones": restricciones,
    }


def buscador_politicas(mensaje, umbral = UMBRAL_POLITICAS):
    orden_politicas, puntajes = _rankear_politicas(mensaje)

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
    """
    if not products_list:
        return "No hay productos en el contexto actual."

    formatted_text = "CATÁLOGO RECUPERADO (Únicos productos que puedes ofrecer):\n"
    for i, prod in enumerate(products_list):
        nombre = prod.get('nombre', 'Producto sin nombre')
        marca = prod.get('marca', '')
        precio = prod.get('precio', 'Precio no disponible')
        tallas = prod.get('tallas', [])
        colores = prod.get('colores', [])
        descripcion = prod.get('descripcion', '')

        # El formato numerado es clave para resolver referencias como "el segundo"
        formatted_text += f"{i + 1}. Producto: {nombre} (Marca: {marca})\n"
        formatted_text += f"   - Precio: ${precio}\n"
        formatted_text += f"   - Tallas disponibles: {', '.join(map(str, tallas))}\n"
        formatted_text += f"   - Colores disponibles: {', '.join(colores) if colores else 'No especificado'}\n"
        formatted_text += f"   - Descripción: {descripcion}\n\n"

    return formatted_text

def classify_intent(user_message: str):
    """
    Enrutador + recuperación en un solo paso.
    Retorna una tupla (contexto: str, productos: list, politicas: list).

    En vez de darle prioridad ciega a políticas sobre productos, se compara
    el puntaje híbrido máximo de cada rama: solo gana políticas si su mejor
    puntaje es mayor o igual al mejor puntaje de productos. Esto evita que
    preguntas de catálogo ("qué tienes de zapatillas") sean capturadas por
    una política semánticamente parecida (ej. la de stock/disponibilidad).
    """
    msg = user_message.lower()

    contexto = (
        "Se tiene para el usuario la siguiente información relevante con respecto a "
        "su petición, ordenada según la prioridad con la que se debe atender:\n\n"
    )

    orden_politicas, puntajes_politicas = _rankear_politicas(msg)
    mejor_puntaje_politica = puntajes_politicas[orden_politicas[0]] if orden_politicas else 0.0
    politica_relevante = mejor_puntaje_politica >= UMBRAL_POLITICAS

    diagnostico = buscar_productos_con_diagnostico(msg, NProductos=PRODUCTOS_CONSULTA, umbral=UMBRAL_PRODUCTOS)
    producto_relevante = diagnostico["hubo_candidatos_relevantes"]
    mejor_puntaje_producto = diagnostico["puntaje_maximo"]

    usar_politica = politica_relevante and (
        not producto_relevante or mejor_puntaje_politica >= mejor_puntaje_producto
    )

    # 1. Rama políticas (solo si de verdad es la más relevante de las dos)
    if usar_politica:
        politicas_encontradas = [
            politicas_resultados[idx] for idx in orden_politicas
            if puntajes_politicas[idx] >= UMBRAL_POLITICAS
        ]
        texto_politicas = "".join(f"- {p['tema']}: {p['contenido']}\n" for p in politicas_encontradas)
        contexto += f"A. Políticas atingentes a la petición (En orden de relevancia):\n{texto_politicas}\n"
        return contexto, [], politicas_encontradas

    # 2. Rama productos
    if diagnostico["productos"]:
        contexto += f"B. Productos atingentes a la petición:\n{format_retrieved_products(diagnostico['productos'])}\n"
        return contexto, diagnostico["productos"], []

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
        return contexto_sin_stock, [], []

    # 3. Prioridad Baja: Saludos y continuidad
    return "No hay información relevante para la petición. Responder con un saludo o mensaje cordial y ofrecer ayuda adicional.", [], []