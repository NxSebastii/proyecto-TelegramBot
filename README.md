# Novac - Agente Virtual de Retail (ACME) 🚀

Este repositorio contiene la implementación de **Novac**, un agente virtual contextual diseñado para operar en Telegram. A diferencia de un bot tradicional de reglas, Novac utiliza un flujo RAG (Retrieval-Augmented Generation) direccional estricto, memoria en RAM estructurada y el modelo **Gemini 2.5 Flash** para asistir a los clientes en la búsqueda de productos y resolución de dudas operativas.

## 🧠 Arquitectura General del Sistema (Pipeline)

El sistema opera bajo un principio estricto de separación de responsabilidades, dividiendo el flujo en 5 etapas principales:

1. **Recepción (Telegram):** Captura asíncrona de mensajes vía `python-telegram-bot` (`bot/telegram_app.py`).
2. **Enrutamiento Lógico:** Clasificación de la intención del usuario (Catálogo, Políticas o Continuidad Conversacional) para optimizar la recuperación.
3. **Recuperación Dirigida (RAG):**
   - **Catálogo:** Extracción de filtros exactos combinada con búsqueda vectorial (`sentence-transformers`) sobre `productos.json`. Excluye automáticamente productos sin stock.
   - **Políticas:** Búsqueda semántica pura en `politicas.json`.
4. **Modelo de Estado (Memoria en RAM):** Recuperación e inyección del historial conversacional y los últimos productos vistos vinculados al `chat_id` del usuario (`bot/memory.py`).
5. **Generación (LLM):** Ensamblaje del prompt maestro e invocación a la API de Gemini, aplicando reglas estrictas de anti-alucinación y formato HTML para Telegram (`bot/llm_client.py` y `bot/prompt_builder.py`).

## 📂 Organización del Repositorio

La estructura modular garantiza la escalabilidad y facilita el desarrollo en paralelo:

```text
📦 raiz_del_proyecto
 ┣ 📂 bot/                 # Interfaz de usuario y conexión con la IA
 ┃ ┣ 📜 llm_client.py      # Cliente de la API de Google GenAI (Gemini) y System Prompt
 ┃ ┣ 📜 memory.py          # Gestor de estado (Diccionario relacional en RAM)
 ┃ ┣ 📜 prompt_builder.py  # Ensamblador de contexto y formateo en Markdown
 ┃ ┗ 📜 telegram_app.py    # Controladores, handlers y webhook de Telegram
 ┣ 📂 core/                # Lógica de negocio y motor de búsqueda
 ┃ ┣ 📜 data_parser.py     # Limpieza, validación de JSONs y control de stock
 ┃ ┗ 📜 search_engine.py   # Motor RAG híbrido y semántico
 ┣ 📂 data/                # Bases de datos estáticas
 ┃ ┣ 📜 productos.json
 ┃ ┗ 📜 politicas.json
 ┣ 📜 .env                 # Variables de entorno (No versionado)
 ┣ 📜 config.py            # Cargador centralizado de configuraciones
 ┣ 📜 main.py              # Orquestador y punto de entrada del sistema
 ┗ 📜 README.md            # Documentación