# ============================================================
# 🤖 agente_ecomarket.py — Devoluciones EcoMarket (sin dirección)
# ============================================================

from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from typing import Optional
import unicodedata
import re

# Herramientas de negocio
from herramientas_ecomarket import (
    verificar_elegibilidad_devolucion,
    generar_etiqueta_devolucion,
    procesar_reembolso,
)

# RAG
from rag_system import build_or_load_chroma, consultar_conocimiento_rag


# -------- Utilidades de tono --------
def respuesta_amable(texto: str) -> str:
    from datetime import datetime
    h = datetime.now().hour
    saludo = (
        "Buenos días ☀️ Gracias por contactarnos. " if h < 12 else
        "Buenas tardes 🌻 Gracias por contactarnos. " if h < 18 else
        "Buenas noches 🌙 Gracias por contactarnos. "
    )
    return f"{saludo}{texto}"


def _normalize_text(txt: str) -> str:
    txt = txt.strip().lower()
    txt = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    txt = re.sub(r'[^a-z0-9\s]', ' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()


YES = {"si", "sí", "ok", "confirmo", "claro", "vale", "si confirmo", "si por favor", "afirmativo"}
NO = {"no", "nop", "no gracias", "cancelar", "cancelo", "negativo"}


def _parse_yes_no(txt: str) -> Optional[str]:
    t = _normalize_text(txt)
    if t in YES:
        return "yes"
    if t in NO:
        return "no"
    return None


# -------- Memoria de flujo --------
class EcomarketMemory(ConversationBufferMemory):
    id_devolucion: Optional[str] = None
    esperando_confirmacion: bool = False

    def start_confirm(self, id_dev: str):
        self.id_devolucion = id_dev
        self.esperando_confirmacion = True

    def reset_flow(self):
        self.id_devolucion = None
        self.esperando_confirmacion = False


# -------- Inicialización del agente --------
def initialize_ecomarket_agent(openai_api_key: str, persist_dir: str = "./chroma_db"):
    llm = ChatOpenAI(
        temperature=0.1,
        model="gpt-4o-mini",
        openai_api_key=openai_api_key,
    )

    chroma_result = build_or_load_chroma(persist_directory=persist_dir)
    retriever = chroma_result.get("retriever")
    doc_count = chroma_result.get("doc_count", 0)

    memory = EcomarketMemory(memory_key="chat_history", return_messages=True)

    # ---- Tool 1: Verificar pedido / elegibilidad ----
    def verificar_wrap(ref: str):
        result = verificar_elegibilidad_devolucion(ref)

        # Si no es elegible o referencia inválida -> pide referencia con amabilidad
        if not result.get("elegible"):
            razon = result.get("razon", "")
            # Si fue error de formato, responde instrucción clara
            if "Formato de referencia inválido" in razon or "Falta el ID" in razon:
                return respuesta_amable(
                    "Por supuesto 😊 Para ayudarte, por favor indícame el **número de pedido** "
                    "(formato **P-XXXX**) o tu **número de identificación** (8 dígitos)."
                )
            # Si no cumple política / no encontrado dentro de 30 días
            return respuesta_amable(razon)

        # Elegible -> pedir confirmación
        memory.start_confirm(result["id_devolucion"])
        productos = ", ".join(result.get("productos_retornables", [])) or "—"
        return respuesta_amable(
            f"✅ El pedido **{result['id_pedido']}** es elegible para devolución.\n"
            f"Productos retornables: **{productos}**.\n\n"
            f"¿Deseas continuar con la devolución? (Responde **sí** o **no**)"
        )

    # ---- Tool 2: Manejar confirmación (sin dirección) ----
    def manejar_confirmacion(user_text: str):
        if not memory.esperando_confirmacion:
            # Si no estamos esperando confirmación, no actúa
            return None

        decision = _parse_yes_no(user_text)
        if decision == "yes":
            id_dev = memory.id_devolucion
            # No pedimos dirección: usamos un valor fijo para cumplir la firma de la función
            etiqueta = generar_etiqueta_devolucion(id_dev, "Dirección verificada en sistema")
            reembolso = procesar_reembolso(id_dev)
            memory.reset_flow()

            return respuesta_amable(
                f"✅ ¡Tu devolución ha sido confirmada!\n\n"
                f"📦 {etiqueta['mensaje']}\n"
                f"💰 {reembolso['mensaje']}\n\n"
                f"¿Puedo ayudarte con algo más? ♻️"
            )

        if decision == "no":
            memory.reset_flow()
            return respuesta_amable(
                "Perfecto 😊 No realizaremos la devolución. "
                "Quedo atento si necesitas ayuda con otra consulta."
            )

        # Si no entendí la confirmación, la repito
        return respuesta_amable("Solo para confirmar 😊 ¿Deseas continuar con la devolución? (sí/no)")

    tools = [
        Tool(
            name="verificar_elegibilidad_devolucion",
            func=verificar_wrap,
            description="Verifica si un pedido es elegible para devolución, dado un ID de pedido (P-XXXX) o un nro_id (8 dígitos).",
            return_direct=True,
        ),
        Tool(
            name="manejar_confirmacion",
            func=manejar_confirmacion,
            description="Procesa la confirmación (sí/no) del cliente para continuar o cancelar la devolución.",
            return_direct=True,
        ),
    ]

    # RAG disponible SOLO cuando NO estamos esperando confirmación
    if retriever and doc_count > 0:
        def rag_guard(query: str):
            if memory.esperando_confirmacion:
                return respuesta_amable(
                    "Primero confirmemos la devolución 😊 (Responde **sí** o **no**)."
                )
            return consultar_conocimiento_rag(query, retriever, llm)

        tools.append(
            Tool(
                name="consultar_conocimiento_rag",
                func=rag_guard,
                description="Consulta la base de conocimiento de EcoMarket (políticas, términos, FAQ).",
                return_direct=True,
            )
        )

    SYSTEM_PROMPT = """
Eres ECOBOT y SIEMPRE respondes SOLO en español, con tono amable y claro.

REGLAS:
1) Si el usuario habla de devolver pero NO da referencia (P-XXXX o nro_id 8 dígitos):
   -> Responde con la instrucción para pedir esa referencia. NO llames herramientas.
2) Si hay referencia:
   -> Llama a verificar_elegibilidad_devolucion.
3) Si es elegible:
   -> Pide confirmación (sí/no). NO uses RAG mientras esperas confirmación.
4) Si usuario responde sí/no:
   -> Llama a manejar_confirmacion.
5) Evita mezclar RAG durante confirmación.

Nunca hables en inglés.
Responde SIEMPRE con un único saludo (no dupliques saludos en cadena).
"""

    agent = initialize_agent(
        tools,
        llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        agent_kwargs={"system_message": SYSTEM_PROMPT, "memory_prompts": []},
    )

    return agent  # <- importante para que app lo reciba
