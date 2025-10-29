<h1> <img width="207" height="112" alt="image" src="https://github.com/user-attachments/assets/89fd906b-04fb-4d4f-b5e6-8375083a8a01" /></h1>
<h1>📚 Maestría en Inteligencia Artificial Aplicada – 3er Semestre</h1>

<h3>Asignatura: Inteligencia Artificial Generativa</h3>

<h3>Taller Final</h3>

<hr style="width:60%;">

<h3>👨‍🎓 Estudiantes</h3>
<ul style="list-style:none; padding:0; font-size:18px;">
    <li>Sebastián Murillas</li>
    <li>Octavio Guerra</li>
</ul>

<hr style="width:60%;">

<h3>📅 Fecha: Octubre 28, 2025</h3>

## Arquitectura
- **Frontend:** [`app_ecomarket.py`](app_ecomarket.py) implementa la interfaz en Streamlit.
- **Agente conversacional:** [`agente_ecomarket.py`](agente_ecomarket.py) inicializa el agente, herramientas de negocio y RAG.
- **Herramientas de negocio:** [`herramientas_ecomarket.py`](herramientas_ecomarket.py) simula verificaciones de pedidos, generación de etiquetas y reembolsos.
- **Sistema RAG:** [`rag_system.py`](rag_system.py) descarga documentos de referencia, construye un índice Chroma y responde preguntas con contexto.
- **Datos locales de referencia:** carpeta [`documentos_rag/`](documentos_rag/) con PDFs, CSV y JSON empleados en modo offline.

## Requisitos previos
1. **Python** 3.10 o superior.
2. **Clave de OpenAI** con acceso al modelo `gpt-4o-mini` (puedes ajustar el modelo en `agente_ecomarket.py`).
3. Dependencias del sistema para `pypdf`, `chromadb` y `sentence-transformers` (por ejemplo, `build-essential`, `libssl-dev`, `poppler-utils` en Debian/Ubuntu).
4. (Opcional) **PyTorch** para aprovechar GPU; el sistema usa CPU automáticamente si no está disponible.

## Instalación
```bash
# 1. Clonar el repositorio
git clone https://github.com/<usuario>/EntregaFinalGenIA25-2.git
cd EntregaFinalGenIA25-2

# 2. Crear y activar un entorno virtual (opcional pero recomendado)
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuración de variables de entorno
Crea un archivo `.env` en la raíz del proyecto con tu clave de OpenAI:

```
OPENAI_API_KEY="tu_clave_aqui"
```

El archivo [`app_ecomarket.py`](app_ecomarket.py) carga automáticamente este valor mediante `python-dotenv`.

## Preparar la base de conocimiento (RAG)
Al iniciar el agente, el módulo [`rag_system.py`](rag_system.py) intentará:
1. Cargar una base Chroma persistida en `./chroma_db`.
2. Si no existe o está vacía, descargar los documentos oficiales definidos en `GITHUB_RAW_URL` y generar los *embeddings*.

Si tu entorno no tiene acceso a internet, copia los documentos manualmente a `documentos_rag/` y ejecuta una reconstrucción forzada:

```bash
python - <<'PY'
from rag_system import load_remote_documents, build_or_load_chroma

docs = load_remote_documents(base_url="file://$(pwd)/documentos_rag/")
build_or_load_chroma(docs=docs, force_rebuild=True)
PY
```

También puedes borrar la base para regenerarla desde cero:

```bash
python - <<'PY'
from rag_system import build_or_load_chroma

build_or_load_chroma(force_rebuild=True)
PY
```

## Ejecución local
```bash
streamlit run app_ecomarket.py
```

El asistente quedará disponible en `http://localhost:8501`. La primera carga puede tardar mientras se construye el índice RAG.

## Flujo de uso
1. Ingresa el número de pedido (`P-XXXX`) o tu número de identificación (8 dígitos).
2. El agente verificará la elegibilidad y pedirá confirmación antes de generar etiqueta y reembolso (implementado en `herramientas_ecomarket.py`).
3. Si no hay una devolución en proceso, puedes hacer preguntas sobre políticas y productos. El agente consultará la base RAG mediante la herramienta `consultar_conocimiento_rag`.

## Despliegue
### Streamlit Community Cloud
1. Publica el repositorio en GitHub.
2. En [Streamlit Community Cloud](https://streamlit.io/cloud), crea una nueva app apuntando a `app_ecomarket.py`.
3. Define la variable de entorno `OPENAI_API_KEY` en la sección *Advanced settings*.
4. (Opcional) Sube los documentos RAG a un bucket público o incluye la carpeta `documentos_rag/` en el repositorio.

### Contenedor Docker (opcional)
Crea un archivo `Dockerfile` (no incluido) basado en `python:3.11-slim`, copia el proyecto y ejecuta `streamlit run app_ecomarket.py --server.port 8501 --server.address 0.0.0.0`. Asegúrate de inyectar `OPENAI_API_KEY` como variable de entorno y de persistir `./chroma_db` si deseas reutilizar el índice.

## Solución de problemas
- **Faltan dependencias del sistema**: instala `sudo apt-get update && sudo apt-get install -y build-essential libssl-dev poppler-utils`.
- **`sentence-transformers` no instalado**: verifica que `pip install -r requirements.txt` se haya ejecutado correctamente; es requerido por `HuggingFaceEmbeddings`.
- **Sin conexión a internet**: utiliza la carpeta `documentos_rag/` incluida y reconstruye la base con `force_rebuild=True`.
- **Errores de API de OpenAI**: revisa tu cuota y permisos para el modelo configurado.

## Licencia
Distribuido bajo la licencia MIT. Consulta el archivo [`LICENSE`](LICENSE) para más detalles.
