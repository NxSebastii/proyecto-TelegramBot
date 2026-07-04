import re
import json
import os

RUTA_PRODUCTOS = os.path.join(os.path.dirname(__file__), "../data/productos.json")
RUTA_POLITICAS = os.path.join(os.path.dirname(__file__), "../data/politicas.json")
RUTA_EMBEDDINGS = os.path.join(os.path.dirname(__file__), "../data/embeddings.pkl")
with open(RUTA_PRODUCTOS, encoding="utf-8") as f:
    productos = json.load(f)

with open(RUTA_POLITICAS, encoding="utf-8") as f:
    politicas = json.load(f)
marcas_disponibles = sorted({p.get("marca", "").lower() for p in productos if p.get("marca")})
colores_disponibles = sorted({c.lower() for p in productos for c in p.get("colores", [])})

PALABRAS_ABSOLUTAS = ["menos de", "máximo", "maximo", "hasta", "bajo", "por menos de", "no más de"]

# Tolerancia usada cuando el precio detectado NO viene acompañado de una
# palabra de tope: se interpreta como precio aproximado (+-20%)
TOLERANCIA_PRECIO_APROXIMADO = 0.20


def extraer_marca(msg: str):
    """Retorna la marca detectada (en minúscula) o None si no se menciona ninguna."""
    msg = msg.lower()
    for marca in marcas_disponibles:
        if marca in msg:
            return marca
    return None


def extraer_color(msg: str):
    """Retorna el color detectado (en minúscula) o None si no se menciona ninguno."""
    msg = msg.lower()
    for color in colores_disponibles:
        if color in msg:
            return color
    return None


def extraer_talla(msg: str):
    """
    Busca patrones tipo "talla 42", "número 40", o un número suelto de 2 dígitos
    (heurística simple: la mayoría de tallas de calzado/ropa están en ese rango).
    """
    msg = msg.lower()

    match = re.search(r"(?:talla|número|numero|n°|nro)\s*(\d{2,3})", msg)
    if match:
        return int(match.group(1))

    return None


def extraer_precio(msg: str):
    """
    Busca un monto en la consulta (ej. "$50.000", "50000", "50 mil").
    Retorna una tupla (precio_valor, es_precio_maximo).
    Si no encuentra ningún monto, retorna (None, False).
    """
    msg = msg.lower()
 
    match_mil = re.search(r"(\d+)\s*(?:mil|lucas?)\b", msg)
    if match_mil:
        valor = int(match_mil.group(1)) * 1000
        es_maximo = any(palabra in msg for palabra in PALABRAS_ABSOLUTAS)
        return valor, es_maximo
 
    match = re.search(r"(\d{1,3}(?:[.,]\d{3})+|\d{4,})", msg)
    if not match:
        return None, False
 
    valor = int(match.group(1).replace(".", "").replace(",", ""))
    es_maximo = any(palabra in msg for palabra in PALABRAS_ABSOLUTAS)
    return valor, es_maximo


def extraer_restricciones(msg: str) -> dict:
    """
    Punto de entrada único: devuelve un diccionario con todas las
    restricciones explícitas detectadas en el mensaje del usuario.
    Cada campo es None si no se menciona esa restricción.
    """
    precio_valor, precio_es_maximo = extraer_precio(msg)

    return {
        "marca": extraer_marca(msg),
        "color": extraer_color(msg),
        "talla": extraer_talla(msg),
        "precio_valor": precio_valor,
        "precio_es_maximo": precio_es_maximo,
    }


if __name__ == "__main__":
    # Pruebas rápidas manuales
    ejemplos = [
        "quiero zapatillas Nike talla 42",
        "algo negro para correr, menos de 80000 pesos",
        "tienen chaquetas azules por ahí como 60 lucas",
        "hola, buenas tardes",
    ]
    for ejemplo in ejemplos:
        print(ejemplo, "->", extraer_restricciones(ejemplo))