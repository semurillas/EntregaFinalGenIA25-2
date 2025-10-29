import os
import requests
import time
import shutil # Importado para manejar la eliminación de directorios
import json # Importamos JSON aquí para la carga y transformación de FAQ
from typing import List, Dict, Any, Optional

# Importamos la librería PyTorch para la detección de CUDA (Mejora la compatibilidad)
try:
    import torch
    # Determinar el dispositivo: 'cuda' si está disponible, sino 'cpu'
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
except ImportError:
    # Si PyTorch no está instalado, por defecto usamos 'cpu'
    DEVICE = 'cpu'
    print("ADVERTENCIA: PyTorch no está instalado. Usando 'cpu' por defecto para embeddings.")


# IMPORTS recomendados por la documentación actual de LangChain:
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
# Ya no necesitamos JSONLoader
# from langchain_community.document_loaders.json_loader import JSONLoader 

# Usamos HuggingFaceEmbeddings genérico
from langchain_community.embeddings import HuggingFaceEmbeddings 

# Importación esencial para la nueva sintaxis de LangChain
from langchain_core.messages import HumanMessage

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.schema import Document


# --- DIRECTORIO DONDE SE GUARDARÁN LOS DOCUMENTOS DESCARGADOS ---
DOWNLOAD_DIR = "documentos_rag"
# --- FIN DE CONFIGURACIÓN ---

# Base raw URL (tu repo)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/semurillas/GenIA-20252-ICESI/main/Taller%202/Documentos/"

# --- FUNCIÓN DE TRANSFORMACIÓN PARA EL JSON DE FAQ ---
def transform_faq_docs(raw_data: List[Dict[str, str]], source_file: str) -> List[Document]:
    """Combina pregunta/respuesta en el contenido a partir de la lista de diccionarios JSON."""
    transformed_docs = []
    for data in raw_data:
        try:
            pregunta = data.get("pregunta", "")
            respuesta = data.get("respuesta", "")
            
            # Nuevo contenido para el chunk
            new_content = f"PREGUNTA FRECUENTE: {pregunta}\nRESPUESTA: {respuesta}"
            
            # Crear un nuevo Document con el contenido combinado
            new_doc = Document(
                page_content=new_content,
                metadata={
                    'source': source_file,
                    'type': 'FAQ'
                }
            )
            transformed_docs.append(new_doc)
        except Exception as e:
            # En caso de error en la estructura de un ítem, lo ignoramos y avisamos
            print(f"ERROR al transformar ítem FAQ: {e}. Ítem: {data}")
    return transformed_docs

# --- FUNCIÓN DE CARGA CUSTOMIZADA PARA FAQ JSON ---
def load_faq_json_custom(file_path: str) -> List[Document]:
    """Carga y transforma FAQ JSON usando Python nativo, asumiendo formato JSON Lines o múltiples objetos."""
    file_name = os.path.basename(file_path)
    all_faq_items = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            
            # 1. Intentamos leer línea por línea (JSON Lines), que es robusto para el error "Extra data".
            for i, line in enumerate(f):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                
                try:
                    item = json.loads(stripped_line)
                    # Si el archivo tiene un array de objetos FAQ por línea, extendemos la lista
                    if isinstance(item, list):
                        all_faq_items.extend(item)
                    # Si es un objeto individual FAQ (JSON Lines), lo añadimos
                    elif isinstance(item, dict):
                        all_faq_items.append(item)
                    
                except json.JSONDecodeError:
                    # Si falla, la línea no es JSON válido, la ignoramos.
                    pass 
        
        # 2. Si la lectura línea por línea no arrojó resultados, intentamos una carga completa del archivo.
        if not all_faq_items:
             with open(file_path, 'r', encoding='utf-8') as f_full:
                 f_content = f_full.read().strip()
                 if f_content:
                      # Intentamos cargar el contenido completo
                      data_full = json.loads(f_content)
                      if isinstance(data_full, list):
                          all_faq_items.extend(data_full)
                      elif isinstance(data_full, dict):
                          all_faq_items.append(data_full)

        if all_faq_items:
            transformed_docs = transform_faq_docs(all_faq_items, file_name)
            # Imprimimos el total de documentos de FAQ cargados (debería ser > 0)
            print(f"DEBUG: {len(transformed_docs)} documentos cargados y transformados de {file_name}.")
            return transformed_docs
        else:
            print(f"ERROR: No se pudo extraer ningún dato JSON de {file_name}. ¿Archivo vacío o formato incorrecto?")
            return []
            
    except Exception as e:
        print(f"ERROR CRÍTICO: Falló la carga manual de FAQ JSON en {file_name}: {e}")
        return []
# ------------------------------------------------------------------


