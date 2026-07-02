#data parser
import pickle

from sentence_transformers import SentenceTransformer, util
import json
import os
model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v1")

RUTA_PRODUCTOS = os.path.join(os.path.dirname(__file__), "../data/productos.json")
RUTA_POLITICAS = os.path.join(os.path.dirname(__file__), "../data/politicas.json")
RUTA_EMBEDDINGS = os.path.join(os.path.dirname(__file__), "../data/embeddings.pkl")


UMBRAL_PRODUCTOS = 0.10
UMBRAL_POLITICAS = 0.30
PRODUCTOS_CONSULTA = 5

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
    """
    Texto en español natural que se embebe con el modelo. Este texto NO se
    muestra al usuario, solo sirve para que el modelo entienda el producto.
    """
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

if __name__ == "__main__":
    # Prueba rápida manual
    consulta_prueba = "algo abrigado para el frío de la montaña"
    print("Productos encontrados:")
    for p in buscador_productos(consulta_prueba):
        print("-", p["nombre"])

    print("\nPolítica encontrada:")
    print(buscador_politicas("quiero devolver un producto")[0]["tema"])