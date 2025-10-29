# 🤖 EcoMarket - Sistema de Agente Inteligente para Consultas y Devoluciones

Este proyecto implementa un asistente inteligente capaz de **gestionar devoluciones de pedidos** dentro del entorno de EcoMarket.  
El agente utiliza un modelo conversacional y herramientas simuladas para verificar si un pedido es elegible para devolución, generar la etiqueta de envío y procesar el reembolso. Y adicional, permite que el cliente o usuario haga consultas generales que son respondidas usando la base datos RAG que se ha preparado con documentos de la compañia EcoMarket.

---

# Fase I. Diseño de la Arquitectura del Agente.

## 🧰 Herramientas del Agente (Tools)

El agente utiliza funciones simuladas para interactuar con los sistemas internos de EcoMarket.  
Estas funciones son llamadas **"Herramientas"** y permiten que el agente tome decisiones y ejecute acciones.

A continuación las describimos:

---

### 1. `verificar_elegibilidad_devolucion(id_referencia: str)`

**Objetivo:**  
Determinar si un pedido es elegible para devolución.

**Entrada:**

| Parámetro | Tipo | Descripción |
|---------|------|-------------|
| `id_referencia` | `str` | Puede ser el **ID del pedido** (ej. `P-1003`) o el **número de identificación del cliente** (8 dígitos). |

**Flujo que realiza:**
1. Verifica si el pedido existe.
2. Comprueba que haya sido **entregado**.
3. Valida que el plazo de devolución (30 días) no haya expirado.
4. Identifica qué productos son **retornables** según la política de EcoMarket.
5. Si todo es válido, genera un **ID único de devolución** (`DEV-xxxx`).

**Respuesta esperada:**
```json
{
  "success": true,
  "elegible": true,
  "razon": "El pedido P-1003 es elegible...",
  "productos_retornables": ["bolsas reutilizables"],
  "id_pedido": "P-1003",
  "id_devolucion": "DEV-a92f2043"
}
```

---

### 2. `generar_etiqueta_devolucion(id_devolucion: str, direccion_origen: str)`

**Objetivo:**  
Simular la generación de una **etiqueta de envío** para devolver el producto.

**Entrada:**

| Parámetro | Tipo | Descripción |
|---------|------|-------------|
| `id_devolucion` | `str` | Identificador único de devolución generado previamente. |
| `direccion_origen` | `str` | Dirección desde donde se recogerá el producto. |

**Salida:**

| Clave | Tipo | Descripción |
|-------|------|-------------|
| `tracking_id` | `str` | Código de rastreo del envío. |
| `url_etiqueta` | `str` | Enlace simulado al PDF de la etiqueta. |
| `mensaje` | `str` | Mensaje descriptivo y amigable. |

**Respuesta ejemplo:**
```json
{
  "success": true,
  "tracking_id": "TRK-12a9b35c",
  "url_etiqueta": "https://ecomarket.com/etiquetas/DEV-a92f2043.pdf",
  "mensaje": "Etiqueta generada. El tracking es TRK-12a9b35c."
}
```

---

### 3. `procesar_reembolso(id_devolucion: str)`

**Objetivo:**  
Simular el inicio del proceso de **reembolso** al cliente.

**Entrada:**

| Parámetro | Tipo | Descripción |
|---------|------|-------------|
| `id_devolucion` | `str` | Identificador único de devolución. |

**Salida:**
```json
{
  "success": true,
  "mensaje": "Reembolso procesado. El monto se reflejará en 3-5 días hábiles."
}
```

---

## 🧠 Resumen Visual del Proceso

| Paso | Acción | Herramienta Utilizada |
|-----|--------|----------------------|
| 1 | El cliente solicita devolución | *N/A (conversación)* |
| 2 | Se valida si el pedido puede devolverse | `verificar_elegibilidad_devolucion()` |
| 3 | Cliente confirma | *N/A (conversación)* |
| 4 | Se genera etiqueta de envío | `generar_etiqueta_devolucion()` |
| 5 | Se inicia el reembolso | `procesar_reembolso()` |

---

## Bases de Datos Simuladas
Para uso por las Herramientas se crearon dos (2) bases de datos simuladas
- Una para Productos de EcoMarket, llamada **PRODUCTOS_DB**, donde se encuentra si un producto es Retornable o no.
- Una para Pedidos de EcoMarket, llamada **PEDIDOS_DB**, donde se encuentran registros de pedidos hechos con su ID de pedido, su estado (Entregado, En preparacion, Cancelado, etc.), Los productos incluidos en el Pedido, ID y Nombre del Cliente que hizo el Pedido.

## 🎯 Beneficios del Enfoque

- Permite flujos **autónomos y guiados**.
- El agente **toma decisiones** según el contexto.
- Las herramientas encapsulan la lógica de negocio.
- La interfaz final puede ser desplegada fácilmente con **Streamlit o Gradio**.


## 🧠 Selección del Marco de Agentes