def download_file_from_github(raw_url: str, local_filename: str, timeout: int = 60) -> str:
    """
    Descarga un archivo remoto. Retorna el nombre del archivo local (con ruta) si es exitoso, o None si falla.
    """
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"DEBUG: Carpeta de descarga '{DOWNLOAD_DIR}' creada.")

    local_path = os.path.join(DOWNLOAD_DIR, local_filename)
    
    print(f"DEBUG: Intentando descargar: {raw_url} a {local_path}")
    corrected = raw_url.replace("/refs/heads/main/", "/main/")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(corrected, stream=True, timeout=timeout)
            resp.raise_for_status() # Lanza HTTPError si el código de estado es 4xx o 5xx
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"DEBUG: Descarga exitosa de {local_path}")
            return local_path
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Falló la descarga de {raw_url} (Intento {attempt + 1}/{max_retries}): {e}")
            if hasattr(resp, 'status_code') and resp.status_code == 404:
                 print("ERROR: Archivo no encontrado (404). Se omite.")
                 return None
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return None
    return None


def load_remote_documents(base_url: str = GITHUB_RAW_URL) -> List[Document]:
    """
    Descarga y carga los documentos definidos en el repositorio.
    Retorna lista de Document (langchain.schema.Document)
    """
    docs: List[Document] = []
    
    # Definición de archivos a cargar con Loader de LangChain
    files_to_load_lc = [
        ("Politica_de_Devoluciones_EcoMarket.pdf", "Politica_de_Devoluciones_EcoMarket.pdf", PyPDFLoader, {}),
        ("Terminos_y_Condiciones_Generales_de_Venta_EcoMarket.pdf", "Terminos_y_Condiciones_Generales_de_Venta_EcoMarket.pdf", PyPDFLoader, {}),
        ("Manual_de_Uso_Productos_Ecologicos.pdf", "Manual_de_Uso_Productos_Ecologicos.pdf", PyPDFLoader, {}),
    ]
    
    # Archivos a cargar con lógica customizada (para evitar dependencias)
    files_to_load_custom = [
        ("faq_ecomarket.json", "faq_ecomarket.json", load_faq_json_custom),
    ]

    # 1. Cargar documentos con LangChain Loaders
    for remote_name, local_name, Loader, loader_args in files_to_load_lc:
        downloaded_path = download_file_from_github(base_url + remote_name, local_name)
        
        if downloaded_path:
            try:
                loader = Loader(file_path=downloaded_path, **loader_args)
                loaded_docs = loader.load()
                docs.extend(loaded_docs)
                print(f"DEBUG: {len(loaded_docs)} documentos cargados de {local_name}.")
            except Exception as e:
                print(f"ERROR: Falló la carga de {local_name} con {Loader.__name__}: {e}")
                
    # 2. Cargar documentos con lógica Customizada (JSON FAQ)
    for remote_name, local_name, custom_loader_func in files_to_load_custom:
        downloaded_path = download_file_from_github(base_url + remote_name, local_name)
        
        if downloaded_path:
            loaded_docs = custom_loader_func(downloaded_path)
            docs.extend(loaded_docs)
                
    return docs


