# 🤖 EcoMarket - Sistema de Agente Inteligente para Devoluciones

Este proyecto implementa un asistente inteligente capaz de **gestionar devoluciones de pedidos** dentro del entorno de EcoMarket.  
El agente utiliza un modelo conversacional y herramientas simuladas para verificar si un pedido es elegible para devolución, generar la etiqueta de envío y procesar el reembolso.

---

## 🧰 Herramientas del Agente (Tools)

El agente utiliza funciones simuladas para interactuar con los sistemas internos de EcoMarket.  
Estas funciones son llamadas **"Herramientas"** y permiten que el agente tome decisiones y ejecute acciones.

A continuación se describe cada una de ellas.

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

## 🎯 Beneficios del Enfoque

- Permite flujos **autónomos y guiados**.
- El agente **toma decisiones** según el contexto.
- Las herramientas encapsulan la lógica de negocio.
- La interfaz final puede ser desplegada fácilmente con **Streamlit o Gradio**.

---

✅ Este archivo está listo para documentación en GitHub.