Para el desarrollo del agente inteligente encargado de gestionar el proceso de devoluciones en EcoMarket, se evaluaron dos frameworks ampliamente utilizados en el ámbito de la Inteligencia Artificial Generativa: **LangChain** y **LlamaIndex**.  

Luego del análisis comparativo, se seleccionó **LangChain** como el marco principal para la implementación del agente.

### 🎯 Justificación

El proyecto requiere que el asistente no solo responda preguntas mediante acceso a datos (RAG), sino que **también ejecute acciones concretas**, como:

- Verificar si un pedido es elegible para devolución.
- Generar una etiqueta de envío.
- Procesar un reembolso.

LangChain ofrece una estructura clara para trabajar con **agentes que utilizan herramientas (Tools)** y que pueden tomar decisiones basadas en la conversación. Su enfoque está orientado específicamente al **control autónomo del flujo de acciones**, lo que coincide directamente con los objetivos de este proyecto.

Por otro lado, **LlamaIndex** se destaca en la **gestión y recuperación avanzada de información**, pero su estructura para la definición de agentes con acciones es menos directa y requiere componentes adicionales. Por esto, LlamaIndex fue empleado únicamente como parte del sistema RAG en el Taller 2, pero no como framework principal del agente.

### 📊 Comparativa LangChain vs LlamaIndex

| Criterio | **LangChain** | **LlamaIndex** |
|---------|:-------------:|:--------------:|
| **Enfoque principal** | Orquestación de agentes + herramientas | Recuperación e indexación de información (RAG) |
| **Facilidad para definir herramientas (Tools)** | ✅ Muy alta | ⚠️ Posible, pero menos directa |
| **Modelo de agente con toma de decisiones** | ✅ Diseñado para esto | ⚠️ Se requiere configuración adicional |
| **Integración con RAG** | Compatible con varios motores RAG | ⭐ Excelente soporte nativo |
| **Curva de aprendizaje** | Moderada (agentes + memoria) | Baja para RAG, pero más alta para agentes |
| **Adecuación al proyecto** | ✅ Ideal para automatizar devoluciones y acciones | Útil pero no suficiente para el flujo autónomo |
| **Comunidad y soporte** | Muy amplia y activa | En crecimiento |

### ✅ Conclusión

Se seleccionó **LangChain** porque:

- Permite **modelar agentes que pueden tomar decisiones y ejecutar acciones**.
- Se ajusta perfectamente al flujo de **devolución automatizada**.
- Facilita la **integración con herramientas externas**, incluyendo las simuladas para este proyecto.
- Permite mantener una estructura clara, comprensible y escalable dentro del contexto académico.

## 🧰 Planificación del Flujo de Trabajo

La lógica conversacional está implementada en [`agente_ecomarket.py`](agente_ecomarket.py) y se apoya en las herramientas definidas en [`herramientas_ecomarket.py`](herramientas_ecomarket.py). El siguiente diagrama resume las decisiones principales del agente y cuándo invoca cada herramienta:


```mermaid
flowchart TD
    A[Inicio de mensaje] --> B{¿Incluye ID de pedido<br/>P-XXXX o nro_id?};
    B -- No --> C[Responder con saludo y solicitar referencia<br/>sin usar herramientas];
    C --> Z[Fin del turno];
    B -- Sí --> D[Llamar verificar_elegibilidad_devolucion()<br/>herramientas_ecomarket];
    D --> E{¿Pedido elegible?};
    E -- No --> F[Responder motivo y cerrar flujo];
    F --> Z;
    E -- Sí --> G[Guardar id_devolucion en memoria<br/>EcomarketMemory.start_confirm];
    G --> H[Pedir confirmación (sí/no)];
    H --> I{Respuesta del usuario};
    I -- "sí" --> J[Llamar generar_etiqueta_devolucion()<br/>y procesar_reembolso()];
    J --> K[Enviar etiqueta + confirmación de reembolso];
    I -- "no" --> L[Restablecer memoria y confirmar cancelación];
    I -- Otro --> M[Repetir solicitud de confirmación];
    K --> Z;
    L --> Z;
    M --> H;
    H --> N{¿Llegan preguntas informativas y<br/>no hay confirmación pendiente?};
    N -- Sí --> O[Llamar consultar_conocimiento_rag()<br/>para responder con contexto];
    O --> Z;
```

**Puntos clave del flujo:**
- El agente solo invoca `verificar_elegibilidad_devolucion()` cuando el mensaje incluye una referencia válida. Esto evita llamadas innecesarias y asegura que el usuario comparta su pedido o identificación.
- Mientras `EcomarketMemory.esperando_confirmacion` es `True`, se bloquean consultas al RAG (`consultar_conocimiento_rag`). El agente se centra en cerrar la devolución pidiendo una respuesta "sí/no".
- Ante una confirmación positiva, se ejecutan en cadena `generar_etiqueta_devolucion()` y `procesar_reembolso()` para entregar la etiqueta simulada y notificar el reembolso. Un "no" cancela la operación y restablece la memoria.
- Si el usuario realiza preguntas informativas y no hay una devolución pendiente, el agente consulta la base de conocimiento mediante RAG para complementar sus respuestas.