def build_or_load_chroma(docs: Optional[List[Document]] = None,
                         persist_directory: str = "./chroma_db",
                         collection_name: str = "ecomarket_rag_data",
                         openai_api_key: Optional[str] = None,
                         force_rebuild: bool = False) -> Dict[str, Any]:
    """
    Si persist_directory ya contiene la colección, la reutiliza.
    Si force_rebuild es True, elimina el directorio y recrea la base de datos.
    Devuelve dict con keys: vectorstore, retriever, doc_count
    """

    if force_rebuild and os.path.exists(persist_directory):
        try:
            shutil.rmtree(persist_directory)
            print(f"DEBUG: Directorio de ChromaDB borrado forzadamente: {persist_directory}")
        except Exception as e:
            print(f"ERROR: No se pudo borrar el directorio de ChromaDB: {e}")
        
    # --- INICIALIZACIÓN DE EMBEDDINGS (BGE-M3 con manejo de dispositivo) ---
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3", 
            model_kwargs={'device': DEVICE}, # Usa 'cuda' si está disponible, sino 'cpu'
            encode_kwargs={'normalize_embeddings': True}
        )
        print(f"DEBUG: Embeddings inicializados con BAAI/bge-m3 en dispositivo: {DEVICE}.")
    except Exception as e:
        print(f"ERROR: Falló la inicialización de HuggingFaceEmbeddings. ¿Tiene instalado 'sentence-transformers'? Detalle: {e}")
        return {"vectorstore": None, "retriever": None, "doc_count": 0}
    # -----------------------------------------------

    doc_count = 0
    
    # 1. Intentar cargar ChromaDB existente
    if os.path.exists(persist_directory) and not force_rebuild:
        try:
            vectordb = Chroma(persist_directory=persist_directory, collection_name=collection_name, embedding_function=embeddings)
            doc_count = vectordb._collection.count()
            
            if doc_count > 0:
                print(f"DEBUG: ChromaDB existente cargada con {doc_count} documentos.")
                retriever = vectordb.as_retriever(search_kwargs={"k": 5})
                return {"vectorstore": vectordb, "retriever": retriever, "doc_count": doc_count}
            else:
                print("DEBUG: ChromaDB existente encontrada pero vacía. Procediendo a recrear.")
        except Exception as e:
            print(f"ERROR: Falló la carga de ChromaDB existente: {e}. Procediendo a recrear.")

    # 2. Crear/Poblar la base de datos
    if docs is None:
        docs = load_remote_documents() 

    if not docs:
        print("ERROR CRÍTICO: No se pudo cargar ningún documento remoto. Retornando doc_count=0.")
        return {"vectorstore": None, "retriever": None, "doc_count": 0}
        
    # --- LÓGICA DE SPLIT SELECTIVO ---
    docs_to_split = []
    docs_no_split = []

    for doc in docs:
        source = doc.metadata.get('source', '')
        # Separamos PDFs para división; el JSON transformado no necesita división.
        if source.lower().endswith(('.pdf')): 
            docs_to_split.append(doc)
        else:
            docs_no_split.append(doc)

    print(f"DEBUG: Documentos largos (PDFs) a dividir: {len(docs_to_split)}")
    print(f"DEBUG: Documentos estructurados (JSON) sin dividir: {len(docs_no_split)}")

    # 3. Segmentación de Texto solo para los documentos largos
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    pdf_chunks = splitter.split_documents(docs_to_split)
    
    # 4. Unificación de los Chunks Finales
    chunks = docs_no_split + pdf_chunks
    
    if not chunks:
        print("ERROR CRÍTICO: Los documentos cargados no produjeron chunks. Retornando doc_count=0.")
        return {"vectorstore": None, "retriever": None, "doc_count": 0}

    # Creación y persistencia
    try:
        vectordb = Chroma.from_documents(documents=chunks, embedding=embeddings, collection_name=collection_name, persist_directory=persist_directory)
        doc_count = len(chunks)
        print(f"DEBUG: ChromaDB creada y persistida con {doc_count} chunks.")
        retriever = vectordb.as_retriever(search_kwargs={"k": 5})
        return {"vectorstore": vectordb, "retriever": retriever, "doc_count": doc_count}
    except Exception as e:
        print(f"ERROR CRÍTICO: Falló la creación de ChromaDB: {e}")
        return {"vectorstore": None, "retriever": None, "doc_count": 0}


def consultar_conocimiento_rag(query: str, retriever, llm, top_k: int = 3) -> str:
    """
    Recupera docs relevantes y pregunta al LLM para obtener respuesta con contexto.
    Utiliza la sintaxis moderna de LangChain (.invoke()).
    """
    if retriever is None:
        return "RAG no disponible (retriever es None). El conocimiento base no fue cargado."

    try:
        docs = retriever.invoke(query)
    except Exception as e:
        return f"Error en la invocación del retriever: {e}"
    
    if not docs:
        return "No se encontraron documentos relevantes en la base de conocimiento para la consulta."
        
    contexto = "\n\n".join([f"Source: {d.metadata.get('source','unknown')}\n{d.page_content}" for d in docs])
    
    prompt = f"""Instrucción: Eres un asistente de servicio al cliente de EcoMarket. Responde a la pregunta del usuario utilizando únicamente el contexto proporcionado.

    **Reglas de Respuesta y Prioridad:**
    1. Si el contexto contiene una respuesta de "PREGUNTA FRECUENTE" directamente relacionada con la consulta, usa esa respuesta concisa y directa.
    2. Si solo hay información general o parcial de otros documentos (Términos, Políticas), sintetiza la respuesta basándote en ellos.
    3. Si la respuesta definitiva NO está en el contexto, y has revisado el contexto a fondo, indica de manera cortés que la información solicitada no se encuentra disponible en la base de datos de conocimiento de EcoMarket.

    Contexto:
    {contexto}

    Pregunta: {query}

    Respuesta:"""
    
    try:
        response_message = llm.invoke(prompt)
        
        if response_message and hasattr(response_message, 'content'):
            return response_message.content
        else:
            return str(response_message)
            
    except Exception as e:
        return f"Error crítico al invocar el LLM durante RAG: {e}"
# Fin de rag_system.py