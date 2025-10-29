import os
from dotenv import load_dotenv
import streamlit as st

from agente_ecomarket import initialize_ecomarket_agent

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---- Config de página ----
st.set_page_config(page_title="EcoMarket - Asistente", page_icon="♻️", layout="centered")
st.title("🤖 EcoMarket — Asistente de Consultas y Devoluciones")

# ---- Inicialización de estado ----
if "agent" not in st.session_state:
    st.session_state.agent = initialize_ecomarket_agent(OPENAI_API_KEY)

if "messages" not in st.session_state:
    # guardamos como tuplas (role, text)
    st.session_state.messages = []

agent = st.session_state.agent

# ---- Render historial (arriba lo antiguo, abajo lo nuevo) ----
for role, text in st.session_state.messages:
    if role == "user":
        with st.chat_message("user"):
            st.markdown(text)
    else:
        with st.chat_message("assistant"):
            st.markdown(text)

# ---- Entrada de usuario ----
prompt = st.chat_input("Escribe tu consulta o pedido de devolución…")
if prompt:
    # Mostrar usuario
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ejecutar agente
    try:
        result = agent.invoke({"input": prompt})
        output = result.get("output", str(result))
    except Exception as e:
        output = f"Ups, ocurrió un error al procesar tu solicitud: {e}"

    # Mostrar bot (el agente ya devuelve tono amable con saludo único)
    st.session_state.messages.append(("assistant", output))
    with st.chat_message("assistant"):
        st.markdown(output)
