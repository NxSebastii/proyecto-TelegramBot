#data parser
import pickle
import re

from sentence_transformers import SentenceTransformer, util
import json
import os
model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v1")

RUTA_PRODUCTOS = os.path.join(os.path.dirname(__file__), "../data/productos.json")
RUTA_POLITICAS = os.path.join(os.path.dirname(__file__), "../data/politicas.json")
RUTA_EMBEDDINGS = os.path.join(os.path.dirname(__file__), "../data/embeddings.pkl")


UMBRAL_PRODUCTOS = 0.07
UMBRAL_POLITICAS = 0.20
PRODUCTOS_CONSULTA = 3

# Ponderación de la búsqueda híbrida: cuánto pesa la similitud semántica
# (embeddings) vs. la coincidencia literal de palabras clave. Deben sumar 1.0.
PESO_SEMANTICO = 0.7
PESO_PALABRA_CLAVE = 0.3

def product_data(producto):
    """
    Función para parsear los datos de un producto y devolverlos en un formato estructurado.
    """
    return {
        "id": producto.get("id", ""),
        "nombre": producto.get("nombre", ""),
        "precio": producto.get("precio", 0),
        "tallas": producto.get("tallas", []),
        "descripcion": producto.get("descripcion", "")
    }

def policy_data(policy_text):
    """
    Función para parsear el texto de una política y devolverlo en un formato estructurado.
    """
    return {
        "tema": policy_text.get("tema", ""),
        "contenido": policy_text.get("contenido", "")
    }

def construir_texto_producto(producto):
    return (
        f"{producto.get('nombre', '')}. "
        f"{producto.get('descripcion', '')}. "
        f"Categoría: {producto.get('categoria', '')}. "
        f"Marca: {producto.get('marca', '')}. "
        f"Etiquetas: {', '.join(producto.get('tags', []))}."
    )

def construir_texto_politica(policy_text):
    """
    Texto en español natural que se embebe con el modelo para políticas.
    """
    return f"Tema: {policy_text.get('tema', '')}. {policy_text.get('contenido', '')}"

def tokenizar(texto):
    """Extrae el conjunto de palabras (en minúscula, sin puntuación) de un texto."""
    return set(re.findall(r"\w+", texto.lower()))

with open(RUTA_PRODUCTOS, encoding="utf-8") as f:
    productos = json.load(f)

with open(RUTA_POLITICAS, encoding="utf-8") as f:
    politicas = json.load(f)


# Texto que se embebe (va al modelo)
textos_embedding_productos = [construir_texto_producto(p) for p in productos]
textos_embedding_politicas = [construir_texto_politica(p) for p in politicas]

# Datos estructurados que se devuelven al usuario (mismo orden/índice que arriba)
catalogo_resultados = [product_data(p) for p in productos]
politicas_resultados = [policy_data(p) for p in politicas]

# Tokens precalculados de cada ítem, usados por la parte de palabra clave
# de la búsqueda híbrida (mismo orden/índice que las listas de arriba)
tokens_productos = [tokenizar(t) for t in textos_embedding_productos]
tokens_politicas = [tokenizar(t) for t in textos_embedding_politicas]

def generar_embeddings():
    if os.path.exists(RUTA_EMBEDDINGS):
        with open(RUTA_EMBEDDINGS, "rb") as f:
            embeddings = pickle.load(f)
        return embeddings["productos"], embeddings["politicas"]
    embeddings_productos = model.encode(textos_embedding_productos, convert_to_tensor=True)
    embeddings_politicas = model.encode(textos_embedding_politicas, convert_to_tensor=True)

    with open(RUTA_EMBEDDINGS, "wb") as f:
        pickle.dump({"productos": embeddings_productos, "politicas": embeddings_politicas}, f)
    return embeddings_productos, embeddings_politicas

embeddings_productos, embeddings_politicas = generar_embeddings()

